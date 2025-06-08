# backend/app/src/repositories/bonuses/user_account_repository.py

"""
Repository for UserAccount entities.
Provides CRUD operations and specific methods for managing user point/currency accounts.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone # Added timezone
from decimal import Decimal # For balance type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update # Added update

from backend.app.src.models.bonuses.account import UserAccount
from backend.app.src.schemas.bonuses.account import UserAccountCreate, UserAccountUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class UserAccountRepository(BaseRepository[UserAccount, UserAccountCreate, UserAccountUpdate]):
    """
    Repository for managing UserAccount records.
    """

    def __init__(self):
        super().__init__(UserAccount)

    async def get_by_user_and_group(self, db: AsyncSession, *, user_id: int, group_id: int) -> Optional[UserAccount]:
        """
        Retrieves a user's account for a specific group.
        Relies on the UniqueConstraint('user_id', 'group_id') on the model.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
            group_id: The ID of the group.

        Returns:
            The UserAccount object if found, otherwise None.
        """
        statement = select(self.model).where(
            self.model.user_id == user_id, # type: ignore[attr-defined]
            self.model.group_id == group_id # type: ignore[attr-defined]
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_accounts_for_user(self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100) -> List[UserAccount]:
        """
        Retrieves all accounts for a specific user across different groups.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of UserAccount objects.
        """
        statement = (
            select(self.model)
            .where(self.model.user_id == user_id) # type: ignore[attr-defined]
            .order_by(self.model.group_id) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_accounts_for_group(self, db: AsyncSession, *, group_id: int, skip: int = 0, limit: int = 100) -> List[UserAccount]:
        """
        Retrieves all user accounts within a specific group.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of UserAccount objects.
        """
        statement = (
            select(self.model)
            .where(self.model.group_id == group_id) # type: ignore[attr-defined]
            .order_by(self.model.user_id) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def update_balance(
        self, db: AsyncSession, *, account_id: int, change_amount: Decimal, last_transaction_at: Optional[datetime] = None
    ) -> Optional[UserAccount]:
        """
        Atomically updates the balance of a user account by a specified amount.
        This method uses a select-then-update pattern. For true atomicity under high concurrency,
        consider database-level locks (e.g., SELECT FOR UPDATE) or direct SQL UPDATE statements
        managed carefully by the service layer alongside transaction creation.
        This repository method is provided for direct balance adjustments but should be
        used with caution, ideally within a service-layer transaction that also records
        an AccountTransaction.

        Args:
            db: The SQLAlchemy asynchronous database session.
            account_id: The ID of the UserAccount to update.
            change_amount: The amount to add (positive) or subtract (negative) from the balance.
            last_transaction_at: Optional. Timestamp for `last_transaction_at`. Defaults to now(UTC).

        Returns:
            The updated UserAccount object if found and updated, otherwise None.
        """
        user_account = await self.get(db, id=account_id) # Consider with_for_update here if needed
        if not user_account:
            return None

        user_account.balance += change_amount # type: ignore[union-attr]
        user_account.last_transaction_at = last_transaction_at if last_transaction_at else datetime.now(timezone.utc) # type: ignore[union-attr]
        # updated_at will be handled by TimestampedMixin if BaseRepository.update calls db.add(user_account)
        # or if SQLAlchemy event listeners are correctly configured for "before_flush".
        # For this direct manipulation, explicitly setting it is safer if not relying on super().update
        user_account.updated_at = datetime.now(timezone.utc) # type: ignore[union-attr]


        try:
            db.add(user_account) # Mark as dirty
            await db.commit()
            await db.refresh(user_account)
            return user_account
        except Exception as e:
            logger.error(f"Error updating balance for account {account_id}: {e}")
            await db.rollback()
            raise

    # BaseRepository methods create, get, update (generic), remove are inherited.
    # `create` uses UserAccountCreate. `user_id` and `group_id` must be provided.
    # The generic `update` (using UserAccountUpdate) is for fields like `currency_name`.
