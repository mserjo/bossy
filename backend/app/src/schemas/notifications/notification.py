# backend/app/src/schemas/notifications/notification.py
import logging
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, Literal

from pydantic import BaseModel, Field

from app.src.schemas.base import BaseDBRead # Common DB fields
# Enum for notification status - can be moved to a common location if used elsewhere
# from app.src.core.dicts import NotificationStatusEnum

# Initialize logger for this module
logger = logging.getLogger(__name__)

# --- Notification Status Enum (Example, can be defined in core.dicts or constants) ---
# Using Literal for now as a simple Enum alternative within Pydantic
NotificationStatusLiterals = Literal["unread", "read", "archived", "deleted"]
NotificationTypeLiterals = Literal["system_alert", "task_update", "group_invite", "new_badge", "event_reminder", "general_info"]

# --- Notification Schemas ---

class NotificationBase(BaseModel):
    """
    Base schema for notifications.
    """
    user_id: UUID = Field(..., description="The unique identifier of the user receiving the notification.")
    title: str = Field(..., min_length=3, max_length=150, description="The title of the notification.")
    message: str = Field(..., max_length=1000, description="The main content/message of the notification.")
    notification_type: NotificationTypeLiterals = Field(
        ...,
        description="The type of notification (e.g., 'system_alert', 'task_update')."
    )
    payload: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional JSON payload with additional context or deep-linking information (e.g., {'task_id': 'uuid', 'group_id': 'uuid'})."
    )

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "NotificationBase"
        json_schema_extra = {
            "example": {
                "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "title": "New Task Assigned",
                "message": "You have been assigned a new task: 'Complete Project Proposal'.",
                "notification_type": "task_update",
                "payload": {"task_id": "c1d2e3f4-a5b6-c7d8-e9f0-a1b2c3d4e5f6"}
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"NotificationBase instance created with data: {data}")


class NotificationCreateInternal(NotificationBase):
    """
    Schema for creating a new notification internally by services.
    Includes initial status.
    """
    status: NotificationStatusLiterals = Field(
        "unread",
        description="Initial status of the notification, defaults to 'unread'."
    )
    # sent_at: Optional[datetime] = Field(None, description="Timestamp when the notification was actually sent or made available. Can be set by the service.")


    class Config(NotificationBase.Config):
        title = "NotificationCreateInternal"
        json_schema_extra = {
            "example": {
                "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "title": "Welcome to Kudos!",
                "message": "Thank you for joining our platform. We hope you enjoy the gamified experience.",
                "notification_type": "general_info",
                "status": "unread",
                "payload": {"welcome_bonus_points": 100}
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"NotificationCreateInternal instance created for user '{self.user_id}', title '{self.title}'.")


class NotificationUpdate(BaseModel):
    """
    Schema for updating a notification, e.g., marking it as read or archived.
    """
    status: Optional[NotificationStatusLiterals] = Field(
        None,
        description="New status for the notification (e.g., 'read', 'archived')."
    )
    # read_at: Optional[datetime] = Field(None, description="Timestamp when the notification was marked as read. Could be set by logic when status changes to 'read'.")

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "NotificationUpdate"
        json_schema_extra = {
            "example": {
                "status": "read"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"NotificationUpdate instance created with update data: {data}")


class NotificationResponse(NotificationBase, BaseDBRead):
    """
    Schema for representing a notification in API responses.
    """
    # id: UUID # From BaseDBRead
    status: NotificationStatusLiterals = Field(..., description="Current status of the notification.")
    # read_at: Optional[datetime] = Field(None, description="Timestamp when the notification was marked as read.")
    # sent_at: Optional[datetime] = Field(None, description="Timestamp when the notification was sent/generated.")
    # created_at: datetime # From BaseDBRead
    # updated_at: datetime # From BaseDBRead

    class Config(NotificationBase.Config): # Inherit Config from NotificationBase for orm_mode and title
        title = "NotificationResponse" # Override title if needed
        json_schema_extra = { # Override or extend example
            "example": {
                "id": "b2c3d4e5-f6a7-8901-2345-67890abcdef01",
                "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "title": "New Task Assigned",
                "message": "You have been assigned a new task: 'Complete Project Proposal'.",
                "notification_type": "task_update",
                "status": "unread",
                "payload": {"task_id": "c1d2e3f4-a5b6-c7d8-e9f0-a1b2c3d4e5f6"},
                "created_at": "2023-06-10T10:00:00Z",
                "updated_at": "2023-06-10T10:00:00Z",
                # "read_at": None,
                # "sent_at": "2023-06-10T10:00:05Z"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"NotificationResponse instance created for notification ID '{self.id}'.")

logger.info("Notification schemas (NotificationBase, NotificationCreateInternal, NotificationUpdate, NotificationResponse) defined successfully.")
