# backend/app/src/services/notifications/notification.py
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.notifications.notification import Notification # SQLAlchemy Model
from app.src.models.auth.user import User # For user_id
from app.src.models.notifications.template import NotificationTemplate # For using templates

from app.src.schemas.notifications.notification import ( # Pydantic Schemas
    NotificationCreateInternal, # For service-level creation
    NotificationUpdate, # For status changes like mark as read
    NotificationResponse
)
# from app.src.services.notifications.template import NotificationTemplateService # For fetching/rendering templates
# from app.src.services.notifications.delivery import NotificationDeliveryService # For triggering delivery

# Initialize logger for this module
logger = logging.getLogger(__name__)

class NotificationService(BaseService):
    """
    Service for managing user notifications within the application.
    Handles creation (potentially from templates), retrieval, and status updates
    (e.g., marking as read/unread).
    Actual sending of notifications (email, SMS, push) is typically delegated
    to NotificationDeliveryService.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("NotificationService initialized.")

    async def get_notification_by_id(self, notification_id: UUID, user_id: Optional[UUID] = None) -> Optional[NotificationResponse]:
        log_ctx = f"notification ID '{notification_id}'"
        if user_id: log_ctx += f" for user ID '{user_id}'"
        logger.debug(f"Attempting to retrieve {log_ctx}.")

        stmt = select(Notification).options(
            selectinload(Notification.user).options(selectinload(User.user_type)) if hasattr(Notification, 'user') else None
        ).where(Notification.id == notification_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))


        if user_id:
            stmt = stmt.where(Notification.user_id == user_id)

        notification_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if notification_db:
            logger.info(f"Notification with ID '{notification_id}' found.")
            # return NotificationResponse.model_validate(notification_db) # Pydantic v2
            return NotificationResponse.from_orm(notification_db) # Pydantic v1

        logger.info(f"Notification with ID '{notification_id}' not found (or not owned by user).")
        return None

    async def create_notification(
        self,
        notification_data: NotificationCreateInternal,
        trigger_delivery: bool = False
    ) -> NotificationResponse:
        logger.debug(f"Attempting to create notification for user ID '{notification_data.user_id}', title: '{notification_data.title}'.")

        user = await self.db_session.get(User, notification_data.user_id)
        if not user:
            raise ValueError(f"User with ID '{notification_data.user_id}' not found. Cannot create notification.")

        notification_db_data = notification_data.dict()

        new_notification_db = Notification(**notification_db_data)

        self.db_session.add(new_notification_db)
        try:
            await self.commit()
            refresh_attrs = []
            if hasattr(Notification, 'user'): refresh_attrs.append('user')
            if refresh_attrs: await self.db_session.refresh(new_notification_db, attribute_names=refresh_attrs)
            else: await self.db_session.refresh(new_notification_db) # Default refresh if no specific relations
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error creating notification for user '{notification_data.user_id}': {e}", exc_info=True)
            raise ValueError(f"Could not create notification due to a data conflict: {e}")

        logger.info(f"Notification ID '{new_notification_db.id}' created successfully for user ID '{new_notification_db.user_id}'.")

        if trigger_delivery:
            logger.info(f"Triggering delivery for notification ID '{new_notification_db.id}'.")
            # from app.src.services.notifications.delivery import NotificationDeliveryService
            # delivery_service = NotificationDeliveryService(self.db_session)
            # await delivery_service.queue_notification_for_delivery(new_notification_db.id)
            logger.warning(f"Delivery triggering for notification ID '{new_notification_db.id}' is a placeholder.")

        # return NotificationResponse.model_validate(new_notification_db) # Pydantic v2
        return NotificationResponse.from_orm(new_notification_db) # Pydantic v1

    async def create_notification_from_template(
        self,
        template_name: str,
        user_id: UUID,
        context_data: Dict[str, Any],
        notification_type_override: Optional[str] = None,
        payload_override: Optional[Dict[str, Any]] = None,
        trigger_delivery: bool = True
    ) -> Optional[NotificationResponse]:
        logger.debug(f"Creating notification for user ID '{user_id}' from template '{template_name}'.")

        from app.src.services.notifications.template import NotificationTemplateService
        template_service = NotificationTemplateService(self.db_session)

        template = await template_service.get_template_by_name(template_name)
        if not template:
            logger.error(f"NotificationTemplate '{template_name}' not found. Cannot create notification.")
            return None

        try:
            rendered_subject, rendered_body = template_service.render_template(template, context_data)
        except Exception as e: # Catch rendering errors
            logger.error(f"Error rendering template '{template_name}' for user '{user_id}': {e}", exc_info=True)
            raise ValueError(f"Failed to render notification template '{template_name}': {e}")

        final_payload = template.default_vars.copy() if template.default_vars else {}
        if payload_override:
            final_payload.update(payload_override)

        # Use template.template_type if notification_type_override is not provided.
        # template.template_type from schema is already a string (e.g. "email", "in_app")
        final_notification_type = notification_type_override or template.template_type

        create_data = NotificationCreateInternal(
            user_id=user_id,
            title=rendered_subject or template.name,
            message=rendered_body,
            notification_type=final_notification_type,
            status="unread",
            payload=final_payload if final_payload else None,
            # template_id=template.id # If Notification model links back to template using template_id
        )
        if hasattr(Notification, 'template_id') and template.id: # Check model field
            setattr(create_data, 'template_id', template.id)


        return await self.create_notification(create_data, trigger_delivery=trigger_delivery)


    async def mark_notifications_as_status(
        self,
        notification_ids: List[UUID],
        user_id: UUID,
        status: str
    ) -> int:
        logger.info(f"User ID '{user_id}' attempting to mark {len(notification_ids)} notifications as '{status}'.")
        if not notification_ids: return 0

        stmt = select(Notification).where(
            Notification.id.in_(notification_ids),
            Notification.user_id == user_id,
            Notification.status != status
        )
        notifications_to_update_db = (await self.db_session.execute(stmt)).scalars().all()

        if not notifications_to_update_db:
            logger.info(f"No notifications found for user ID '{user_id}' matching IDs {notification_ids} that require status update to '{status}'.")
            return 0

        updated_count = 0
        for notification_db in notifications_to_update_db:
            notification_db.status = status
            if status == "read" and hasattr(notification_db, 'read_at'):
                notification_db.read_at = datetime.now(timezone.utc)
            self.db_session.add(notification_db)
            updated_count += 1

        if updated_count > 0:
            await self.commit()
            logger.info(f"Successfully marked {updated_count} notifications as '{status}' for user ID '{user_id}'.")

        return updated_count

    async def get_user_notifications(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        notification_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[NotificationResponse]:
        logger.debug(f"Listing notifications for user ID: {user_id}, status: {status}, type: {notification_type}, skip={skip}, limit={limit}")

        stmt = select(Notification).options(
            selectinload(Notification.user).options(selectinload(User.user_type)) if hasattr(Notification, 'user') else None
            ).where(Notification.user_id == user_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))

        if status:
            stmt = stmt.where(Notification.status == status)
        if notification_type:
            stmt = stmt.where(Notification.notification_type == notification_type)

        stmt = stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)

        notifications_db = (await self.db_session.execute(stmt)).scalars().all()

        # response_list = [NotificationResponse.model_validate(n) for n in notifications_db] # Pydantic v2
        response_list = [NotificationResponse.from_orm(n) for n in notifications_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} notifications for user ID '{user_id}'.")
        return response_list

    async def delete_notification(self, notification_id: UUID, user_id: UUID) -> bool:
        logger.debug(f"User ID '{user_id}' attempting to delete notification ID '{notification_id}'.")

        notification_db = await self.db_session.get(Notification, notification_id)
        if not notification_db:
            logger.warning(f"Notification ID '{notification_id}' not found for deletion.")
            return False

        if notification_db.user_id != user_id:
            logger.error(f"User ID '{user_id}' not authorized to delete notification ID '{notification_id}' (owner: {notification_db.user_id}).")
            return False

        await self.db_session.delete(notification_db)
        await self.commit()
        logger.info(f"Notification ID '{notification_id}' deleted successfully by user ID '{user_id}'.")
        return True

logger.info("NotificationService class defined.")
