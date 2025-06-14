# backend/app/src/schemas/notifications/__init__.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для сутностей, пов'язаних зі сповіщеннями.

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються:
- Шаблонів сповіщень (`NotificationTemplate...Schema` з `template.py`).
- Самих сповіщень, що надсилаються користувачам (`Notification...Schema` з `notification.py`).
- Записів про спроби доставки цих сповіщень (`NotificationDeliveryAttempt...Schema` з `delivery.py`).

Моделі з цього пакету експортуються для використання в сервісному шарі,
API ендпоінтах та інших частинах додатку, що реалізують логіку сповіщень.
"""

# Імпорт централізованого логера
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Схеми, пов'язані з Шаблонами Сповіщень
from backend.app.src.schemas.notifications.template import (
    NotificationTemplateBaseSchema,
    NotificationTemplateCreateSchema,
    NotificationTemplateUpdateSchema,
    NotificationTemplateSchema  # Використовуємо фактичну назву
)

# Схеми, пов'язані зі Сповіщеннями
from backend.app.src.schemas.notifications.notification import (
    NotificationBaseSchema,
    NotificationCreateSchema,
    NotificationUpdateSchema,
    NotificationSchema  # Використовуємо фактичну назву
)

# Схеми, пов'язані зі Спробами Доставки Сповіщень
from backend.app.src.schemas.notifications.delivery import (
    NotificationDeliveryAttemptBaseSchema,
    NotificationDeliveryAttemptCreateSchema,
    # NotificationDeliveryAttemptUpdateSchema, # Оновлення спроб зазвичай не передбачено
    NotificationDeliveryAttemptSchema  # Використовуємо фактичну назву
)

__all__ = [
    # NotificationTemplate schemas
    "NotificationTemplateBaseSchema",
    "NotificationTemplateCreateSchema",
    "NotificationTemplateUpdateSchema",
    "NotificationTemplateSchema",
    # Notification schemas
    "NotificationBaseSchema",
    "NotificationCreateSchema",
    "NotificationUpdateSchema",
    "NotificationSchema",
    # NotificationDeliveryAttempt schemas
    "NotificationDeliveryAttemptBaseSchema",
    "NotificationDeliveryAttemptCreateSchema",
    # "NotificationDeliveryAttemptUpdateSchema",
    "NotificationDeliveryAttemptSchema",
]

logger.debug("Ініціалізація пакету схем Pydantic `notifications`...")
