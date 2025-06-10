# backend/app/src/repositories/groups/group_repository.py

"""
Repository for Group entities.
Provides CRUD operations and specific methods for managing groups.
"""

import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_ # Added or_ for search

from backend.app.src.models.groups.group import Group
from backend.app.src.schemas.groups.group import GroupCreate, GroupUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class GroupRepository(BaseRepository[Group, GroupCreate, GroupUpdate]):
    """
    Repository for managing Group records.
    """

    def __init__(self):
        super().__init__(Group)

    async def get_by_owner_id(self, db: AsyncSession, *, owner_id: int, skip: int = 0, limit: int = 100) -> List[Group]:
        """
        Retrieves all groups owned by a specific user, with pagination.

        Args:
            db: The SQLAlchemy asynchronous database session.
            owner_id: The ID of the user who owns the groups.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A list of Group objects.
        """
        statement = (
            select(self.model)
            .where(self.model.owner_id == owner_id) # type: ignore[attr-defined]
            .order_by(self.model.name) # type: ignore[attr-defined] # Default order by name
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_by_group_type_id(
        self, db: AsyncSession, *, group_type_id: int, skip: int = 0, limit: int = 100
    ) -> List[Group]:
        """
        Retrieves all groups of a specific type, with pagination.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_type_id: The ID of the group type.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A list of Group objects.
        """
        statement = (
            select(self.model)
            .where(self.model.group_type_id == group_type_id) # type: ignore[attr-defined]
            .order_by(self.model.name) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def search_groups_by_name(
        self, db: AsyncSession, *, name_query: str, skip: int = 0, limit: int = 100
    ) -> List[Group]:
        """
        Searches for groups by name (case-insensitive partial match).

        Args:
            db: The SQLAlchemy asynchronous database session.
            name_query: The search term for the group name.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A list of Group objects matching the name query.
        """
        search_filter = f"%{name_query.lower()}%"
        statement = (
            select(self.model)
            .where(self.model.name.ilike(search_filter)) # type: ignore[attr-defined]
            .order_by(self.model.name) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    # The base `create` and `update` methods from BaseRepository will be used.
    # For `create`, owner_id will need to be set by the service layer based on the
    # authenticated user. The GroupCreate schema does not include owner_id for this reason.
    # `update` uses GroupUpdate schema.
    # Soft delete (`remove` method in BaseRepository if soft delete mixin is used by Group model)
    # should work as expected if Group inherits from a model with SoftDeleteMixin (BaseMainModel does).
