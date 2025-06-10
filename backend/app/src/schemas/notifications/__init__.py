# backend/app/src/schemas/notifications/__init__.py
"""
Pydantic схеми для сутностей, пов'язаних зі "Сповіщеннями".

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються шаблонів сповіщень,
самих сповіщень та спроб їх доставки в програмі Kudos.
"""

# Схеми, пов'язані з Шаблонами Сповіщень
from .template import (
    NotificationTemplateBaseSchema,
    NotificationTemplateCreateSchema,
    NotificationTemplateUpdateSchema,
    NotificationTemplateSchema
)

# Схеми, пов'язані зі Сповіщеннями
from .notification import (
    NotificationBaseSchema,
    NotificationCreateSchema,
    NotificationUpdateSchema,
    NotificationSchema
)

# Схеми, пов'язані зі Спробами Доставки Сповіщень
from .delivery import (
    NotificationDeliveryAttemptBaseSchema,
    NotificationDeliveryAttemptCreateSchema,
    NotificationDeliveryAttemptSchema
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
    "NotificationDeliveryAttemptSchema",
]
