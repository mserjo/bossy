# backend/app/src/repositories/notifications/notification_repository.py

"""
Repository for Notification entities.
Provides CRUD operations and specific methods for managing user notifications.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func # Added func for count

from backend.app.src.models.notifications.notification import Notification
from backend.app.src.schemas.notifications.notification import NotificationCreateInternal, NotificationUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class NotificationRepository(BaseRepository[Notification, NotificationCreateInternal, NotificationUpdate]):
    """
    Repository for managing Notification records.
    """

    def __init__(self):
        super().__init__(Notification)

    async def get_notifications_for_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        is_read: Optional[bool] = None,
        include_expired: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Retrieves notifications for a specific user, optionally filtered by read status and expiration.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
            is_read: Optional. Filter by read status (True for read, False for unread).
            include_expired: If False (default), only non-expired or notifications without an expiry are returned.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of Notification objects.
        """
        conditions = [self.model.user_id == user_id] # type: ignore[attr-defined]
        if is_read is not None:
            conditions.append(self.model.is_read == is_read) # type: ignore[attr-defined]

        if not include_expired:
            now = datetime.now(timezone.utc)
            conditions.append(
                (self.model.expires_at.is_(None)) | (self.model.expires_at > now) # type: ignore[attr-defined]
            )

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.created_at.desc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def mark_as_read(self, db: AsyncSession, *, notification_id: int, read_at: Optional[datetime] = None) -> Optional[Notification]:
        """
        Marks a specific notification as read.

        Args:
            db: The SQLAlchemy asynchronous database session.
            notification_id: The ID of the notification to mark as read.
            read_at: Optional. Timestamp for when it was read. Defaults to now(UTC).

        Returns:
            The updated Notification object if found and marked read, otherwise None.
        """
        db_obj = await self.get(db, id=notification_id)
        if db_obj and not db_obj.is_read: # type: ignore[union-attr]
            db_obj.is_read = True # type: ignore[union-attr]
            db_obj.read_at = read_at if read_at else datetime.now(timezone.utc) # type: ignore[union-attr]
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        return db_obj

    async def mark_all_as_read_for_user(self, db: AsyncSession, *, user_id: int, read_at: Optional[datetime] = None) -> int:
        """
        Marks all unread notifications for a specific user as read.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user whose notifications are to be marked as read.
            read_at: Optional. Timestamp for when they were read. Defaults to now(UTC).

        Returns:
            The number of notifications successfully marked as read.
        """
        now = datetime.now(timezone.utc)
        effective_read_at = read_at if read_at else now

        statement = (
            update(self.model)
            .where(
                self.model.user_id == user_id, # type: ignore[attr-defined]
                self.model.is_read == False # type: ignore[attr-defined]
            )
            .values(is_read=True, read_at=effective_read_at, updated_at=now)
            .execution_options(synchronize_session=False)
        )
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore[no-any-return]

    async def delete_expired_notifications(self, db: AsyncSession) -> int:
        """
        Deletes notifications that have passed their 'expires_at' timestamp.
        This is a hard delete.

        Args:
            db: The SQLAlchemy asynchronous database session.

        Returns:
            The number of expired notifications successfully deleted.
        """
        now = datetime.now(timezone.utc)
        statement = delete(self.model).where(
            self.model.expires_at.is_not(None), # type: ignore[attr-defined]
            self.model.expires_at < now # type: ignore[attr-defined]
        ).execution_options(synchronize_session=False)

        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore[no-any-return]

    async def count_unread_notifications_for_user(self, db: AsyncSession, *, user_id: int) -> int:
        """
        Counts unread, non-expired notifications for a user.

        Args:
            db: AsyncSession
            user_id: int

        Returns:
            int: Count of unread notifications.
        """
        now = datetime.now(timezone.utc)
        conditions = [
            self.model.user_id == user_id, # type: ignore[attr-defined]
            self.model.is_read == False, # type: ignore[attr-defined]
            (self.model.expires_at.is_(None)) | (self.model.expires_at > now) # type: ignore[attr-defined]
        ]

        statement = select(func.count(self.model.id)).where(*conditions) # type: ignore[attr-defined]
        result = await db.execute(statement)
        count = result.scalar_one_or_none()
        return count if count is not None else 0

    # BaseRepository methods create, get, update, remove are inherited.
