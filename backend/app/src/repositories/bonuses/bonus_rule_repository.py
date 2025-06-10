# backend/app/src/repositories/bonuses/bonus_rule_repository.py

"""
Repository for BonusRule entities.
Provides CRUD operations and specific methods for managing bonus rules.
"""

import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.app.src.models.bonuses.bonus_rule import BonusRule
from backend.app.src.schemas.bonuses.bonus_rule import BonusRuleCreate, BonusRuleUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class BonusRuleRepository(BaseRepository[BonusRule, BonusRuleCreate, BonusRuleUpdate]):
    """
    Repository for managing BonusRule records.
    """

    def __init__(self):
        super().__init__(BonusRule)

    async def get_rules_for_group(
        self,
        db: AsyncSession,
        *,
        group_id: int,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[BonusRule]:
        """
        Retrieves bonus rules for a specific group, optionally filtered by active status.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            is_active: Optional. If True, only active rules are returned.
                               If False, only inactive. If None, all rules.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of BonusRule objects.
        """
        conditions = [self.model.group_id == group_id] # type: ignore[attr-defined]
        if is_active is not None:
            conditions.append(self.model.is_active == is_active) # type: ignore[attr-defined]

        if hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.name) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_rules_by_bonus_type(
        self,
        db: AsyncSession,
        *,
        bonus_type_id: int,
        group_id: Optional[int] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[BonusRule]:
        """
        Retrieves bonus rules by bonus type, optionally filtered by group and active status.

        Args:
            db: The SQLAlchemy asynchronous database session.
            bonus_type_id: The ID of the bonus type.
            group_id: Optional. Filter by a specific group ID.
            is_active: Optional. Filter by active status (True, False, or None for all).
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of BonusRule objects.
        """
        conditions = [self.model.bonus_type_id == bonus_type_id] # type: ignore[attr-defined]
        if group_id is not None:
            conditions.append(self.model.group_id == group_id) # type: ignore[attr-defined]
        if is_active is not None:
            conditions.append(self.model.is_active == is_active) # type: ignore[attr-defined]

        if hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.group_id, self.model.name) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_rule_by_name_and_group(
        self, db: AsyncSession, *, name: str, group_id: int
    ) -> Optional[BonusRule]:
        """
        Retrieves a specific bonus rule by its name within a specific group.
        Assumes name is unique within a group for bonus rules.

        Args:
            db: The SQLAlchemy asynchronous database session.
            name: The name of the bonus rule.
            group_id: The ID of the group.

        Returns:
            The BonusRule object if found, otherwise None.
        """
        conditions = [
            self.model.name == name, # type: ignore[attr-defined]
            self.model.group_id == group_id # type: ignore[attr-defined]
        ]
        if hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = select(self.model).where(*conditions)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    # BaseRepository methods create, get, update, remove are inherited.
    # `group_id` for creation will be handled by the service layer.
    # `BonusRuleCreate` and `BonusRuleUpdate` schemas are used.
