# backend/app/src/repositories/files/user_avatar_repository.py

"""
Repository for UserAvatar entities.
Manages the link between users and their avatar file records.
"""

import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload

from backend.app.src.models.files.avatar import UserAvatar
from backend.app.src.models.files.file import FileRecord
from backend.app.src.schemas.files.avatar import UserAvatarCreate, UserAvatarUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class UserAvatarRepository(BaseRepository[UserAvatar, UserAvatarCreate, UserAvatarUpdate]):
    """
    Repository for managing UserAvatar records.
    UserAvatar links a user to a FileRecord for their avatar.
    The UserAvatar model uses user_id as its primary key.
    """

    def __init__(self):
        super().__init__(UserAvatar)

    async def get_by_user_id(self, db: AsyncSession, *, user_id: int) -> Optional[UserAvatar]:
        """
        Retrieves the UserAvatar record for a specific user using user_id as PK.
        Eager loads the associated file_record.
        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user whose avatar record is to be fetched.
        Returns:
            The UserAvatar object if found, otherwise None.
        """
        statement = (
            select(self.model)
            .where(self.model.user_id == user_id) # type: ignore[attr-defined]
            .options(selectinload(self.model.file_record)) # type: ignore[attr-defined]
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_active_avatar_for_user(self, db: AsyncSession, *, user_id: int) -> Optional[UserAvatar]:
        """
        Retrieves the active UserAvatar record for a specific user.
        Eager loads the associated file_record.
        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
        Returns:
            The active UserAvatar object if found, otherwise None.
        """
        statement = (
            select(self.model)
            .where(
                self.model.user_id == user_id, # type: ignore[attr-defined]
                self.model.is_active == True   # type: ignore[attr-defined]
            )
            .options(selectinload(self.model.file_record)) # type: ignore[attr-defined]
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def set_active_avatar(
        self, db: AsyncSession, *, user_id: int, file_record_id: int
    ) -> UserAvatar:
        """
        Sets or updates the avatar for a user. Deactivates other avatars for the user.
        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
            file_record_id: The ID of the FileRecord to be used as the avatar.
        Returns:
            The created or updated UserAvatar object.
        """
        await self.deactivate_all_avatars_for_user(db, user_id=user_id)

        existing_avatar = await self.get_by_user_id(db, user_id=user_id)

        if existing_avatar:
            existing_avatar.file_record_id = file_record_id # type: ignore[union-attr]
            existing_avatar.is_active = True # type: ignore[union-attr]
            db.add(existing_avatar)
            await db.commit()
            await db.refresh(existing_avatar)
            return existing_avatar
        else:
            # Ensure UserAvatarCreate schema aligns with these direct assignments or adjust.
            # The model's __init__ will be used here.
            new_avatar_data = {"user_id": user_id, "file_record_id": file_record_id, "is_active": True}
            # obj_in = UserAvatarCreate(**new_avatar_data) # If using schema for validation first
            # return await super().create(db, obj_in=obj_in) # This would use BaseModel's id, not user_id as PK for UserAvatar

            # Direct model creation since UserAvatar PK is user_id
            db_obj = self.model(**new_avatar_data) # type: ignore[call-arg]
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj


    async def deactivate_all_avatars_for_user(self, db: AsyncSession, *, user_id: int) -> int:
        """
        Marks all existing avatar records for a user as inactive.
        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
        Returns:
            The number of avatar records updated.
        """
        statement = (
            update(self.model)
            .where(
                self.model.user_id == user_id, # type: ignore[attr-defined]
                self.model.is_active == True  # type: ignore[attr-defined]
            )
            .values(is_active=False)
            .execution_options(synchronize_session=False) # Recommended for bulk updates
        )
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore[no-any-return]

    async def delete_avatar_for_user(self, db: AsyncSession, *, user_id: int) -> bool:
        """
        Deletes the UserAvatar record for a specific user (using user_id as PK).
        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user whose avatar link should be deleted.
        Returns:
            True if an avatar was found and deleted, False otherwise.
        """
        # UserAvatar's PK is user_id. BaseRepository.remove() assumes PK is 'id'.
        # So, we implement delete specifically for user_id.
        obj = await self.get_by_user_id(db, user_id=user_id)
        if obj:
            await db.delete(obj)
            await db.commit()
            return True
        return False

    # Note on super().create(): Since UserAvatar's PK is user_id, super().create()
    # (which typically creates a new record with an auto-incrementing 'id')
    # is not directly suitable if we want to enforce user_id as the PK without a separate 'id' column.
    # The set_active_avatar method handles the upsert logic correctly for UserAvatar's structure.
    # If UserAvatar was changed to have its own 'id' PK and user_id as a unique FK, then super().create()
    # could be used more directly after ensuring uniqueness of user_id.
