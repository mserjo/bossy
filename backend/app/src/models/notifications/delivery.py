# backend/app/src/models/notifications/delivery.py

"""
SQLAlchemy model for Notification Delivery Attempts.
Tracks the status of attempts to deliver a notification via different channels.
"""

import logging
from typing import Optional, TYPE_CHECKING, Dict, Any # For Mapped type hints
from datetime import datetime, timezone, timedelta # Added timezone, timedelta for __main__
from enum import Enum as PythonEnum # For Enum definitions

from sqlalchemy import ForeignKey, Text, DateTime, String, Enum as SQLAlchemyEnum, Integer, JSON # Added Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func # For server_default on attempted_at

from backend.app.src.models.base import BaseModel
# Assuming NotificationChannelEnum is defined in template.py or a central dicts module.
# For robust imports, centralize enums, e.g., in backend.app.src.core.dicts
try:
    from backend.app.src.models.notifications.template import NotificationChannelEnum
except ImportError:
    # Fallback if template.py is not yet created or enum moved, define locally for this file to be self-contained for now
    logger.warning("NotificationChannelEnum not found in template.py, using local definition for NotificationDeliveryAttempt.")
    class NotificationChannelEnum(PythonEnum):
        IN_APP = "in_app"
        EMAIL = "email"
        SMS = "sms"
        PUSH = "push"

# Configure logger for this module
logger = logging.getLogger(__name__)

class DeliveryStatusEnum(PythonEnum): # Changed to inherit from PythonEnum
    """ Defines the status of a notification delivery attempt. """
    PENDING = "pending"     # Attempt has not been made yet / is queued.
    SENT = "sent"           # Notification was successfully sent to the provider (e.g., email server, SMS gateway).
    FAILED = "failed"         # Attempt to send failed (e.g., connection error, invalid address before send).
    DELIVERED = "delivered"   # Confirmed delivery (if supported by provider, e.g., push notification acknowledged).
    UNDELIVERABLE = "undeliverable" # Confirmed undeliverable (e.g., hard bounce email, invalid phone number from provider).
    # READ = "read"           # Read status is usually on the Notification model itself by user action.

if TYPE_CHECKING:
    from backend.app.src.models.notifications.notification import Notification

class NotificationDeliveryAttempt(BaseModel):
    """
    Represents an attempt to deliver a specific notification via a particular channel.
    A single notification might have multiple delivery attempts if retries occur or if sent via multiple channels.

    Attributes:
        notification_id (int): Foreign key to the notification being delivered.
        channel (NotificationChannelEnum): The channel used for this delivery attempt (e.g., email, sms).
        status (DeliveryStatusEnum): The outcome of this delivery attempt.
        attempted_at (datetime): Timestamp when the delivery attempt was made.
        external_message_id (Optional[str]): ID from the external provider (e.g., email Message-ID, SMS gateway transaction ID).
        error_message (Optional[str]): Error message if the delivery attempt failed.
        provider_response (Optional[Dict]): Raw response or details from the delivery provider (stored as JSON).
        # `id`, `created_at`, `updated_at` from BaseModel.
        # `created_at` can indicate when this attempt record was created/queued.
    """
    __tablename__ = "notification_delivery_attempts"

    notification_id: Mapped[int] = mapped_column(Integer, ForeignKey("notifications.id"), nullable=False, index=True, comment="FK to the notification being delivered")

    channel: Mapped[NotificationChannelEnum] = mapped_column(
        SQLAlchemyEnum(NotificationChannelEnum, name="delivery_notificationchannelenum", native_enum=False, create_constraint=True),
        nullable=False,
        index=True,
        comment="Channel used for this delivery attempt (e.g., email, sms)"
    )

    status: Mapped[DeliveryStatusEnum] = mapped_column(
        SQLAlchemyEnum(DeliveryStatusEnum, name="deliverystatusenum", native_enum=False, create_constraint=True),
        nullable=False,
        default=DeliveryStatusEnum.PENDING,
        index=True,
        comment="Outcome of this delivery attempt (e.g., sent, failed, delivered)"
    )

    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the delivery attempt was made/initiated (UTC)"
    )

    external_message_id: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, index=True, comment="ID from the external provider (e.g., email Message-ID)")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Error message if the delivery attempt failed")
    provider_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="Raw response or details from the delivery provider (JSON)")

    # --- Relationships ---
    notification: Mapped["Notification"] = relationship(back_populates="delivery_attempts")

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        # Ensure channel and status are accessed correctly, especially if they are Enum objects
        channel_val = self.channel.value if isinstance(self.channel, PythonEnum) else self.channel
        status_val = self.status.value if isinstance(self.status, PythonEnum) else self.status
        return f"<NotificationDeliveryAttempt(id={id_val}, notification_id={self.notification_id}, channel='{channel_val}', status='{status_val}')>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- NotificationDeliveryAttempt Model --- Demonstration")

    # Example NotificationDeliveryAttempt instances
    # Assume Notification id=1 exists
    attempt1_email_sent = NotificationDeliveryAttempt(
        notification_id=1,
        channel=NotificationChannelEnum.EMAIL, # Use the Enum member here
        status=DeliveryStatusEnum.SENT,       # Use the Enum member here
        attempted_at=datetime.now(timezone.utc) - timedelta(seconds=30),
        external_message_id="<CAOjp2BFk...@mail.gmail.com>"
    )
    attempt1_email_sent.id = 1 # Simulate ORM-set ID
    attempt1_email_sent.created_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    attempt1_email_sent.updated_at = datetime.now(timezone.utc) - timedelta(seconds=30)

    logger.info(f"Example Successful Email Delivery Attempt: {attempt1_email_sent!r}")
    logger.info(f"  Notification ID: {attempt1_email_sent.notification_id}, Channel: {attempt1_email_sent.channel.value}") # Access .value for Enum
    logger.info(f"  Status: {attempt1_email_sent.status.value}") # Access .value for Enum
    logger.info(f"  External ID: {attempt1_email_sent.external_message_id}")
    logger.info(f"  Attempted At: {attempt1_email_sent.attempted_at.isoformat() if attempt1_email_sent.attempted_at else 'N/A'}")
    logger.info(f"  Created At: {attempt1_email_sent.created_at.isoformat() if attempt1_email_sent.created_at else 'N/A'}")


    attempt2_sms_failed = NotificationDeliveryAttempt(
        notification_id=2, # Assume Notification id=2 exists
        channel=NotificationChannelEnum.SMS,
        status=DeliveryStatusEnum.FAILED,
        attempted_at=datetime.now(timezone.utc) - timedelta(minutes=2),
        error_message="Invalid phone number format or number not reachable.",
        provider_response={"gateway_error_code": "E-203"}
    )
    attempt2_sms_failed.id = 2
    logger.info(f"Example Failed SMS Delivery Attempt: {attempt2_sms_failed!r}")
    logger.info(f"  Error: {attempt2_sms_failed.error_message}")
    logger.info(f"  Provider Response: {attempt2_sms_failed.provider_response}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"NotificationDeliveryAttempt attributes (conceptual table columns): {[c.name for c in NotificationDeliveryAttempt.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
