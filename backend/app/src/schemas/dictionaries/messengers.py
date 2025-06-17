# backend/app/src/schemas/dictionaries/messengers.py
"""
Pydantic схеми для довідника "Платформи Месенджерів".

Цей модуль визначає схеми для представлення, створення та оновлення
записів у довіднику платформ месенджерів (наприклад, Telegram, Viber, Slack).
"""

from typing import Optional
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)

# Абсолютний імпорт базових схем для довідників
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryBaseResponseSchema,
    DictionaryCreateSchema,
    DictionaryUpdateSchema
)


# from pydantic import Field

# Схема для представлення запису Платформи Месенджера (у відповідях API)
class MessengerPlatformResponseSchema(DictionaryBaseResponseSchema):
    """
    Pydantic схема для представлення запису довідника "Платформа Месенджера".
    Успадковує всі поля від `DictionaryBaseResponseSchema`.
    """
    # Специфічні поля для MessengerPlatformSchema, якщо є, додаються тут.
    # Наприклад:
    # supports_markdown: bool = Field(True, description="Чи підтримує платформа форматування Markdown у повідомленнях.")
    pass


# Схема для створення нового запису Платформи Месенджера
class MessengerPlatformCreateSchema(DictionaryCreateSchema):
    """
    Pydantic схема для створення нового запису в довіднику "Платформа Месенджера".
    Успадковує всі поля від `DictionaryCreateSchema`.
    """
    # Специфічні поля для створення MessengerPlatform, якщо є, додаються тут.
    pass


# Схема для оновлення існуючого запису Платформи Месенджера
class MessengerPlatformUpdateSchema(DictionaryUpdateSchema):
    """
    Pydantic схема для оновлення існуючого запису в довіднику "Платформа Месенджера".
    Успадковує всі поля від `DictionaryUpdateSchema`.
    """
    # Специфічні поля для оновлення MessengerPlatform, якщо є, додаються тут.
    pass


if __name__ == "__main__":
    # Демонстраційний блок для схем MessengerPlatform.
    logger.info("--- Pydantic Схеми для Довідника: MessengerPlatform ---")

    logger.info("\nMessengerPlatformSchema (приклад для відповіді API):")
    messenger_platform_data_from_db = {
        "id": 1,
        "name": "Telegram",  # TODO i18n
        "code": "TELEGRAM",
        "description": "Платформа для обміну повідомленнями Telegram.",  # TODO i18n
        "state": "active",
        "created_at": "2023-08-01T10:00:00Z",
        "updated_at": "2023-08-01T12:30:00Z",
    }
    from datetime import datetime  # Потрібно для конвертації рядків у datetime

    messenger_platform_data_from_db['created_at'] = datetime.fromisoformat(
        messenger_platform_data_from_db['created_at'].replace('Z', '+00:00'))
    messenger_platform_data_from_db['updated_at'] = datetime.fromisoformat(
        messenger_platform_data_from_db['updated_at'].replace('Z', '+00:00'))

    messenger_platform_schema_instance = MessengerPlatformResponseSchema(**messenger_platform_data_from_db) # Renamed
    logger.info(messenger_platform_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nMessengerPlatformCreateSchema (приклад для створення):")
    create_data = {
        "name": "Viber",  # TODO i18n
        "code": "VIBER",
        "description": "Платформа для обміну повідомленнями Viber."  # TODO i18n
    }
    create_schema_instance = MessengerPlatformCreateSchema(**create_data)
    logger.info(create_schema_instance.model_dump_json(indent=2))

    logger.info("\nMessengerPlatformUpdateSchema (приклад для оновлення):")
    update_data = {
        "description": "Оновлений опис для платформи Viber.",  # TODO i18n
        "state": "beta"  # TODO i18n
    }
    update_schema_instance = MessengerPlatformUpdateSchema(**update_data)
    logger.info(update_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації даних на рівні API та для серіалізації.")
