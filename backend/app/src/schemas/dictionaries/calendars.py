# backend/app/src/schemas/dictionaries/calendars.py
"""
Pydantic схеми для довідника "Постачальники Календарів".

Цей модуль визначає схеми для представлення, створення та оновлення
записів у довіднику постачальників календарів (наприклад, Google Calendar, Outlook Calendar).
"""

from typing import Optional
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Абсолютний імпорт базових схем для довідників
from backend.app.src.schemas.dictionaries.base_dict import (
    BaseDictionarySchema,
    DictionaryCreateSchema,
    DictionaryUpdateSchema
)


# from pydantic import Field

# Схема для представлення запису Постачальника Календаря (у відповідях API)
class CalendarProviderSchema(BaseDictionarySchema):
    """
    Pydantic схема для представлення запису довідника "Постачальник Календаря".
    Успадковує всі поля від `BaseDictionarySchema`.
    """
    # Специфічні поля для CalendarProviderSchema, якщо є, додаються тут.
    # Наприклад:
    # api_integration_url: Optional[AnyHttpUrl] = Field(None, description="URL для інтеграції з API календаря.")
    pass


# Схема для створення нового запису Постачальника Календаря
class CalendarProviderCreateSchema(DictionaryCreateSchema):
    """
    Pydantic схема для створення нового запису в довіднику "Постачальник Календаря".
    Успадковує всі поля від `DictionaryCreateSchema`.
    """
    # Специфічні поля для створення CalendarProvider, якщо є, додаються тут.
    pass


# Схема для оновлення існуючого запису Постачальника Календаря
class CalendarProviderUpdateSchema(DictionaryUpdateSchema):
    """
    Pydantic схема для оновлення існуючого запису в довіднику "Постачальник Календаря".
    Успадковує всі поля від `DictionaryUpdateSchema`.
    """
    # Специфічні поля для оновлення CalendarProvider, якщо є, додаються тут.
    pass


if __name__ == "__main__":
    # Демонстраційний блок для схем CalendarProvider.
    logger.info("--- Pydantic Схеми для Довідника: CalendarProvider ---")

    logger.info("\nCalendarProviderSchema (приклад для відповіді API):")
    calendar_provider_data_from_db = {
        "id": 1,
        "name": "Google Calendar",  # TODO i18n
        "code": "GOOGLE_CALENDAR",
        "description": "Інтеграція з сервісом Google Calendar.",  # TODO i18n
        "state": "active",
        "created_at": "2023-07-01T10:00:00Z",
        "updated_at": "2023-07-01T12:30:00Z",
    }
    from datetime import datetime  # Потрібно для конвертації рядків у datetime

    # from pydantic import AnyHttpUrl # Для прикладу з api_integration_url
    calendar_provider_data_from_db['created_at'] = datetime.fromisoformat(
        calendar_provider_data_from_db['created_at'].replace('Z', '+00:00'))
    calendar_provider_data_from_db['updated_at'] = datetime.fromisoformat(
        calendar_provider_data_from_db['updated_at'].replace('Z', '+00:00'))

    calendar_provider_schema_instance = CalendarProviderSchema(**calendar_provider_data_from_db)
    logger.info(calendar_provider_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nCalendarProviderCreateSchema (приклад для створення):")
    create_data = {
        "name": "Outlook Calendar",  # TODO i18n
        "code": "OUTLOOK_CALENDAR",
        "description": "Інтеграція з сервісом Outlook Calendar."  # TODO i18n
    }
    create_schema_instance = CalendarProviderCreateSchema(**create_data)
    logger.info(create_schema_instance.model_dump_json(indent=2))

    logger.info("\nCalendarProviderUpdateSchema (приклад для оновлення):")
    update_data = {
        "description": "Оновлений опис для інтеграції з Outlook Calendar.",  # TODO i18n
        "state": "beta"  # TODO i18n
    }
    update_schema_instance = CalendarProviderUpdateSchema(**update_data)
    logger.info(update_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації даних на рівні API та для серіалізації.")
