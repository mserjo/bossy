# backend/app/src/services/notifications/delivery_channels.py
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List # Added List for push_tokens
from uuid import uuid4 # For placeholder message IDs

from app.src.models.auth.user import User # For user details like email, phone
from app.src.models.notifications.notification import Notification # The notification content
# from app.src.config.settings import settings # For API keys, SMTP config etc.

# Initialize logger for this module
logger = logging.getLogger(__name__)

class ChannelSender(ABC):
    """
    Abstract Base Class for notification channel senders.
    Defines the interface for sending a notification through a specific channel.
    """

    @abstractmethod
    async def send(
        self,
        user_to_notify: User,
        notification_content: Notification,
    ) -> Dict[str, Any]:
        """
        Sends the notification.

        Args:
            user_to_notify (User): The recipient user object.
            notification_content (Notification): The notification object containing title, message, etc.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - "status": "success" or "failed"
                - "message_id": Optional external message ID from the provider.
                - "error": Optional error message if failed.
                - "channel_type": The type of channel used (e.g., "EMAIL", "SMS").
        """
        pass

class EmailNotificationService(ChannelSender):
    """
    Handles sending notifications via Email.
    Actual email sending logic is a placeholder.
    """
    channel_type = "EMAIL"

    async def send(
        self,
        user_to_notify: User,
        notification_content: Notification,
    ) -> Dict[str, Any]:
        recipient_email = getattr(user_to_notify, 'email', None)
        if not recipient_email:
            logger.warning(f"User ID '{user_to_notify.id}' has no email address. Cannot send email notification ID '{notification_content.id}'.")
            return {"status": "failed", "error": "User has no email address.", "channel_type": self.channel_type}

        subject = notification_content.title
        body = notification_content.message

        message_id = f"placeholder_email_msg_id_{notification_content.id}_{uuid4()}"
        logger.info(f"[PLACEHOLDER] Sending EMAIL notification ID '{notification_content.id}':")
        logger.info(f"  To: {recipient_email} (User: {getattr(user_to_notify, 'username', user_to_notify.id)})")
        logger.info(f"  Subject: {subject}")
        logger.info(f"  Body: {body[:100]}...")
        logger.info(f"  Email sent (simulated). Message ID: {message_id}")

        return {"status": "success", "message_id": message_id, "channel_type": self.channel_type}


class SmsNotificationService(ChannelSender):
    """
    Handles sending notifications via SMS.
    Actual SMS sending logic is a placeholder.
    """
    channel_type = "SMS"

    async def send(
        self,
        user_to_notify: User,
        notification_content: Notification,
    ) -> Dict[str, Any]:
        phone_number = getattr(user_to_notify, 'phone_number', None)
        if not phone_number:
            logger.warning(f"User ID '{user_to_notify.id}' has no phone number. Cannot send SMS for notification ID '{notification_content.id}'.")
            return {"status": "failed", "error": "User has no phone number.", "channel_type": self.channel_type}

        sms_text = f"{notification_content.title}: {notification_content.message}"
        max_sms_length = 160
        if len(sms_text) > max_sms_length:
            sms_text = sms_text[:max_sms_length-3] + "..."
            logger.warning(f"SMS text for notification ID '{notification_content.id}' was truncated to {max_sms_length} chars.")

        message_id = f"placeholder_sms_msg_id_{notification_content.id}_{uuid4()}"
        logger.info(f"[PLACEHOLDER] Sending SMS notification ID '{notification_content.id}':")
        logger.info(f"  To: {phone_number} (User: {getattr(user_to_notify, 'username', user_to_notify.id)})")
        logger.info(f"  Text: {sms_text}")
        logger.info(f"  SMS sent (simulated). Message ID: {message_id}")

        return {"status": "success", "message_id": message_id, "channel_type": self.channel_type}


class PushNotificationService(ChannelSender):
    """
    Handles sending Push Notifications (e.g., via FCM, APNS).
    Actual push notification sending logic is a placeholder.
    """
    channel_type = "PUSH"

    async def send(
        self,
        user_to_notify: User,
        notification_content: Notification,
    ) -> Dict[str, Any]:
        push_tokens: List[str] = getattr(user_to_notify, 'active_push_tokens', [])

        if not push_tokens:
            logger.warning(f"User ID '{user_to_notify.id}' has no active push tokens. Cannot send push for notification ID '{notification_content.id}'.")
            return {"status": "failed", "error": "User has no active push tokens.", "channel_type": self.channel_type}

        title = notification_content.title
        body = notification_content.message
        payload = notification_content.payload or {}

        message_id = f"placeholder_push_batch_id_{notification_content.id}_{uuid4()}"
        logger.info(f"[PLACEHOLDER] Sending PUSH notification ID '{notification_content.id}':")
        logger.info(f"  To User: {getattr(user_to_notify, 'username', user_to_notify.id)} (Tokens: {push_tokens})")
        logger.info(f"  Title: {title}")
        logger.info(f"  Body: {body[:100]}...")
        logger.info(f"  Payload: {payload}")
        logger.info(f"  Push notification sent (simulated). Batch ID: {message_id}")

        return {"status": "success", "message_id": message_id, "sent_to_tokens": len(push_tokens), "channel_type": self.channel_type}


logger.info("Notification channel sender services (Email, SMS, Push placeholders) defined.")
