# backend/app/src/repositories/groups/invitation_repository.py

"""
Repository for GroupInvitation entities.
Provides CRUD operations and specific methods for managing group invitations.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone # Added timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update # Added update for potential status changes

from backend.app.src.models.groups.invitation import GroupInvitation, InvitationStatusEnum
from backend.app.src.schemas.groups.invitation import GroupInvitationCreate, GroupInvitationUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class GroupInvitationRepository(BaseRepository[GroupInvitation, GroupInvitationCreate, GroupInvitationUpdate]):
    """
    Repository for managing GroupInvitation records.
    """

    def __init__(self):
        super().__init__(GroupInvitation)

    async def get_by_invitation_code(self, db: AsyncSession, *, invitation_code: str) -> Optional[GroupInvitation]:
        """
        Retrieves a group invitation by its unique invitation code.

        Args:
            db: The SQLAlchemy asynchronous database session.
            invitation_code: The unique code of the invitation.

        Returns:
            The GroupInvitation object if found, otherwise None.
        """
        statement = select(self.model).where(self.model.invitation_code == invitation_code) # type: ignore[attr-defined]
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_all_for_group(
        self,
        db: AsyncSession,
        *,
        group_id: int,
        status: Optional[InvitationStatusEnum] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[GroupInvitation]:
        """
        Retrieves all invitations for a specific group, optionally filtered by status.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            status: Optional. Filter by a specific invitation status.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of GroupInvitation objects.
        """
        conditions = [self.model.group_id == group_id] # type: ignore[attr-defined]
        if status:
            conditions.append(self.model.status == status) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.created_at.desc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_all_for_email(
        self,
        db: AsyncSession,
        *,
        email: str,
        group_id: Optional[int] = None, # Optionally filter by group as well
        status: Optional[InvitationStatusEnum] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[GroupInvitation]:
        """
        Retrieves all invitations sent to a specific email address,
        optionally filtered by group and status.

        Args:
            db: The SQLAlchemy asynchronous database session.
            email: The email address to filter by.
            group_id: Optional. Filter by a specific group ID.
            status: Optional. Filter by a specific invitation status.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of GroupInvitation objects.
        """
        conditions = [self.model.email_invited == email] # type: ignore[attr-defined]
        if group_id is not None:
            conditions.append(self.model.group_id == group_id) # type: ignore[attr-defined]
        if status:
            conditions.append(self.model.status == status) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.created_at.desc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_all_for_target_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        group_id: Optional[int] = None, # Optionally filter by group
        status: Optional[InvitationStatusEnum] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[GroupInvitation]:
        """
        Retrieves all invitations sent directly to a specific target user ID,
        optionally filtered by group and status.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the target user.
            group_id: Optional. Filter by a specific group ID.
            status: Optional. Filter by a specific invitation status.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of GroupInvitation objects.
        """
        conditions = [self.model.target_user_id == user_id] # type: ignore[attr-defined]
        if group_id is not None:
            conditions.append(self.model.group_id == group_id) # type: ignore[attr-defined]
        if status:
            conditions.append(self.model.status == status) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.created_at.desc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def update_status(
        self, db: AsyncSession, *, invitation_id: int, new_status: InvitationStatusEnum
    ) -> Optional[GroupInvitation]:
        """
        Updates the status of a specific invitation.
        Also updates `accepted_at` or `revoked_at` based on the new status.

        Args:
            db: The SQLAlchemy asynchronous database session.
            invitation_id: The ID of the invitation to update.
            new_status: The new status for the invitation.

        Returns:
            The updated GroupInvitation object if found, otherwise None.
        """
        db_obj = await self.get(db, id=invitation_id)
        if db_obj:
            if db_obj.status == new_status: # No change needed
                return db_obj

            db_obj.status = new_status
            now = datetime.now(timezone.utc)
            db_obj.updated_at = now # type: ignore[union-attr]

            if new_status == InvitationStatusEnum.ACCEPTED:
                db_obj.accepted_at = now # type: ignore[union-attr]
            elif new_status == InvitationStatusEnum.REVOKED:
                db_obj.revoked_at = now # type: ignore[union-attr]
            # Add other status-specific logic if needed (e.g., clearing accepted_at if status changes from accepted)

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        return None

    # The base `create` and `remove` (hard delete) methods from BaseRepository will be used.
    # `create` uses GroupInvitationCreate schema.
    # `update` (generic) uses GroupInvitationUpdate, but `update_status` is more specific.
    # The model has default factories for `invitation_code` and `expires_at`.
