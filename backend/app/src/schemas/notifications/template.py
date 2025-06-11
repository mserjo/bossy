# backend/app/src/schemas/notifications/template.py
"""
Pydantic схеми для сутності "Шаблон Сповіщення" (NotificationTemplate).

Цей модуль визначає схеми для представлення, створення та оновлення
шаблонів сповіщень, які використовуються для генерації повідомлень
різними каналами (email, SMS, in-app).
"""
from typing import Optional

from pydantic import Field
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Абсолютний імпорт базових схем для довідників
from backend.app.src.schemas.dictionaries.base_dict import (
    BaseDictionarySchema,
    DictionaryCreateSchema,
    DictionaryUpdateSchema
)


# TODO: Визначити та імпортувати Enum NotificationChannelType з core.dicts
# from backend.app.src.core.dicts import NotificationChannelType

# Заглушка для NotificationChannelType
class TempNotificationChannelType:  # TODO: Видалити після імпорту Enum
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"


TEMPLATE_SUBJECT_MAX_LENGTH = 500
TEMPLATE_TYPE_MAX_LENGTH = 50


class NotificationTemplateBaseSchema(BaseSchema):  # Не успадковує DictionaryCreateSchema напряму, щоб мати свої поля
    """
    Базова схема з полями, специфічними для шаблону сповіщення,
    використовується для Create та Update схем.
    """
    subject_template: str = Field(
        ...,
        max_length=TEMPLATE_SUBJECT_MAX_LENGTH,
        description="Шаблон теми сповіщення. Може містити плейсхолдери (наприклад, {{user_name}})."
    )
    body_template: str = Field(
        ...,
        description="Шаблон тіла сповіщення. Може містити плейсхолдери та HTML/Markdown/текст залежно від типу."
    )
    # TODO: Замінити str на NotificationChannelType та додати валідатор на основі Enum.
    template_type: str = Field(
        ...,
        max_length=TEMPLATE_TYPE_MAX_LENGTH,
        description=f"Тип/канал шаблону (наприклад, '{TempNotificationChannelType.EMAIL}', '{TempNotificationChannelType.SMS}')."
    )


class NotificationTemplateCreateSchema(DictionaryCreateSchema, NotificationTemplateBaseSchema):
    """
    Схема для створення нового шаблону сповіщення.
    Успадковує поля `name`, `code`, `description`, `state`, `notes` з `DictionaryCreateSchema`
    та додає `subject_template`, `body_template`, `template_type` з `NotificationTemplateBaseSchema`.
    """
    # name, code, description, state, notes - з DictionaryCreateSchema
    # subject_template, body_template, template_type - з NotificationTemplateBaseSchema
    pass


class NotificationTemplateUpdateSchema(DictionaryUpdateSchema, NotificationTemplateBaseSchema):
    """
    Схема для оновлення існуючого шаблону сповіщення.
    Всі поля є опціональними.
    """
    # name, code, description, state, notes - опціональні з DictionaryUpdateSchema
    # subject_template, body_template, template_type - робимо опціональними тут
    subject_template: Optional[str] = Field(None, max_length=TEMPLATE_SUBJECT_MAX_LENGTH)
    body_template: Optional[str] = None
    template_type: Optional[str] = Field(None, max_length=TEMPLATE_TYPE_MAX_LENGTH)


class NotificationTemplateSchema(BaseDictionarySchema):
    """
    Схема для представлення даних шаблону сповіщення у відповідях API.
    Успадковує `id`, `code`, `name`, `description`, `state`, `notes`, `group_id`,
    `created_at`, `updated_at`, `deleted_at` від `BaseDictionarySchema` (який успадковує `BaseMainSchema`).
    """
    subject_template: str = Field(description="Шаблон теми сповіщення.")
    body_template: str = Field(description="Шаблон тіла сповіщення.")
    # TODO: Замінити str на NotificationChannelType Enum або схему, що його представляє.
    template_type: str = Field(description="Тип/канал шаблону.")

    # model_config успадковується з BaseDictionarySchema


if __name__ == "__main__":
    # Демонстраційний блок для схем шаблонів сповіщень.
    logger.info("--- Pydantic Схеми для Шаблонів Сповіщень (NotificationTemplate) ---")
    from datetime import datetime  # Потрібно для прикладів з BaseDictionarySchema

    logger.info("\nNotificationTemplateCreateSchema (приклад для створення):")
    create_template_data = {
        "name": "Вітальний Email",  # TODO i18n
        "code": "WELCOME_EMAIL_V2",
        "description": "Шаблон для вітального email при реєстрації.",  # TODO i18n
        "subject_template": "Ласкаво просимо до {project_name}, {{user_name}}!",  # TODO i18n (плейсхолдери окремо)
        "body_template": "<h1>Привіт, {{user_name}}!</h1><p>Дякуємо за реєстрацію.</p>",
        # TODO i18n (плейсхолдери окремо)
        "template_type": TempNotificationChannelType.EMAIL,  # TODO: замінити на Enum.value
        "state": "active"
    }
    create_template_instance = NotificationTemplateCreateSchema(**create_template_data)
    logger.info(create_template_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nNotificationTemplateUpdateSchema (приклад для оновлення):")
    update_template_data = {
        "subject_template": "Ласкаво просимо до оновленого {project_name}, {{user_name}}!",  # TODO i18n
        "state": "inactive"
    }
    update_template_instance = NotificationTemplateUpdateSchema(**update_template_data)
    logger.info(update_template_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nNotificationTemplateSchema (приклад відповіді API):")
    template_response_data = {
        "id": 1,
        "code": "TASK_REMINDER_SMS",
        "name": "SMS: Нагадування про завдання",  # TODO i18n
        "description": "Надсилає SMS-нагадування про наближення терміну виконання завдання.",  # TODO i18n
        "subject_template": "Kudos: Нагадування про завдання",  # SMS не має теми, але поле може бути для уніфікації
        "body_template": "Нагадуємо: термін виконання вашого завдання '{{task_name}}' спливає {{due_date}}.",
        # TODO i18n
        "template_type": TempNotificationChannelType.SMS,  # TODO: замінити на Enum.value
        "state": "active",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    template_response_instance = NotificationTemplateSchema(**template_response_data)
    logger.info(template_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації та серіалізації даних шаблонів сповіщень.")
    logger.info("TODO: Інтегрувати Enum 'NotificationChannelType' з core.dicts для поля 'template_type'.")
