# backend/app/src/schemas/notifications/notification.py
"""
Pydantic схеми для сутності "Сповіщення" (Notification).

Цей модуль визначає схеми для:
- Базового представлення сповіщення (`NotificationBaseSchema`).
- Створення нового сповіщення (зазвичай виконується сервісом) (`NotificationCreateSchema`).
- Оновлення статусу прочитання сповіщення (`NotificationUpdateSchema`).
- Представлення даних про сповіщення у відповідях API (`NotificationSchema`).
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import Field

# Абсолютний імпорт базових схем та Enum
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.core.dicts import NotificationType as NotificationTypeEnum  # Реальний Enum
from backend.app.src.core.dicts import RelatedEntityType # Імпорт RelatedEntityType
from backend.app.src.config.logging import get_logger
from datetime import timedelta # Переміщено timedelta сюди
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)

# Імпорти для конкретних схем
from backend.app.src.schemas.auth.user import UserPublicProfileSchema
from .template import NotificationTemplateSchema # Відносний імпорт
from .delivery import NotificationDeliveryAttemptSchema # Відносний імпорт

# Placeholder assignments removed
# NotificationTemplateSchema = Any
# UserPublicProfileSchema = Any

NOTIFICATION_TITLE_MAX_LENGTH = 255
NOTIFICATION_RELATED_ENTITY_TYPE_MAX_LENGTH = 50


class NotificationBaseSchema(BaseSchema):
    """
    Базова схема для полів сповіщення.
    """
    user_id: int = Field(description=_("notification.fields.user_id.description"))
    template_id: Optional[int] = Field(None, description=_("notification.fields.template_id.description"))
    title: str = Field(
        ...,
        max_length=NOTIFICATION_TITLE_MAX_LENGTH,
        description=_("notification.fields.title.description")
    )
    message: str = Field(...,
                         description=_("notification.fields.message.description"))

    notification_type: NotificationTypeEnum = Field(
        description=_("notification.fields.notification_type.description")
    )
    related_entity_type: Optional[RelatedEntityType] = Field(
        None,
        description=_("notification.fields.related_entity_type.description"),
        examples=["task", "user_account"]
    )
    related_entity_id: Optional[int] = Field(
        None,
        description=_("notification.fields.related_entity_id.description")
    )
    data_payload: Optional[Dict[str, Any]] = Field(
        None,
        description=_("notification.fields.data_payload.description")
    )
    # model_config успадковується з BaseSchema (from_attributes=True)


class NotificationCreateSchema(NotificationBaseSchema):
    """
    Схема для створення нового сповіщення.
    Зазвичай використовується внутрішніми сервісами.
    """
    # Успадковує всі поля від NotificationBaseSchema.
    # is_read та read_at не встановлюються при створенні, вони мають значення за замовчуванням.
    pass


class NotificationUpdateSchema(BaseSchema):
    """
    Схема для оновлення статусу сповіщення (наприклад, позначка про прочитання).
    Дозволяє оновлювати лише обмежений набір полів.
    """
    is_read: Optional[bool] = Field(None, description=_("notification.update.fields.is_read.description"))
    # read_at буде встановлено сервером, якщо is_read=True


class NotificationSchema(NotificationBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про сповіщення у відповідях API.
    `created_at` з TimestampedSchemaMixin позначає час створення сповіщення.
    """
    # id, created_at, updated_at успадковані.
    # user_id, template_id, title, message, notification_type,
    # related_entity_type, related_entity_id, data_payload успадковані.

    is_read: bool = Field(description=_("notification.response.fields.is_read.description"))
    read_at: Optional[datetime] = Field(None, description=_("notification.response.fields.read_at.description"))

    user: Optional[UserPublicProfileSchema] = Field(None,
                                                    description=_("notification.response.fields.user.description"))
    template: Optional[NotificationTemplateSchema] = Field(None,
                                                           description=_("notification.response.fields.template.description"))
    delivery_attempts: List[NotificationDeliveryAttemptSchema] = Field(default_factory=list,
                                                                       description=_("notification.response.fields.delivery_attempts.description"))


if __name__ == "__main__":
    # Демонстраційний блок для схем сповіщень.
    logger.info("--- Pydantic Схеми для Сповіщень (Notification) ---")
    # from datetime import timedelta  # Вже імпортовано вище

    logger.info("\nNotificationCreateSchema (приклад для створення):")
    create_notification_data = {
        "user_id": 101,
        "title": "Ваш щотижневий звіт готовий!",  # TODO i18n
        "message": "Шановний користувачу, ваш звіт за минулий тиждень згенеровано та доступний у вашому кабінеті.",
        # TODO i18n
        "notification_type": NotificationTypeEnum.GENERAL_INFO, # Використовуємо Enum напряму
        "related_entity_type": RelatedEntityType.REPORT, # Використовуємо Enum напряму
        "related_entity_id": 789,
        "data_payload": {"report_url": "/reports/789"}
    }
    create_notification_instance = NotificationCreateSchema(**create_notification_data)
    logger.info(create_notification_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nNotificationUpdateSchema (приклад для оновлення статусу прочитання):")
    update_notification_data = {"is_read": True}
    update_notification_instance = NotificationUpdateSchema(**update_notification_data)
    logger.info(update_notification_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nNotificationSchema (приклад відповіді API):")
    notification_response_data = {
        "id": 1,
        "user_id": 101,
        "title": "Новий бейдж отримано!",  # TODO i18n
        "message": "Вітаємо! Ви отримали бейдж 'Активний Учасник'.",  # TODO i18n
        "notification_type": NotificationTypeEnum.BONUS_AWARDED.value,  # Приклад, може бути більш специфічний тип
        "is_read": False,
        "created_at": datetime.now() - timedelta(hours=1),
        "updated_at": datetime.now() - timedelta(hours=1),
        "related_entity_type": "badge",
        "related_entity_id": 5,
        # "user": {"id": 101, "username": "notify_user", "name": "Отримувач"}, # Приклад UserPublicProfileSchema
        # "template": {"id": 3, "name": "Шаблон Отримання Бейджа", "subject_template": "Вітаємо!",
        #              "created_at": str(datetime.now()), "updated_at": str(datetime.now())}, # Приклад NotificationTemplateSchema
        "delivery_attempts": [ # Приклад NotificationDeliveryAttemptSchema
            # {"id": 1, "notification_id": 1, "attempted_at": str(datetime.now() - timedelta(minutes=5)),
            #  "status": "SUCCESS", "channel": "EMAIL"},
            # {"id": 2, "notification_id": 1, "attempted_at": str(datetime.now() - timedelta(minutes=2)),
            #  "status": "PENDING", "channel": "PUSH"}
        ]
    }
    notification_response_instance = NotificationSchema(**notification_response_data)
    logger.info(notification_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми для пов'язаних об'єктів (`template`, `user`, `delivery_attempts`) тепер імпортовані.")
    logger.info("Приклади даних для цих полів у `notification_response_data` закоментовані або надані частково,")
    logger.info("оскільки потребують повної структури відповідних схем.")
    logger.info(
        f"Поле 'notification_type' використовує значення з Enum `NotificationType` (наприклад, '{NotificationTypeEnum.TASK_REMINDER.value}').")
