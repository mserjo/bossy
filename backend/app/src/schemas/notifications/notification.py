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
from typing import Optional, List, Dict, Any  # Any для тимчасових полів

from pydantic import Field

# Абсолютний імпорт базових схем та Enum
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.core.dicts import NotificationType as NotificationTypeEnum  # Реальний Enum
from backend.app.src.core.dicts import RelatedEntityType # Імпорт RelatedEntityType
from backend.app.src.config.logging import get_logger  # Імпорт логера
from datetime import timedelta # Переміщено timedelta сюди
# Отримання логера для цього модуля
logger = get_logger(__name__)

# TODO: Замінити Any на конкретні схеми, коли вони будуть доступні/рефакторені.
# from backend.app.src.schemas.notifications.template import NotificationTemplateSchema
# from backend.app.src.schemas.auth.user import UserPublicProfileSchema
NotificationTemplateSchema = Any  # Тимчасовий заповнювач
UserPublicProfileSchema = Any  # Тимчасовий заповнювач

NOTIFICATION_TITLE_MAX_LENGTH = 255
NOTIFICATION_RELATED_ENTITY_TYPE_MAX_LENGTH = 50


class NotificationBaseSchema(BaseSchema):
    """
    Базова схема для полів сповіщення.
    """
    user_id: int = Field(description="Ідентифікатор користувача-отримувача сповіщення.")
    template_id: Optional[int] = Field(None, description="ID шаблону, на основі якого створено сповіщення (якщо є).")
    title: str = Field(
        ...,
        max_length=NOTIFICATION_TITLE_MAX_LENGTH,
        description="Заголовок сповіщення."
    )
    message: str = Field(...,
                         description="Тіло сповіщення (вже відрендерений текст).")  # `Text` з моделі тут просто `str`

    notification_type: NotificationTypeEnum = Field( # Змінено на NotificationTypeEnum
        description="Тип сповіщення." # Використовує значення з core.dicts.NotificationType
    )
    related_entity_type: Optional[RelatedEntityType] = Field( # Змінено на RelatedEntityType
        None,
        # max_length більше не потрібен для Enum
        description="Тип пов'язаної сутності.", # Використовує значення з core.dicts.RelatedEntityType
        examples=["task", "user_account"]
    )
    related_entity_id: Optional[int] = Field(
        None,
        description="ID пов'язаної сутності."
    )
    data_payload: Optional[Dict[str, Any]] = Field(  # Для додаткових структурованих даних
        None,
        description="Додаткові структуровані дані для сповіщення (наприклад, для побудови посилань на клієнті)."
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
    is_read: Optional[bool] = Field(None, description="Новий статус прочитання сповіщення.")
    # read_at буде встановлено сервером, якщо is_read=True


class NotificationSchema(NotificationBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про сповіщення у відповідях API.
    `created_at` з TimestampedSchemaMixin позначає час створення сповіщення.
    """
    # id, created_at, updated_at успадковані.
    # user_id, template_id, title, message, notification_type,
    # related_entity_type, related_entity_id, data_payload успадковані.

    is_read: bool = Field(description="Статус прочитання сповіщення (True, якщо прочитано).")
    read_at: Optional[datetime] = Field(None, description="Час, коли сповіщення було позначено як прочитане.")

    # TODO: Замінити Any на відповідні схеми.
    user: Optional[UserPublicProfileSchema] = Field(None,
                                                    description="Інформація про користувача-отримувача (зазвичай не включається, оскільки запит іде від імені цього користувача).")
    template: Optional[NotificationTemplateSchema] = Field(None,
                                                           description="Інформація про використаний шаблон сповіщення (якщо був).")
    # delivery_attempts: Optional[List[Any]] = Field(default_factory=list) # TODO: Додати схему NotificationDeliveryAttemptSchema


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
        # "template": {"id": 3, "name": "Шаблон Отримання Бейджа"}, # Приклад NotificationTemplateSchema
    }
    notification_response_instance = NotificationSchema(**notification_response_data)
    logger.info(notification_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми для пов'язаних об'єктів (`template`, `user`) наразі є заповнювачами (Any).")
    logger.info("Їх потрібно буде імпортувати після їх рефакторингу/визначення.")
    logger.info(
        f"Поле 'notification_type' використовує значення з Enum `NotificationType` (наприклад, '{NotificationTypeEnum.TASK_REMINDER.value}').")
    # logger.info("TODO: Додати валідатор для `notification_type` на основі Enum.") # Валідатор не потрібен для Enum
