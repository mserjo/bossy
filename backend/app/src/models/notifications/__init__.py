# backend/app/src/models/notifications/__init__.py

"""
This package contains SQLAlchemy models related to notifications, including
the notifications themselves, templates for generating them, and delivery statuses.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Notification models package initialized.")

# Example of re-exporting for easier access:
# from .notification import Notification
# from .template import NotificationTemplate
# from .delivery import NotificationDeliveryAttempt

# __all__ = [
#     "Notification",
#     "NotificationTemplate",
#     "NotificationDeliveryAttempt",
# ]
