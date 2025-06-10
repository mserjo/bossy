# backend/app/src/services/bonuses/account.py
import logging
from typing import List, Optional, Tuple, Any # Added Any for adjust_account_balance return
from uuid import UUID
from decimal import Decimal # For precise balance calculations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.bonuses.account import UserAccount # SQLAlchemy UserAccount model
from app.src.models.auth.user import User # For linking account to user
from app.src.models.groups.group import Group # If accounts are per-group per-user

from app.src.schemas.bonuses.account import ( # Pydantic Schemas
    UserAccountCreate, # May not be directly exposed if accounts are auto-created
    UserAccountResponse,
    UserAccountUpdate # For manual adjustments by admin, perhaps
)
# from app.src.schemas.bonuses.transaction import AccountTransactionCreate # For adjust_account_balance conceptual call
# from app.src.services.bonuses.transaction import AccountTransactionService # For balance adjustments

# Initialize logger for this module
logger = logging.getLogger(__name__)

class UserAccountService(BaseService):
    """
    Service for managing user bonus accounts.
    Handles creation, retrieval, and balance display.
    Balance adjustments should ideally be done atomically via AccountTransactionService.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("UserAccountService initialized.")

    async def get_user_account(
        self,
        user_id: UUID,
        group_id: Optional[UUID] = None
    ) -> Optional[UserAccountResponse]:
        log_msg = f"user ID '{user_id}'"
        if group_id: log_msg += f" in group ID '{group_id}'"
        logger.debug(f"Attempting to retrieve bonus account for {log_msg}.")

        stmt = select(UserAccount).options(
            selectinload(UserAccount.user).options(selectinload(User.user_type)),
            selectinload(UserAccount.group) if hasattr(UserAccount, 'group') else None
        ).where(UserAccount.user_id == user_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))


        if hasattr(UserAccount, 'group_id'):
            if group_id:
                stmt = stmt.where(UserAccount.group_id == group_id)
            else:
                stmt = stmt.where(UserAccount.group_id.is_(None)) # type: ignore
        elif group_id:
             logger.warning(f"UserAccount model does not seem to support group-specific accounts, but group_id '{group_id}' was provided. Ignoring group_id.")

        account_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if account_db:
            logger.info(f"Bonus account found for {log_msg}.")
            # return UserAccountResponse.model_validate(account_db) # Pydantic v2
            return UserAccountResponse.from_orm(account_db) # Pydantic v1

        logger.info(f"No bonus account found for {log_msg}.")
        return None

    async def get_or_create_user_account(
        self,
        user_id: UUID,
        group_id: Optional[UUID] = None,
        initial_balance: Decimal = Decimal("0.0")
    ) -> UserAccountResponse:
        account_response = await self.get_user_account(user_id, group_id)
        if account_response:
            return account_response

        log_msg = f"user ID '{user_id}'"
        if group_id: log_msg += f" in group ID '{group_id}'"
        logger.info(f"No existing bonus account for {log_msg}. Creating new account.")

        user = await self.db_session.get(User, user_id)
        if not user: raise ValueError(f"User with ID '{user_id}' not found.")

        actual_group_id_for_creation = group_id
        if group_id and hasattr(UserAccount, 'group_id'):
            group = await self.db_session.get(Group, group_id)
            if not group: raise ValueError(f"Group with ID '{group_id}' not found.")
        elif group_id:
             logger.warning(f"UserAccount model does not support group_id, but group_id '{group_id}' provided. Creating account without group linkage.")
             actual_group_id_for_creation = None

        account_db_data = {"user_id": user_id, "balance": initial_balance}
        if hasattr(UserAccount, 'group_id'): # Only add group_id if model supports it
            account_db_data["group_id"] = actual_group_id_for_creation

        new_account_db = UserAccount(**account_db_data)

        self.db_session.add(new_account_db)
        try:
            await self.commit()
            # Refresh to load relationships like user, group
            refresh_attrs = ['user']
            if hasattr(UserAccount, 'group') and actual_group_id_for_creation:
                refresh_attrs.append('group')
            await self.db_session.refresh(new_account_db, attribute_names=refresh_attrs)
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error creating account for {log_msg}: {e}", exc_info=True)
            account_response_retry = await self.get_user_account(user_id, group_id) # Check if concurrently created
            if account_response_retry: return account_response_retry
            raise ValueError(f"Could not create account for {log_msg} due to data conflict.")

        logger.info(f"Bonus account created for {log_msg} with ID {new_account_db.id}.")
        # return UserAccountResponse.model_validate(new_account_db) # Pydantic v2
        return UserAccountResponse.from_orm(new_account_db) # Pydantic v1


    async def adjust_account_balance(
        self,
        user_id: UUID,
        amount: Decimal,
        transaction_type: str,
        description: Optional[str] = None,
        related_entity_id: Optional[UUID] = None,
        group_id: Optional[UUID] = None,
        commit_session: bool = True
    ) -> Tuple[UserAccountResponse, Any]: # Any for simulated transaction response

        logger.info(f"Attempting to adjust balance for user ID '{user_id}' by {amount} for type '{transaction_type}'. Group: {group_id}")

        # Get ORM model instance of the account
        account_response_schema = await self.get_or_create_user_account(user_id, group_id)
        # Assuming UserAccountResponse has an 'id' field corresponding to UserAccount.id
        stmt_get_orm = select(UserAccount).where(UserAccount.id == account_response_schema.id)
        account_db_model = (await self.db_session.execute(stmt_get_orm)).scalar_one_or_none()

        if not account_db_model: # Should not happen if get_or_create works
            raise ValueError(f"User account not found for user {user_id}, group {group_id} after get_or_create.")


        current_balance = Decimal(account_db_model.balance)
        adjustment_amount = Decimal(amount)

        if adjustment_amount < Decimal("0.0") and current_balance < abs(adjustment_amount):
            logger.warning(f"Insufficient funds for user ID '{user_id}'. Current: {current_balance}, Debit: {abs(adjustment_amount)}.")
            raise ValueError(f"Insufficient funds. Current balance: {current_balance}.")

        from app.src.models.bonuses.transaction import AccountTransaction # Local import

        new_balance = current_balance + adjustment_amount
        account_db_model.balance = new_balance
        if hasattr(account_db_model, 'last_transaction_at'): # Check model attribute
            account_db_model.last_transaction_at = datetime.now(timezone.utc)
        self.db_session.add(account_db_model)

        transaction_db = AccountTransaction(
            user_account_id=account_db_model.id,
            transaction_type=transaction_type,
            amount=adjustment_amount,
            balance_after_transaction=new_balance,
            description=description,
            related_entity_id=related_entity_id
        )
        self.db_session.add(transaction_db)

        if commit_session:
            await self.commit()
        else:
            await self.db_session.flush([account_db_model, transaction_db])

        # Refresh for response
        refresh_attrs = ['user']
        if hasattr(UserAccount, 'group') and account_db_model.group_id:
             refresh_attrs.append('group')
        await self.db_session.refresh(account_db_model, attribute_names=refresh_attrs)
        await self.db_session.refresh(transaction_db)

        logger.info(f"Balance for user ID '{user_id}' (Account ID: {account_db_model.id}) adjusted by {adjustment_amount}. New balance: {new_balance}.")

        from app.src.schemas.bonuses.transaction import AccountTransactionResponse # Local import
        # transaction_response = AccountTransactionResponse.model_validate(transaction_db) # Pydantic v2
        transaction_response = AccountTransactionResponse.from_orm(transaction_db) # Pydantic v1

        # return UserAccountResponse.model_validate(account_db_model), transaction_response # Pydantic v2
        return UserAccountResponse.from_orm(account_db_model), transaction_response # Pydantic v1

    async def list_user_accounts(
        self,
        skip: int = 0,
        limit: int = 100,
        group_id: Optional[UUID] = None,
        min_balance: Optional[Decimal] = None
    ) -> List[UserAccountResponse]:
        logger.debug(f"Listing user accounts: group={group_id}, min_balance={min_balance}, skip={skip}, limit={limit}")

        stmt = select(UserAccount).options(
            selectinload(UserAccount.user).options(selectinload(User.user_type)),
            selectinload(UserAccount.group) if hasattr(UserAccount, 'group') else None
        )
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))


        conditions = []
        if hasattr(UserAccount, 'group_id'):
            if group_id:
                conditions.append(UserAccount.group_id == group_id)
            # If group_id is None, lists all accounts (global and all groups if not filtered otherwise).
            # To list only global accounts when group_id is None: conditions.append(UserAccount.group_id.is_(None))

        if min_balance is not None:
            conditions.append(UserAccount.balance >= min_balance)

        if conditions:
            stmt = stmt.where(*conditions)

        order_by_attrs = [UserAccount.user_id]
        if hasattr(UserAccount, 'group_id'):
            order_by_attrs.append(UserAccount.group_id) # type: ignore
        stmt = stmt.order_by(*order_by_attrs).offset(skip).limit(limit)

        accounts_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # response_list = [UserAccountResponse.model_validate(acc) for acc in accounts_db] # Pydantic v2
        response_list = [UserAccountResponse.from_orm(acc) for acc in accounts_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} user accounts.")
        return response_list

logger.info("UserAccountService class defined.")
