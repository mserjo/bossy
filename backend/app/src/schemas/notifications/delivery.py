# backend/app/src/schemas/notifications/delivery.py
"""
Pydantic схеми для сутності "Спроба Доставки Сповіщення" (NotificationDeliveryAttempt).

Цей модуль визначає схеми для:
- Базового представлення спроби доставки (`NotificationDeliveryAttemptBaseSchema`).
- Створення нового запису про спробу доставки (зазвичай виконується сервісом) (`NotificationDeliveryAttemptCreateSchema`).
- Представлення даних про спробу доставки у відповідях API (`NotificationDeliveryAttemptSchema`).
"""
from datetime import datetime
from typing import Optional

from pydantic import Field

# Абсолютний імпорт базових схем
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.config.logging import get_logger  # Імпорт логера
from backend.app.src.core.dicts import NotificationChannelType, DeliveryStatusType # Імпортовано Enums
from datetime import timedelta # Переміщено timedelta сюди
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Enums NotificationChannelType та DeliveryStatusType імпортовано вище.

# CHANNEL_MAX_LENGTH = 50 # Не потрібен для Enum
# STATUS_MAX_LENGTH = 50 # Не потрібен для Enum
EXTERNAL_ID_MAX_LENGTH = 255


class NotificationDeliveryAttemptBaseSchema(BaseSchema):
    """
    Базова схема для полів запису про спробу доставки сповіщення.
    """
    notification_id: int = Field(description="Ідентифікатор сповіщення, яке намагалися доставити.")
    channel: NotificationChannelType = Field( # Змінено на NotificationChannelType Enum
        description="Канал доставки."
    )
    status: DeliveryStatusType = Field( # Змінено на DeliveryStatusType Enum
        description="Статус спроби доставки."
    )
    error_message: Optional[str] = Field(None, description="Повідомлення про помилку, якщо доставка не вдалася.")
    external_message_id: Optional[str] = Field(
        None,
        max_length=EXTERNAL_ID_MAX_LENGTH,
        description="Зовнішній ID повідомлення від провайдера доставки (наприклад, SES Message ID, Twilio SID)."
    )
    # model_config успадковується з BaseSchema (from_attributes=True)


class NotificationDeliveryAttemptCreateSchema(NotificationDeliveryAttemptBaseSchema):
    """
    Схема для створення нового запису про спробу доставки сповіщення.
    Зазвичай використовується внутрішніми сервісами доставки.
    """
    # Успадковує всі поля від NotificationDeliveryAttemptBaseSchema.
    # `created_at` (як час спроби) буде встановлено автоматично через TimestampedMixin у відповіді.
    pass


class NotificationDeliveryAttemptSchema(NotificationDeliveryAttemptBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про спробу доставки сповіщення у відповідях API.
    Поле `created_at` (з `TimestampedSchemaMixin`) позначає час здійснення спроби.
    """
    # id, created_at, updated_at успадковані.
    # notification_id, channel, status, error_message, external_message_id успадковані.

    # Можна додати зв'язок з NotificationSchema, якщо потрібно повертати деталі сповіщення разом зі спробою,
    # але зазвичай це не потрібно, оскільки спроби є частиною об'єкта сповіщення.
    # notification: Optional[NotificationSchema] = None


if __name__ == "__main__":
    # Демонстраційний блок для схем спроб доставки сповіщень.
    logger.info("--- Pydantic Схеми для Спроб Доставки Сповіщень (NotificationDeliveryAttempt) ---")

    logger.info("\nNotificationDeliveryAttemptCreateSchema (приклад для створення):")
    create_attempt_data = {
        "notification_id": 101,
        "channel": NotificationChannelType.EMAIL, # Використовуємо Enum
        "status": DeliveryStatusType.PENDING,  # Використовуємо Enum
    }
    create_attempt_instance = NotificationDeliveryAttemptCreateSchema(**create_attempt_data)
    logger.info(create_attempt_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nNotificationDeliveryAttemptSchema (приклад відповіді API):")
    attempt_response_data = {
        "id": 1,
        "notification_id": 101,
        "channel": NotificationChannelType.EMAIL, # Використовуємо Enum
        "status": DeliveryStatusType.SENT,  # Використовуємо Enum
        "external_message_id": "ses-msg-id-xyz789",
        "created_at": datetime.now() - timedelta(seconds=30),
        "updated_at": datetime.now() - timedelta(seconds=30)
        # Може бути таким же, як created_at, якщо статус не змінювався
    }
    attempt_response_instance = NotificationDeliveryAttemptSchema(**attempt_response_data)
    logger.info(attempt_response_instance.model_dump_json(indent=2, exclude_none=True))

    # Приклад з помилкою
    attempt_failed_data = {
        "id": 2,
        "notification_id": 102,
        "channel": NotificationChannelType.SMS, # Використовуємо Enum
        "status": DeliveryStatusType.FAILED,  # Використовуємо Enum
        "error_message": "Неправильний номер телефону отримувача",  # TODO i18n
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    attempt_failed_instance = NotificationDeliveryAttemptSchema(**attempt_failed_data)
    logger.info(f"\nПриклад невдалої спроби:\n{attempt_failed_instance.model_dump_json(indent=2, exclude_none=True)}")

    logger.info("\nПримітка: Ці схеми використовуються для валідації та серіалізації даних спроб доставки.")
    # TODO Коментарі про Enum видалено, оскільки вони тепер імпортовані та використовуються.

# Потрібно для timedelta в __main__ - вже переміщено нагору
# from datetime import timedelta
