# backend/app/src/schemas/notifications/delivery.py
import logging
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field

from app.src.schemas.base import BaseDBRead # Common DB fields

# Initialize logger for this module
logger = logging.getLogger(__name__)

# --- Notification Delivery Status Enum (Example) ---
DeliveryChannelLiterals = Literal["email", "sms", "push_notification", "in_app_internal", "webhook", "messenger_bot"]
DeliveryStatusLiterals = Literal["pending", "sent", "failed", "delivered", "read", "undeliverable", "skipped"]

# --- NotificationDeliveryAttempt Schemas ---

class NotificationDeliveryAttemptBase(BaseModel):
    """
    Base schema for tracking attempts to deliver a notification.
    """
    notification_id: UUID = Field(..., description="The unique identifier of the notification being delivered.")
    channel: DeliveryChannelLiterals = Field(
        ...,
        description="The delivery channel used for this attempt (e.g., 'email', 'sms', 'push_notification')."
    )
    status: DeliveryStatusLiterals = Field(
        "pending",
        description="Current status of this delivery attempt."
    )
    attempt_count: int = Field(
        1,
        ge=1,
        description="The number of times delivery has been attempted via this channel for this notification."
    )
    sent_at: Optional[datetime] = Field(
        None,
        description="Timestamp when the delivery attempt was initiated/sent. Can be None if still pending."
    )
    # delivered_at: Optional[datetime] = Field(None, description="Timestamp when the notification was confirmed delivered (if supported by channel).")
    # read_at: Optional[datetime] = Field(None, description="Timestamp when the notification was confirmed read (if supported by channel).")
    error_message: Optional[str] = Field(
        None,
        max_length=1000,
        description="Error message if the delivery attempt failed."
    )
    # external_message_id: Optional[str] = Field(None, max_length=255, description="ID from the external service (e.g., SES Message ID, Twilio SID).")

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "NotificationDeliveryAttemptBase"
        json_schema_extra = {
            "example": {
                "notification_id": "b2c3d4e5-f6a7-8901-2345-67890abcdef01",
                "channel": "email",
                "status": "sent",
                "attempt_count": 1,
                "sent_at": "2023-06-10T10:00:05Z",
                "error_message": None,
                # "external_message_id": "0100017aabcdef01-01234567-0123-0123-0123-0123456789ab-000000"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"NotificationDeliveryAttemptBase instance created with data: {data}")


class NotificationDeliveryAttemptCreate(NotificationDeliveryAttemptBase):
    """
    Schema for creating a new notification delivery attempt record.
    Typically used internally by notification services.
    """
    pass

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"NotificationDeliveryAttemptCreate instance for notification '{self.notification_id}' via '{self.channel}'.")

# No Update schema is typically defined for delivery attempts, as they are usually immutable records of an attempt.
# New attempts would create new records. Status updates might occur on the existing record via service logic.

class NotificationDeliveryAttemptResponse(NotificationDeliveryAttemptBase, BaseDBRead):
    """
    Schema for representing a notification delivery attempt in API responses.
    """
    # id: UUID # From BaseDBRead
    # created_at: datetime # From BaseDBRead
    # updated_at: datetime # From BaseDBRead (reflects last status change)

    class Config(NotificationDeliveryAttemptBase.Config):
        title = "NotificationDeliveryAttemptResponse"
        json_schema_extra = { # Override or extend example
            "example": {
                "id": "d4e5f6a7-b8c9-0123-4567-890abcdef0123",
                "notification_id": "b2c3d4e5-f6a7-8901-2345-67890abcdef01",
                "channel": "email",
                "status": "delivered", # Example of a later status
                "attempt_count": 1,
                "sent_at": "2023-06-10T10:00:05Z",
                # "delivered_at": "2023-06-10T10:01:15Z",
                "error_message": None,
                # "external_message_id": "0100017aabcdef01-01234567-0123-0123-0123-0123456789ab-000000",
                "created_at": "2023-06-10T10:00:04Z",
                "updated_at": "2023-06-10T10:01:15Z" # Updated when status changed to 'delivered'
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"NotificationDeliveryAttemptResponse instance created for attempt ID '{self.id}'.")

logger.info("NotificationDeliveryAttempt schemas (NotificationDeliveryAttemptBase, NotificationDeliveryAttemptCreate, NotificationDeliveryAttemptResponse) defined successfully.")
