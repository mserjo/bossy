# backend/app/src/repositories/bonuses/account_transaction_repository.py

"""
Repository for AccountTransaction entities.
Provides CRUD (mainly Create and Read) operations for account transactions.
"""

import logging
from typing import Optional, List
from datetime import datetime # Not strictly needed here unless for default args, but good for context

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.src.models.bonuses.transaction import AccountTransaction, TransactionTypeEnum
from backend.app.src.schemas.bonuses.transaction import AccountTransactionCreate
# Transactions are typically immutable, so an Update schema is usually not needed.
# If corrections are made, they are usually new counter-transactions.
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class AccountTransactionRepository(BaseRepository[AccountTransaction, AccountTransactionCreate, AccountTransactionCreate]): # Using Create for Update type as placeholder
    """
    Repository for managing AccountTransaction records.
    Transactions are generally append-only.
    """

    def __init__(self):
        super().__init__(AccountTransaction)

    async def get_transactions_for_account(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        skip: int = 0,
        limit: int = 50 # Default to 50 for transaction history
    ) -> List[AccountTransaction]:
        """
        Retrieves transactions for a specific account, ordered by most recent first.

        Args:
            db: The SQLAlchemy asynchronous database session.
            account_id: The ID of the UserAccount.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of AccountTransaction objects.
        """
        statement = (
            select(self.model)
            .where(self.model.account_id == account_id) # type: ignore[attr-defined]
            .order_by(self.model.created_at.desc()) # type: ignore[attr-defined] # Show most recent first
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_transactions_by_type(
        self,
        db: AsyncSession,
        *,
        transaction_type: TransactionTypeEnum,
        account_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AccountTransaction]:
        """
        Retrieves transactions of a specific type, optionally filtered by account.

        Args:
            db: The SQLAlchemy asynchronous database session.
            transaction_type: The TransactionTypeEnum value to filter by.
            account_id: Optional. Filter by a specific UserAccount ID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of AccountTransaction objects.
        """
        conditions = [self.model.transaction_type == transaction_type] # type: ignore[attr-defined]
        if account_id is not None:
            conditions.append(self.model.account_id == account_id) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.created_at.desc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_transactions_by_related_entity(
        self,
        db: AsyncSession,
        *,
        related_entity_type: str,
        related_entity_id: int,
        account_id: Optional[int] = None, # Optional filter
        skip: int = 0,
        limit: int = 100
    ) -> List[AccountTransaction]:
        """
        Retrieves transactions related to a specific entity (e.g., a particular task or reward redemption).

        Args:
            db: The SQLAlchemy asynchronous database session.
            related_entity_type: The type of the related entity (e.g., 'task', 'reward').
            related_entity_id: The ID of the related entity.
            account_id: Optional. Filter further by a specific UserAccount ID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of AccountTransaction objects.
        """
        conditions = [
            self.model.related_entity_type == related_entity_type, # type: ignore[attr-defined]
            self.model.related_entity_id == related_entity_id   # type: ignore[attr-defined]
        ]
        if account_id is not None:
            conditions.append(self.model.account_id == account_id) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.created_at.desc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    # Create method is inherited from BaseRepository.
    # `account_id`, `transaction_type`, `amount` are key fields for AccountTransactionCreate.
    # `balance_after_transaction` and `performed_by_user_id` (if applicable)
    # would typically be set by the service layer before calling create.
    # Transactions are generally immutable, so update/remove methods from BaseRepository
    # might not be used or should be used with extreme caution.
