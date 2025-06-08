# backend/app/src/repositories/groups/membership_repository.py

"""
Repository for GroupMembership entities.
Provides CRUD operations and specific methods for managing group memberships.
"""

import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete # Added delete for potential specific scenarios
from sqlalchemy.orm import selectinload # For eager loading example

from backend.app.src.models.groups.membership import GroupMembership
from backend.app.src.models.dictionaries.user_roles import UserRole # For type hinting role object
from backend.app.src.schemas.groups.membership import GroupMembershipCreate, GroupMembershipUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class GroupMembershipRepository(BaseRepository[GroupMembership, GroupMembershipCreate, GroupMembershipUpdate]):
    """
    Repository for managing GroupMembership records.
    This represents the many-to-many relationship between Users and Groups,
    including the role of the user within the group.
    """

    def __init__(self):
        super().__init__(GroupMembership)

    async def get_by_user_and_group(
        self, db: AsyncSession, *, user_id: int, group_id: int
    ) -> Optional[GroupMembership]:
        """
        Retrieves a specific membership record for a user in a group.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
            group_id: The ID of the group.

        Returns:
            The GroupMembership object if found, otherwise None.
        """
        statement = select(self.model).where(
            self.model.user_id == user_id, # type: ignore[attr-defined]
            self.model.group_id == group_id # type: ignore[attr-defined]
        )
        # Example of how you might eagerly load the role if often needed:
        # statement = statement.options(selectinload(self.model.role)) # type: ignore[attr-defined]
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_memberships_for_user(
        self, db: AsyncSession, *, user_id: int, include_inactive: bool = False, skip: int = 0, limit: int = 100
    ) -> List[GroupMembership]:
        """
        Retrieves all group memberships for a specific user, with pagination.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
            include_inactive: If True, includes memberships where `is_active` is False.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of GroupMembership objects.
        """
        conditions = [self.model.user_id == user_id] # type: ignore[attr-defined]
        if not include_inactive:
            conditions.append(self.model.is_active == True) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.group_id) # type: ignore[attr-defined] # Or by join_date, etc.
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_memberships_for_group(
        self, db: AsyncSession, *, group_id: int, include_inactive: bool = False, skip: int = 0, limit: int = 100
    ) -> List[GroupMembership]:
        """
        Retrieves all group memberships for a specific group (i.e., all members of the group), with pagination.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            include_inactive: If True, includes memberships where `is_active` is False.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of GroupMembership objects.
        """
        conditions = [self.model.group_id == group_id] # type: ignore[attr-defined]
        if not include_inactive:
            conditions.append(self.model.is_active == True) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            # Eager load user and role for efficient access in services/responses
            .options(
                selectinload(self.model.user), # type: ignore[attr-defined]
                selectinload(self.model.role)  # type: ignore[attr-defined]
            )
            .order_by(self.model.user_id) # type: ignore[attr-defined] # Or by join_date, etc.
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_user_role_in_group(
        self, db: AsyncSession, *, user_id: int, group_id: int
    ) -> Optional[UserRole]:
        """
        Retrieves the role of a specific user within a specific group.
        This method ensures the role relationship is loaded.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
            group_id: The ID of the group.

        Returns:
            The UserRole object if the membership and role exist and membership is active, otherwise None.
        """
        statement = (
            select(self.model)
            .where(
                self.model.user_id == user_id, # type: ignore[attr-defined]
                self.model.group_id == group_id, # type: ignore[attr-defined]
                self.model.is_active == True # type: ignore[attr-defined] # Typically only want role if membership is active
            )
            .options(selectinload(self.model.role)) # type: ignore[attr-defined] # Eager load the role
        )
        membership = (await db.execute(statement)).scalar_one_or_none()

        if membership:
            return membership.role
        return None

    async def count_members_in_group(self, db: AsyncSession, *, group_id: int, include_inactive: bool = False) -> int:
        """
        Counts the number of members in a specific group.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            include_inactive: If True, includes memberships where `is_active` is False.

        Returns:
            The number of members in the group.
        """
        attributes_filter = {"group_id": group_id}
        if not include_inactive:
            attributes_filter["is_active"] = True

        return await self.count(
            db,
            attributes=attributes_filter
        )

    # The base `create`, `update`, and `remove` methods from BaseRepository will be used.
    # `create` uses GroupMembershipCreate.
    # `update` uses GroupMembershipUpdate (e.g., for changing role_id, is_active, notes).
    # `remove` will hard delete a membership record.
    # The UniqueConstraint on (user_id, group_id) in the model will prevent duplicate memberships.
