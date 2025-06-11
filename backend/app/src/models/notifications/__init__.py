# backend/app/src/models/notifications/__init__.py
"""
Пакет моделей SQLAlchemy для сутностей, пов'язаних зі "Сповіщеннями".

Цей пакет містить моделі для представлення шаблонів сповіщень,
самих сповіщень, надісланих користувачам, та спроб їх доставки
в програмі Kudos.

Моделі експортуються для зручного доступу з інших частин програми.
"""

from .template import NotificationTemplate
from .notification import Notification
from .delivery import NotificationDeliveryAttempt

__all__ = [
    "NotificationTemplate",
    "Notification",
    "NotificationDeliveryAttempt",
]

# Майбутні моделі, пов'язані зі сповіщеннями (наприклад, UserNotificationPreferences),
# також можуть бути додані сюди для експорту.
