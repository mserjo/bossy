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
from backend.app.src.config import logger

# Схеми, пов'язані з Шаблонами Сповіщень
from backend.app.src.schemas.notifications.template import (
    NotificationTemplateBaseSchema,
    NotificationTemplateCreateSchema,
    NotificationTemplateUpdateSchema,
    NotificationTemplateResponseSchema  # Оновлено ім'я
)

# Схеми, пов'язані зі Сповіщеннями
from backend.app.src.schemas.notifications.notification import (
    NotificationBaseSchema,
    NotificationCreateSchema,
    NotificationUpdateSchema,
    NotificationResponseSchema  # Оновлено ім'я
)

# Схеми, пов'язані зі Спробами Доставки Сповіщень
from backend.app.src.schemas.notifications.delivery import (
    NotificationDeliveryAttemptBaseSchema,
    NotificationDeliveryAttemptCreateSchema,
    # NotificationDeliveryAttemptUpdateSchema, # Оновлення спроб зазвичай не передбачено
    NotificationDeliveryAttemptResponseSchema  # Оновлено ім'я
)

__all__ = [
    # NotificationTemplate schemas
    "NotificationTemplateBaseSchema",
    "NotificationTemplateCreateSchema",
    "NotificationTemplateUpdateSchema",
    "NotificationTemplateResponseSchema", # Оновлено ім'я
    # Notification schemas
    "NotificationBaseSchema",
    "NotificationCreateSchema",
    "NotificationUpdateSchema",
    "NotificationResponseSchema", # Оновлено ім'я
    # NotificationDeliveryAttempt schemas
    "NotificationDeliveryAttemptBaseSchema",
    "NotificationDeliveryAttemptCreateSchema",
    # "NotificationDeliveryAttemptUpdateSchema",
    "NotificationDeliveryAttemptResponseSchema", # Оновлено ім'я
]

logger.debug("Ініціалізація пакету схем Pydantic `notifications`...")
