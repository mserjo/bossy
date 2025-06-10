# backend/app/src/repositories/gamification/level_repository.py

"""
Repository for Level (gamification) entities.
Provides CRUD operations and specific methods for managing levels.
"""

import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.app.src.models.gamification.level import Level
from backend.app.src.schemas.gamification.level import LevelCreate, LevelUpdate # Assuming these are the correct schema names
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class LevelRepository(BaseRepository[Level, LevelCreate, LevelUpdate]):
    """
    Repository for managing Level records in the gamification system.
    Levels are typically group-specific.
    """

    def __init__(self):
        super().__init__(Level)

    async def get_levels_for_group(
        self,
        db: AsyncSession,
        *,
        group_id: int,
        min_points_threshold: Optional[int] = None,
        include_archived: bool = False, # Assuming 'state' field can be 'archived'
        skip: int = 0,
        limit: int = 100
    ) -> List[Level]:
        """
        Retrieves levels for a specific group, optionally filtered by minimum points
        and whether to include archived levels.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            min_points_threshold: Optional. Filter for levels requiring at least these points.
            include_archived: Optional. If True, includes levels marked as 'archived' (or similar inactive state).
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of Level objects.
        """
        conditions = [self.model.group_id == group_id] # type: ignore[attr-defined]
        if min_points_threshold is not None:
            conditions.append(self.model.min_points_required >= min_points_threshold) # type: ignore[attr-defined]

        if not include_archived and hasattr(self.model, "state"):
            conditions.append(self.model.state == "active") # type: ignore[attr-defined]

        if hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]


        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.level_number.asc().nulls_first(), self.model.min_points_required.asc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_level_by_number(
        self, db: AsyncSession, *, group_id: int, level_number: int
    ) -> Optional[Level]:
        """
        Retrieves a specific level by its number within a group.
        Assumes level_number is unique within a group if used as a lookup.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            level_number: The numerical representation of the level.

        Returns:
            The Level object if found, otherwise None.
        """
        conditions = [
            self.model.group_id == group_id, # type: ignore[attr-defined]
            self.model.level_number == level_number # type: ignore[attr-defined]
        ]
        if hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = select(self.model).where(*conditions)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_level_by_min_points(
        self, db: AsyncSession, *, group_id: int, points: int
    ) -> Optional[Level]:
        """
        Retrieves the highest level achieved for a given number of points in a group.
        This typically means finding the level with the highest min_points_required
        that is less than or equal to the user's current points.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            points: The current points of a user.

        Returns:
            The Level object corresponding to the achieved level, or None if no level is met.
        """
        conditions = [
            self.model.group_id == group_id, # type: ignore[attr-defined]
            self.model.min_points_required <= points, # type: ignore[attr-defined]
            self.model.state == "active" # type: ignore[attr-defined]
        ]
        if hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.min_points_required.desc()) # type: ignore[attr-defined]
        )
        result = await db.execute(statement)
        return result.scalars().first()


    # BaseRepository methods create, get, update, remove are inherited.
    # `group_id` for creation will be handled by the service layer.
    # `LevelCreate` and `LevelUpdate` schemas from `schemas.gamification.level` are used.
    # Note: The schemas in `gamification/level.py` use UUID for `id` fields in examples,
    # but the `Level` model (inheriting from `BaseGroupAffiliatedMainModel` -> `BaseModel`) uses integer IDs.
    # This repository assumes integer IDs as per the models. Schema ID types should align with model ID types.
