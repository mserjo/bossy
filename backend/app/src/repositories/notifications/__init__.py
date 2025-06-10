# backend/app/src/repositories/notifications/__init__.py

"""
This package contains repository classes for notification-related entities.

Modules within this package will define repositories for notifications,
notification templates, and delivery attempts.
"""

# Import and re-export repository classes here as they are created.
# This allows for cleaner imports from other parts of the application,
# e.g., `from app.src.repositories.notifications import NotificationRepository`.

from .notification_repository import NotificationRepository
from .notification_template_repository import NotificationTemplateRepository
from .delivery_attempt_repository import NotificationDeliveryAttemptRepository


# Define __all__ to specify which names are exported when `from .notifications import *` is used.
# This also helps linters and IDEs understand the public API of this package.
__all__ = [
    "NotificationRepository",
    "NotificationTemplateRepository",
    "NotificationDeliveryAttemptRepository",
]

# Detailed comments:
# This __init__.py file initializes the 'notifications' sub-package within the
# 'repositories' package. Its primary roles are:
#
# 1. Package Recognition:
#    It makes Python treat the 'repositories/notifications' directory as a sub-package.
#
# 2. Namespace Management:
#    It serves as a central point for importing and re-exporting repository
#    classes defined in other modules within this sub-package. This simplifies
#    access for other application layers.
#
# 3. Public API Definition (`__all__`):
#    The `__all__` list explicitly declares which symbols are part of the public
#    interface of this sub-package.
#
# This structure promotes a clean and organized data access layer for
# notification components.
