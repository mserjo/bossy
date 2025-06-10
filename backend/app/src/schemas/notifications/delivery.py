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


# TODO: Визначити та імпортувати Enums NotificationChannelType та DeliveryStatusType з core.dicts.
# from backend.app.src.core.dicts import NotificationChannelType, DeliveryStatusType

# Заглушки для Enums, поки вони не визначені в core.dicts
class TempNotificationChannelType:  # TODO: Видалити
    EMAIL = "email"
    SMS = "sms"


class TempDeliveryStatusType:  # TODO: Видалити
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


CHANNEL_MAX_LENGTH = 50
STATUS_MAX_LENGTH = 50
EXTERNAL_ID_MAX_LENGTH = 255


class NotificationDeliveryAttemptBaseSchema(BaseSchema):
    """
    Базова схема для полів запису про спробу доставки сповіщення.
    """
    notification_id: int = Field(description="Ідентифікатор сповіщення, яке намагалися доставити.")
    # TODO: Замінити str на NotificationChannelType та додати валідатор.
    channel: str = Field(
        max_length=CHANNEL_MAX_LENGTH,
        description=f"Канал доставки (наприклад, '{TempNotificationChannelType.EMAIL}', '{TempNotificationChannelType.SMS}')."
    )
    # TODO: Замінити str на DeliveryStatusType та додати валідатор.
    status: str = Field(
        max_length=STATUS_MAX_LENGTH,
        description=f"Статус спроби доставки (наприклад, '{TempDeliveryStatusType.PENDING}', '{TempDeliveryStatusType.SENT}', '{TempDeliveryStatusType.FAILED}')."
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
    print("--- Pydantic Схеми для Спроб Доставки Сповіщень (NotificationDeliveryAttempt) ---")

    print("\nNotificationDeliveryAttemptCreateSchema (приклад для створення):")
    create_attempt_data = {
        "notification_id": 101,
        "channel": TempNotificationChannelType.EMAIL,  # TODO: Замінити на Enum.value
        "status": TempDeliveryStatusType.PENDING,  # TODO: Замінити на Enum.value
    }
    create_attempt_instance = NotificationDeliveryAttemptCreateSchema(**create_attempt_data)
    print(create_attempt_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nNotificationDeliveryAttemptSchema (приклад відповіді API):")
    attempt_response_data = {
        "id": 1,
        "notification_id": 101,
        "channel": TempNotificationChannelType.EMAIL,  # TODO: Замінити на Enum.value
        "status": TempDeliveryStatusType.SENT,  # TODO: Замінити на Enum.value
        "external_message_id": "ses-msg-id-xyz789",
        "created_at": datetime.now() - timedelta(seconds=30),
        "updated_at": datetime.now() - timedelta(seconds=30)
        # Може бути таким же, як created_at, якщо статус не змінювався
    }
    attempt_response_instance = NotificationDeliveryAttemptSchema(**attempt_response_data)
    print(attempt_response_instance.model_dump_json(indent=2, exclude_none=True))

    # Приклад з помилкою
    attempt_failed_data = {
        "id": 2,
        "notification_id": 102,
        "channel": TempNotificationChannelType.SMS,  # TODO: Замінити на Enum.value
        "status": TempDeliveryStatusType.FAILED,  # TODO: Замінити на Enum.value
        "error_message": "Неправильний номер телефону отримувача",  # TODO i18n
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    attempt_failed_instance = NotificationDeliveryAttemptSchema(**attempt_failed_data)
    print(f"\nПриклад невдалої спроби:\n{attempt_failed_instance.model_dump_json(indent=2, exclude_none=True)}")

    print("\nПримітка: Ці схеми використовуються для валідації та серіалізації даних спроб доставки.")
    print(
        "TODO: Інтегрувати Enum 'NotificationChannelType' та 'DeliveryStatusType' з core.dicts для полів 'channel' та 'status'.")

# Потрібно для timedelta в __main__
from datetime import timedelta
