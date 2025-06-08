# backend/app/src/repositories/bonuses/reward_repository.py

"""
Repository for Reward entities.
Provides CRUD operations and specific methods for managing redeemable rewards.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone # Added timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update # Added update for stock management

from backend.app.src.models.bonuses.reward import Reward
from backend.app.src.schemas.bonuses.reward import RewardCreate, RewardUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class RewardRepository(BaseRepository[Reward, RewardCreate, RewardUpdate]):
    """
    Repository for managing Reward records.
    """

    def __init__(self):
        super().__init__(Reward)

    async def get_rewards_for_group(
        self,
        db: AsyncSession,
        *,
        group_id: int,
        is_active: Optional[bool] = True, # Default to only active rewards
        in_stock_only: bool = False, # Default to show all, even if stock is 0 but not null
        skip: int = 0,
        limit: int = 100
    ) -> List[Reward]:
        """
        Retrieves rewards for a specific group, optionally filtered by active status and stock.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            is_active: Optional. If True, only active rewards. If False, only inactive. If None, all.
            in_stock_only: If True, only returns rewards where stock_quantity > 0 or stock_quantity is NULL (unlimited).
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of Reward objects.
        """
        conditions = [self.model.group_id == group_id] # type: ignore[attr-defined]
        if is_active is not None:
            conditions.append(self.model.is_active == is_active) # type: ignore[attr-defined]

        if in_stock_only:
            conditions.append(
                (self.model.stock_quantity > 0) | (self.model.stock_quantity.is_(None)) # type: ignore[attr-defined]
            )

        if hasattr(self.model, "deleted_at"): # Exclude soft-deleted by default
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.cost_in_points.asc(), self.model.name.asc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def decrement_stock(self, db: AsyncSession, *, reward_id: int, quantity: int = 1) -> Optional[Reward]:
        """
        Decrements the stock_quantity of a specific reward.
        This method should be used carefully, ideally within a transaction managed by a service
        that also handles point deduction and records the redemption.
        It does not decrement if stock_quantity is NULL (unlimited).

        Args:
            db: The SQLAlchemy asynchronous database session.
            reward_id: The ID of the Reward to update.
            quantity: The amount to decrement the stock by (default is 1).

        Returns:
            The updated Reward object if stock was sufficient and updated,
            None if reward not found, or if stock is NULL (unlimited),
            or if stock was insufficient (raises ValueError in that case).
        Raises:
            ValueError: If stock is insufficient or update fails due to concurrency.
        """
        reward = await self.get(db, id=reward_id)
        if not reward:
            return None

        if reward.stock_quantity is not None:
            if reward.stock_quantity < quantity:
                raise ValueError(f"Insufficient stock for reward ID {reward_id}. Available: {reward.stock_quantity}, Requested: {quantity}")

            new_stock = reward.stock_quantity - quantity
            stmt = (
                update(self.model)
                .where(self.model.id == reward_id) # type: ignore[attr-defined]
                .where(self.model.stock_quantity >= quantity) # type: ignore[attr-defined]
                .values(stock_quantity=new_stock, updated_at=datetime.now(timezone.utc))
                .execution_options(synchronize_session="fetch")
            )
            result = await db.execute(stmt)
            if result.rowcount == 0:
                await db.rollback()
                raise ValueError(f"Failed to decrement stock for reward ID {reward_id} due to concurrent update or insufficient stock.")

            await db.commit()
            # Refresh the object in the current session to reflect the changes
            await db.refresh(reward)
            # It's good practice to ensure the in-memory object also reflects the change directly
            # if not relying solely on refresh or if synchronize_session='fetch' behavior is nuanced.
            reward.stock_quantity = new_stock
            reward.updated_at = stmt.compile().params['updated_at'] # Get actual timestamp used if needed from compiled statement

        return reward

    async def increment_stock(self, db: AsyncSession, *, reward_id: int, quantity: int = 1) -> Optional[Reward]:
        """
        Increments the stock_quantity of a specific reward.
        Useful if a redemption is cancelled or stock is replenished.
        Does not increment if stock_quantity is NULL (unlimited).

        Args:
            db: The SQLAlchemy asynchronous database session.
            reward_id: The ID of the Reward to update.
            quantity: The amount to increment the stock by (default is 1).

        Returns:
            The updated Reward object if found and updated, None otherwise.
        """
        reward = await self.get(db, id=reward_id)
        if not reward:
            return None

        if reward.stock_quantity is not None:
            new_stock = reward.stock_quantity + quantity
            stmt = (
                update(self.model)
                .where(self.model.id == reward_id) # type: ignore[attr-defined]
                .values(stock_quantity=new_stock, updated_at=datetime.now(timezone.utc))
                .execution_options(synchronize_session="fetch")
            )
            await db.execute(stmt)
            await db.commit()
            await db.refresh(reward)
            reward.stock_quantity = new_stock
            reward.updated_at = stmt.compile().params['updated_at']

        return reward

    # BaseRepository methods create, get, update, remove are inherited.
