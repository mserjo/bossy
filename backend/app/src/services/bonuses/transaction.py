# backend/app/src/services/bonuses/transaction.py
import logging
from typing import List, Optional, Tuple, Any # Added Any for return type
from uuid import UUID
from decimal import Decimal # For precise amounts and balances
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload # For eager loading
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.src.services.base import BaseService
from app.src.models.bonuses.transaction import AccountTransaction # SQLAlchemy Transaction model
from app.src.models.bonuses.account import UserAccount # To link transaction and update balance
from app.src.models.auth.user import User # For user context on UserAccount
# from app.src.models.groups.group import Group # Not directly used here, but UserAccount might link to it

from app.src.schemas.bonuses.transaction import ( # Pydantic Schemas
    AccountTransactionCreate,
    AccountTransactionResponse
)
# UserAccountResponse might be needed if returning updated account state from here
from app.src.schemas.bonuses.account import UserAccountResponse

# Initialize logger for this module
logger = logging.getLogger(__name__)

class AccountTransactionService(BaseService):
    """
    Service for managing account transactions.
    This service is responsible for creating transaction records and ensuring
    that user account balances are updated atomically and correctly.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("AccountTransactionService initialized.")

    async def create_transaction(
        self,
        transaction_data: AccountTransactionCreate,
        user_account_id: Optional[UUID] = None,
        user_id_for_account_lookup: Optional[UUID] = None,
        group_id_for_account_lookup: Optional[UUID] = None,
        commit_session: bool = True
    ) -> Tuple[AccountTransactionResponse, UserAccountResponse]:
        effective_account_id = user_account_id or transaction_data.user_account_id

        if not effective_account_id and not user_id_for_account_lookup:
            raise ValueError("Either user_account_id or user_id_for_account_lookup must be provided.")

        log_msg_context = f"type '{transaction_data.transaction_type}', amount {transaction_data.amount}"
        logger.debug(f"Attempting to create transaction: {log_msg_context}")

        user_account_db: Optional[UserAccount] = None
        if effective_account_id:
            user_account_db = await self.db_session.get(UserAccount, effective_account_id, options=[
                selectinload(UserAccount.user).options(selectinload(User.user_type)),
                selectinload(UserAccount.group) if hasattr(UserAccount, 'group') else None
            ])
            if not user_account_db:
                raise ValueError(f"UserAccount with ID '{effective_account_id}' not found.")
        elif user_id_for_account_lookup:
            from app.src.services.bonuses.account import UserAccountService
            account_service = UserAccountService(self.db_session)

            # get_or_create_user_account returns a Pydantic schema, so we need to fetch the ORM instance after.
            # This implies get_or_create_user_account might commit. If so, this method isn't fully atomic
            # unless get_or_create_user_account also takes commit_session=False.
            # For now, we proceed assuming it's acceptable or UserAccountService handles it.
            created_or_fetched_account_schema = await account_service.get_or_create_user_account(
                user_id=user_id_for_account_lookup,
                group_id=group_id_for_account_lookup
            )
            user_account_db = await self.db_session.get(UserAccount, created_or_fetched_account_schema.id, options=[
                selectinload(UserAccount.user).options(selectinload(User.user_type)),
                selectinload(UserAccount.group) if hasattr(UserAccount, 'group') else None
            ])
            if not user_account_db:
                 raise ValueError(f"Failed to retrieve UserAccount ORM instance after get/create for user {user_id_for_account_lookup}.")
            effective_account_id = user_account_db.id

        if not user_account_db:
             raise ValueError("User account could not be identified or created.")

        logger.info(f"Processing transaction for UserAccount ID: {user_account_db.id}, User ID: {user_account_db.user_id}")

        current_balance = Decimal(user_account_db.balance)
        transaction_amount = Decimal(transaction_data.amount)

        if transaction_amount < Decimal("0.0"):
            if current_balance < abs(transaction_amount):
                logger.warning(
                    f"Insufficient funds for UserAccount ID '{user_account_db.id}'. "
                    f"Current: {current_balance}, Trying to debit: {abs(transaction_amount)}."
                )
                raise ValueError(f"Insufficient funds. Current balance: {current_balance}.")

        new_balance = current_balance + transaction_amount

        transaction_db_data = transaction_data.dict()

        transaction_db_data['user_account_id'] = user_account_db.id

        new_transaction_db = AccountTransaction(
            **transaction_db_data,
            balance_after_transaction=new_balance
        )

        user_account_db.balance = new_balance
        if hasattr(user_account_db, 'last_transaction_at'): # Check model attribute
            user_account_db.last_transaction_at = datetime.now(timezone.utc)

        self.db_session.add(new_transaction_db)
        self.db_session.add(user_account_db)

        try:
            if commit_session:
                await self.commit()
            else:
                await self.db_session.flush([new_transaction_db, user_account_db])

            refresh_attrs = ['user'] # Base refresh attributes for user_account_db
            if hasattr(UserAccount, 'group') and user_account_db.group_id:
                 refresh_attrs.append('group')
            await self.db_session.refresh(new_transaction_db) # transaction itself usually doesn't have deep relations to refresh
            await self.db_session.refresh(user_account_db, attribute_names=refresh_attrs)

        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error creating transaction for account ID '{user_account_db.id}': {e}", exc_info=True)
            raise ValueError(f"Could not create transaction due to a data conflict: {e}")
        except SQLAlchemyError as e:
            await self.rollback()
            logger.error(f"Database error creating transaction for account ID '{user_account_db.id}': {e}", exc_info=True)
            raise ValueError(f"Database error during transaction processing: {e}")

        logger.info(
            f"Transaction ID '{new_transaction_db.id}' created successfully for account ID '{user_account_db.id}'. "
            f"Old balance: {current_balance}, Amount: {transaction_amount}, New balance: {new_balance}."
        )

        # return (
        #     AccountTransactionResponse.model_validate(new_transaction_db),
        #     UserAccountResponse.model_validate(user_account_db)
        # ) # Pydantic v2
        return (
            AccountTransactionResponse.from_orm(new_transaction_db),
            UserAccountResponse.from_orm(user_account_db)
        ) # Pydantic v1

    async def list_transactions_for_account(
        self,
        user_account_id: UUID,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None
    ) -> List[AccountTransactionResponse]:
        logger.debug(
            f"Listing transactions for account ID: {user_account_id}, type: {transaction_type}, "
            f"date_range: [{start_date}-{end_date}], skip={skip}, limit={limit}"
        )

        stmt = select(AccountTransaction).options(
            selectinload(AccountTransaction.user_account).options(
                selectinload(UserAccount.user).options(selectinload(User.user_type)),
                selectinload(UserAccount.group) if hasattr(UserAccount, 'group') else None
            )
        ).where(AccountTransaction.user_account_id == user_account_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))


        if start_date:
            stmt = stmt.where(AccountTransaction.created_at >= start_date)
        if end_date:
            stmt = stmt.where(AccountTransaction.created_at <= end_date)
        if transaction_type:
            stmt = stmt.where(AccountTransaction.transaction_type == transaction_type)

        stmt = stmt.order_by(AccountTransaction.created_at.desc()).offset(skip).limit(limit)

        transactions_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # response_list = [AccountTransactionResponse.model_validate(t) for t in transactions_db] # Pydantic v2
        response_list = [AccountTransactionResponse.from_orm(t) for t in transactions_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} transactions for account ID '{user_account_id}'.")
        return response_list

    async def get_transaction_by_id(self, transaction_id: UUID) -> Optional[AccountTransactionResponse]:
        logger.debug(f"Attempting to retrieve transaction by ID: {transaction_id}")

        stmt = select(AccountTransaction).options(
            selectinload(AccountTransaction.user_account).options(
                selectinload(UserAccount.user).options(selectinload(User.user_type)),
                selectinload(UserAccount.group) if hasattr(UserAccount, 'group') else None
            )
        ).where(AccountTransaction.id == transaction_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))

        transaction_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if transaction_db:
            logger.info(f"Transaction with ID '{transaction_id}' found.")
            # return AccountTransactionResponse.model_validate(transaction_db) # Pydantic v2
            return AccountTransactionResponse.from_orm(transaction_db) # Pydantic v1

        logger.info(f"Transaction with ID '{transaction_id}' not found.")
        return None

logger.info("AccountTransactionService class defined.")
