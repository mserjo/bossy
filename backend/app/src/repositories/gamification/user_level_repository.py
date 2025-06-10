# backend/app/src/repositories/gamification/user_level_repository.py

"""
Repository for UserLevel (gamification) entities.
Manages records of users achieving specific levels within groups.
"""

import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload # For eager loading

from backend.app.src.models.gamification.user_level import UserLevel
from backend.app.src.models.gamification.level import Level as LevelModel # Import for join
# Assuming UserLevelCreate schema might be simple or handled by service,
# and UserLevelUpdate is unlikely as these are achievement records.
# Using PydanticBaseModel for placeholder if specific schemas aren't defined/needed for repo.
from pydantic import BaseModel as PydanticBaseModel
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

# Placeholder schemas if not defined in schemas.gamification.user_level
class UserLevelCreateSchema(PydanticBaseModel):
    user_id: int
    level_id: int
    group_id: int

class UserLevelUpdateSchema(PydanticBaseModel):
    pass


class UserLevelRepository(BaseRepository[UserLevel, UserLevelCreateSchema, UserLevelUpdateSchema]):
    """
    Repository for managing UserLevel records.
    """

    def __init__(self):
        super().__init__(UserLevel)

    async def get_current_highest_level_for_user_in_group(
        self, db: AsyncSession, *, user_id: int, group_id: int
    ) -> Optional[UserLevel]:
        """
        Retrieves the UserLevel record corresponding to the highest level
        a user has achieved in a specific group.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
            group_id: The ID of the group.

        Returns:
            The UserLevel object for the highest achieved level, or None.
        """
        statement = (
            select(UserLevel)
            .join(LevelModel, UserLevel.level_id == LevelModel.id) # type: ignore[attr-defined]
            .where(
                UserLevel.user_id == user_id, # type: ignore[attr-defined]
                UserLevel.group_id == group_id # type: ignore[attr-defined]
            )
            .order_by(LevelModel.min_points_required.desc()) # type: ignore[attr-defined]
            .options(selectinload(UserLevel.level)) # type: ignore[attr-defined]
        )
        result = await db.execute(statement)
        return result.scalars().first()


    async def get_users_at_level(
        self, db: AsyncSession, *, level_id: int, group_id: int, skip: int = 0, limit: int = 100
    ) -> List[UserLevel]:
        """
        Retrieves all UserLevel records for users who have achieved a specific level in a group.

        Args:
            db: The SQLAlchemy asynchronous database session.
            level_id: The ID of the level.
            group_id: The ID of the group.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of UserLevel objects.
        """
        statement = (
            select(self.model)
            .where(
                self.model.level_id == level_id, # type: ignore[attr-defined]
                self.model.group_id == group_id # type: ignore[attr-defined]
            )
            .order_by(self.model.achieved_at.desc()) # type: ignore[attr-defined]
            .options(selectinload(self.model.user), selectinload(self.model.level)) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_all_levels_for_user_in_group(
        self, db: AsyncSession, *, user_id: int, group_id: int, skip: int = 0, limit: int = 100
    ) -> List[UserLevel]:
        """
        Retrieves all levels achieved by a specific user in a specific group,
        ordered by when they were achieved (most recent first).

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
            group_id: The ID of the group.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of UserLevel objects.
        """
        statement = (
            select(self.model)
            .where(
                self.model.user_id == user_id, # type: ignore[attr-defined]
                self.model.group_id == group_id # type: ignore[attr-defined]
            )
            .order_by(self.model.achieved_at.desc()) # type: ignore[attr-defined]
            .options(selectinload(self.model.level)) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_specific_user_level_achievement(
        self, db: AsyncSession, *, user_id: int, level_id: int, group_id: int
    ) -> Optional[UserLevel]:
        """
        Checks if a user has achieved a specific level in a specific group.
        Relies on UniqueConstraint('user_id', 'group_id', 'level_id').

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: User's ID.
            level_id: Level's ID.
            group_id: Group's ID.
        Returns:
            The UserLevel record if it exists, else None.
        """
        statement = select(self.model).where(
            self.model.user_id == user_id, # type: ignore[attr-defined]
            self.model.level_id == level_id, # type: ignore[attr-defined]
            self.model.group_id == group_id # type: ignore[attr-defined]
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    # BaseRepository methods create, get, update, remove are inherited.
    # `create` uses UserLevelCreateSchema. `user_id`, `level_id`, `group_id` are essential.
    # `achieved_at` has a server_default.
    # Updates to UserLevel records are unlikely (achievements are usually immutable).
