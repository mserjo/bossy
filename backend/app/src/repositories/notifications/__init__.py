# backend/app/src/repositories/notifications/__init__.py
"""
Репозиторії для моделей, пов'язаних зі "Сповіщеннями", в програмі Kudos.

Цей пакет містить класи репозиторіїв для кожної моделі, що стосується
системи сповіщень: шаблонів сповіщень, самих сповіщень та спроб їх доставки.

Кожен репозиторій успадковує `BaseRepository` (або його похідні, наприклад,
`BaseDictionaryRepository` для шаблонів) та надає спеціалізований
інтерфейс для роботи з конкретною моделлю даних.
"""

from backend.app.src.repositories.notifications.notification_template_repository import NotificationTemplateRepository
from backend.app.src.repositories.notifications.notification_repository import NotificationRepository
from backend.app.src.repositories.notifications.delivery_attempt_repository import NotificationDeliveryAttemptRepository

__all__ = [
    "NotificationTemplateRepository",
    "NotificationRepository",
    "NotificationDeliveryAttemptRepository",
]
