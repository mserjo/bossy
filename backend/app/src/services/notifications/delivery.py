# backend/app/src/services/notifications/delivery.py
import logging
from typing import List, Optional, Dict, Any, Type
from uuid import UUID
from datetime import datetime, timezone, timedelta # Added timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.src.services.base import BaseService
from app.src.models.notifications.notification import Notification # SQLAlchemy Notification model
from app.src.models.notifications.delivery import NotificationDeliveryAttempt # SQLAlchemy DeliveryAttempt model
from app.src.models.auth.user import User # For user preferences and contact details

from app.src.services.notifications.delivery_channels import (
    ChannelSender,
    EmailNotificationService,
    SmsNotificationService,
    PushNotificationService
)
from app.src.schemas.notifications.delivery import NotificationDeliveryAttemptResponse # Import Pydantic schema for return types

# Initialize logger for this module
logger = logging.getLogger(__name__)

class NotificationDeliveryService(BaseService):
    """
    Service responsible for orchestrating the delivery of notifications
    through various configured channels (Email, SMS, Push, etc.).
    It logs delivery attempts and their outcomes.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)

        self.channel_senders: Dict[str, ChannelSender] = {
            "EMAIL": EmailNotificationService(),
            "SMS": SmsNotificationService(),
            "PUSH": PushNotificationService(),
        }
        logger.info("NotificationDeliveryService initialized with configured channel senders.")

    async def send_notification_to_user(
        self,
        notification_id: UUID,
        user_id: UUID,
    ) -> List[NotificationDeliveryAttemptResponse]: # Return list of Pydantic responses
        logger.info(f"Attempting to send notification ID '{notification_id}' to user ID '{user_id}'.")

        notification_db = await self.db_session.get(Notification, notification_id)
        if not notification_db:
            logger.error(f"Notification ID '{notification_id}' not found. Cannot send.")
            return []

        if notification_db.user_id != user_id:
            logger.error(f"Notification ID '{notification_id}' does not belong to user ID '{user_id}'. Mismatch.")
            return []

        user_db = await self.db_session.get(User, user_id, options=[selectinload(User.user_type)]) # Load type for logging/context
        if not user_db:
            logger.error(f"User ID '{user_id}' for notification ID '{notification_id}' not found. Cannot send.")
            return []

        channels_to_try: List[str] = []
        if hasattr(user_db, 'email') and user_db.email and "EMAIL" in self.channel_senders:
            channels_to_try.append("EMAIL")
        if hasattr(user_db, 'phone_number') and user_db.phone_number and "SMS" in self.channel_senders:
            channels_to_try.append("SMS")
        if hasattr(user_db, 'active_push_tokens') and getattr(user_db, 'active_push_tokens', []) and "PUSH" in self.channel_senders:
            channels_to_try.append("PUSH")

        if not channels_to_try:
            logger.warning(f"No suitable channels found or user ID '{user_id}' has no contact info for notification ID '{notification_id}'.")
            # Optionally create a failed attempt record:
            # failed_attempt = NotificationDeliveryAttempt(notification_id=notification_id, channel="NONE", status="FAILED", error_message="No suitable channel/contact info")
            # self.db_session.add(failed_attempt)
            # await self.commit() # Commit this specific failure log
            # return [NotificationDeliveryAttemptResponse.from_orm(failed_attempt)] # Pydantic v1
            return []

        created_attempt_responses: List[NotificationDeliveryAttemptResponse] = []

        for channel_key in channels_to_try:
            sender = self.channel_senders.get(channel_key)
            if not sender:
                logger.error(f"No sender configured for channel '{channel_key}'. Skipping.")
                continue

            logger.debug(f"Attempting delivery of notification ID '{notification_id}' to user ID '{user_id}' via channel '{channel_key}'.")

            attempt_db = NotificationDeliveryAttempt(
                notification_id=notification_id,
                channel=channel_key,
                status="PENDING",
                attempt_count=1
            )
            self.db_session.add(attempt_db)
            await self.db_session.flush([attempt_db])

            try:
                send_result = await sender.send(user_to_notify=user_db, notification_content=notification_db)

                attempt_db.status = str(send_result.get("status", "FAILED")).upper()
                attempt_db.external_message_id = send_result.get("message_id")
                attempt_db.sent_at = datetime.now(timezone.utc)
                if attempt_db.status == "FAILED":
                    attempt_db.error_message = str(send_result.get("error", "Unknown send error"))

                logger.info(f"Delivery attempt for notification ID '{notification_id}' via {channel_key} to user ID '{user_id}': Status {attempt_db.status}, MsgID: {attempt_db.external_message_id}")

            except Exception as e:
                logger.error(f"Exception during send attempt for notification ID '{notification_id}' via {channel_key}: {e}", exc_info=True)
                attempt_db.status = "FAILED"
                attempt_db.error_message = str(e)
                attempt_db.sent_at = datetime.now(timezone.utc)

            self.db_session.add(attempt_db)
            # Don't commit yet, commit all attempts together after the loop

        try:
            await self.commit()
            for att_db in await self.db_session.execute(
                select(NotificationDeliveryAttempt).where(NotificationDeliveryAttempt.notification_id == notification_id) # Re-fetch to ensure all data
            ): # This is not ideal, should use the instances from `created_attempts` if they are still valid in session
                # A better way if created_attempts list was of ORM objects:
                # for att_db in created_attempts_orm_list: await self.db_session.refresh(att_db)
                # For now, let's assume we build responses from the current session state of these objects.
                # This part needs careful review of session object states.
                # For simplicity, we will assume the objects in `created_attempts_orm_list` (if we built one) are okay.
                # The current code doesn't explicitly build created_attempts_orm_list, so this re-fetch is conceptual.
                # Let's just build from the state before commit for now, then adjust if refresh pattern is different.
                pass # The objects are in session, from_orm should work.

            # Fetch attempts again to create responses
            final_attempts_stmt = select(NotificationDeliveryAttempt).where(
                NotificationDeliveryAttempt.notification_id == notification_id,
                NotificationDeliveryAttempt.channel.in_(channels_to_try) # Assuming we only care about attempts made now
            ).order_by(NotificationDeliveryAttempt.created_at.desc()) # Get latest if somehow multiple for same channel (should not happen with current logic)

            final_attempt_orms = (await self.db_session.execute(final_attempts_stmt)).scalars().unique().all()
            created_attempt_responses = [NotificationDeliveryAttemptResponse.from_orm(att) for att in final_attempt_orms]


        except Exception as e:
            await self.rollback()
            logger.error(f"Error committing delivery attempts for notification ID '{notification_id}': {e}", exc_info=True)
            return []

        logger.info(f"Completed all delivery attempts for notification ID '{notification_id}' to user ID '{user_id}'. {len(created_attempt_responses)} attempts processed and recorded.")
        return created_attempt_responses

    async def retry_failed_delivery_attempts(self, max_attempts: int = 3, age_threshold_hours: int = 24) -> int:
        logger.info(f"Retrying failed delivery attempts (max_attempts={max_attempts}, age_threshold_hours={age_threshold_hours}).")

        threshold_time = datetime.now(timezone.utc) - timedelta(hours=age_threshold_hours)

        stmt = select(NotificationDeliveryAttempt).options(
            selectinload(NotificationDeliveryAttempt.notification).selectinload(Notification.user).options(selectinload(User.user_type))
        ).where(
            NotificationDeliveryAttempt.status == "FAILED",
            NotificationDeliveryAttempt.attempt_count < max_attempts,
            NotificationDeliveryAttempt.created_at >= threshold_time
        ).order_by(NotificationDeliveryAttempt.created_at)

        failed_attempts_db = (await self.db_session.execute(stmt)).scalars().all()

        retried_count = 0
        if not failed_attempts_db:
            logger.info("No failed delivery attempts found eligible for retry.")
            return 0

        for attempt in failed_attempts_db:
            if not attempt.notification or not attempt.notification.user:
                logger.warning(f"Skipping retry for attempt ID {attempt.id}: missing notification or user data.")
                continue

            logger.info(f"Retrying delivery for notification ID '{attempt.notification_id}' (Attempt ID: {attempt.id}) to user ID '{attempt.notification.user.id}' via channel '{attempt.channel}'. Prior attempts: {attempt.attempt_count}.")

            sender = self.channel_senders.get(attempt.channel)
            if not sender:
                logger.error(f"No sender for channel '{attempt.channel}' of attempt ID {attempt.id}. Cannot retry.")
                continue

            # Create a NEW attempt record for this retry
            new_retry_attempt_db = NotificationDeliveryAttempt(
                notification_id=attempt.notification_id,
                channel=attempt.channel,
                status="PENDING",
                attempt_count=attempt.attempt_count + 1, # Increment attempt count
                # previous_attempt_id=attempt.id # Optional: link to previous attempt if model supports
            )
            self.db_session.add(new_retry_attempt_db)
            await self.db_session.flush([new_retry_attempt_db])

            try:
                send_result = await sender.send(user_to_notify=attempt.notification.user, notification_content=attempt.notification)
                new_retry_attempt_db.status = str(send_result.get("status", "FAILED")).upper()
                new_retry_attempt_db.external_message_id = send_result.get("message_id")
                new_retry_attempt_db.sent_at = datetime.now(timezone.utc)
                if new_retry_attempt_db.status == "FAILED":
                    new_retry_attempt_db.error_message = str(send_result.get("error", "Retry send error"))
                logger.info(f"Retry attempt {new_retry_attempt_db.attempt_count} for Notif ID '{attempt.notification_id}' via {attempt.channel}: Status {new_retry_attempt_db.status}")
                retried_count +=1
            except Exception as e:
                logger.error(f"Exception during retry send for Notif ID '{attempt.notification_id}' via {attempt.channel}: {e}", exc_info=True)
                new_retry_attempt_db.status = "FAILED"
                new_retry_attempt_db.error_message = str(e)
                new_retry_attempt_db.sent_at = datetime.now(timezone.utc)

            self.db_session.add(new_retry_attempt_db)
            # Mark the old attempt as "superseded" or "retried" to avoid picking it up again
            attempt.status = "RETRY_INITIATED" # Or a more final "FAILED_MAX_ATTEMPTS" if this was the last
            self.db_session.add(attempt)


        if retried_count > 0:
            await self.commit()
            logger.info(f"Processed {retried_count} delivery retries.")
        else:
            logger.info("No delivery attempts were actively retried in this run.")

        return retried_count

    async def list_delivery_attempts_for_notification(
        self, notification_id: UUID, skip: int = 0, limit: int = 10
    ) -> List[NotificationDeliveryAttemptResponse]:
        logger.debug(f"Listing delivery attempts for notification ID: {notification_id}")
        stmt = select(NotificationDeliveryAttempt).options(
            selectinload(NotificationDeliveryAttempt.notification)
        ).where(NotificationDeliveryAttempt.notification_id == notification_id) \
         .order_by(NotificationDeliveryAttempt.created_at.desc()).offset(skip).limit(limit)

        attempts_db = (await self.db_session.execute(stmt)).scalars().all()

        # response_list = [NotificationDeliveryAttemptResponse.model_validate(att) for att in attempts_db] # Pydantic v2
        response_list = [NotificationDeliveryAttemptResponse.from_orm(att) for att in attempts_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} delivery attempts for notification ID '{notification_id}'.")
        return response_list


logger.info("NotificationDeliveryService class defined.")
