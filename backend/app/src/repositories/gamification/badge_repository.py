# backend/app/src/repositories/gamification/badge_repository.py

"""
Repository for Badge (gamification) entities.
Provides CRUD operations and specific methods for managing badges.
"""

import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.app.src.models.gamification.badge import Badge
from backend.app.src.schemas.gamification.badge import BadgeCreate, BadgeUpdate # Assuming these are the correct schema names
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class BadgeRepository(BaseRepository[Badge, BadgeCreate, BadgeUpdate]):
    """
    Repository for managing Badge records in the gamification system.
    Badges can be group-specific or global (if group_id is nullable).
    """

    def __init__(self):
        super().__init__(Badge)

    async def get_badges_for_group(
        self,
        db: AsyncSession,
        *,
        group_id: int,
        is_active_state: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Badge]:
        """
        Retrieves badges for a specific group, optionally filtered by 'state'.
        If is_active_state is True, filters for state='active'.
        If is_active_state is False, filters for state!='active'.
        If is_active_state is None, no state filter is applied.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            is_active_state: Optional. Filter by the 'state' field.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of Badge objects.
        """
        conditions = [self.model.group_id == group_id] # type: ignore[attr-defined]

        if hasattr(self.model, "state") and is_active_state is not None:
            if is_active_state:
                conditions.append(self.model.state == "active") # type: ignore[attr-defined]
            else:
                conditions.append(self.model.state != "active") # type: ignore[attr-defined]

        if hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.name.asc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_global_badges(
        self,
        db: AsyncSession,
        *,
        is_active_state: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Badge]:
        """
        Retrieves global badges (where group_id is NULL).
        Optionally filters by 'state'.

        Args:
            db: The SQLAlchemy asynchronous database session.
            is_active_state: Optional. Filter by the 'state' field.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of global Badge objects.
        """
        conditions = [self.model.group_id.is_(None)] # type: ignore[attr-defined]

        if hasattr(self.model, "state") and is_active_state is not None:
            if is_active_state:
                conditions.append(self.model.state == "active") # type: ignore[attr-defined]
            else:
                conditions.append(self.model.state != "active") # type: ignore[attr-defined]

        if hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.name.asc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_badge_by_name_and_group(
        self, db: AsyncSession, *, name: str, group_id: Optional[int]
    ) -> Optional[Badge]:
        """
        Retrieves a badge by its name within a specific group, or globally if group_id is None.
        Assumes name is unique within its scope (group or global).

        Args:
            db: AsyncSession instance.
            name: Name of the badge.
            group_id: ID of the group, or None for a global badge.

        Returns:
            Optional[Badge]
        """
        conditions = [self.model.name == name] # type: ignore[attr-defined]
        if group_id is None:
            conditions.append(self.model.group_id.is_(None)) # type: ignore[attr-defined]
        else:
            conditions.append(self.model.group_id == group_id) # type: ignore[attr-defined]

        if hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = select(self.model).where(*conditions)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    # BaseRepository methods create, get, update, remove are inherited.
    # `group_id` for creation (if group-specific) will be handled by the service layer.
    # `BadgeCreate` and `BadgeUpdate` schemas from `schemas.gamification.badge` are used.
    # Note: Schemas use UUID for ID examples, models use int. Repository assumes int IDs.
