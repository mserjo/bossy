# backend/app/src/schemas/notifications/__init__.py
import logging

# Initialize logger for this module
logger = logging.getLogger(__name__)

logger.info("Notification schemas package initialized.")

# Import all schemas from this package to make them easily accessible
from .notification import (
    NotificationBase,
    NotificationCreateInternal,
    NotificationUpdate,
    NotificationResponse,
)
from .template import (
    NotificationTemplateBase,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateResponse,
)
from .delivery import (
    NotificationDeliveryAttemptBase,
    NotificationDeliveryAttemptCreate,
    NotificationDeliveryAttemptResponse,
)

__all__ = [
    # Notification schemas
    "NotificationBase",
    "NotificationCreateInternal",
    "NotificationUpdate",
    "NotificationResponse",
    # NotificationTemplate schemas
    "NotificationTemplateBase",
    "NotificationTemplateCreate",
    "NotificationTemplateUpdate",
    "NotificationTemplateResponse",
    # NotificationDeliveryAttempt schemas
    "NotificationDeliveryAttemptBase",
    "NotificationDeliveryAttemptCreate",
    "NotificationDeliveryAttemptResponse",
]

logger.info(f"Successfully imported notification schemas: {__all__}")
