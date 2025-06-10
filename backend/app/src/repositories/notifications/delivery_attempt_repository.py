# backend/app/src/repositories/notifications/delivery_attempt_repository.py

"""
Repository for NotificationDeliveryAttempt entities.
Provides CRUD (mainly Create and Read) operations for notification delivery attempts.
"""

import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.src.models.notifications.delivery import NotificationDeliveryAttempt, DeliveryStatusEnum
from backend.app.src.models.notifications.template import NotificationChannelEnum
from backend.app.src.schemas.notifications.delivery import NotificationDeliveryAttemptCreate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class NotificationDeliveryAttemptRepository(BaseRepository[NotificationDeliveryAttempt, NotificationDeliveryAttemptCreate, NotificationDeliveryAttemptCreate]):
    """
    Repository for managing NotificationDeliveryAttempt records.
    These records are typically append-only, logging each attempt to deliver a notification.
    """

    def __init__(self):
        super().__init__(NotificationDeliveryAttempt)

    async def get_attempts_for_notification(
        self,
        db: AsyncSession,
        *,
        notification_id: int,
        channel: Optional[NotificationChannelEnum] = None,
        status: Optional[DeliveryStatusEnum] = None,
        skip: int = 0,
        limit: int = 10
    ) -> List[NotificationDeliveryAttempt]:
        """
        Retrieves delivery attempts for a specific notification,
        optionally filtered by channel and status.

        Args:
            db: The SQLAlchemy asynchronous database session.
            notification_id: The ID of the notification.
            channel: Optional. Filter by the delivery channel.
            status: Optional. Filter by the delivery status.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of NotificationDeliveryAttempt objects, ordered by most recent attempt first.
        """
        conditions = [self.model.notification_id == notification_id] # type: ignore[attr-defined]
        if channel:
            conditions.append(self.model.channel == channel) # type: ignore[attr-defined]
        if status:
            conditions.append(self.model.status == status) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.attempted_at.desc(), self.model.created_at.desc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_latest_attempt_for_notification_channel(
        self,
        db: AsyncSession,
        *,
        notification_id: int,
        channel: NotificationChannelEnum
    ) -> Optional[NotificationDeliveryAttempt]:
        """
        Retrieves the most recent delivery attempt for a specific notification on a specific channel.

        Args:
            db: The SQLAlchemy asynchronous database session.
            notification_id: The ID of the notification.
            channel: The specific NotificationChannelEnum member.

        Returns:
            The most recent NotificationDeliveryAttempt object if found, otherwise None.
        """
        statement = (
            select(self.model)
            .where(
                self.model.notification_id == notification_id, # type: ignore[attr-defined]
                self.model.channel == channel # type: ignore[attr-defined]
            )
            .order_by(self.model.attempted_at.desc(), self.model.created_at.desc()) # type: ignore[attr-defined]
        )
        result = await db.execute(statement)
        return result.scalars().first()

    # Create method is inherited from BaseRepository.
    # Updates are rare; new attempts create new records.
