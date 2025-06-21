# backend/app/src/schemas/dictionaries/calendars.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для довідника "Провайдери Календарів".

Цей модуль визначає схеми Pydantic для валідації даних під час створення,
оновлення та представлення записів у довіднику провайдерів календарів
(наприклад, Google Calendar, Outlook Calendar, Apple iCloud Calendar).
Довідник зберігає інформацію про назву провайдера, його код, опис,
а також специфічні налаштування для інтеграції.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone # timezone для прикладу в __main__
from pydantic import Field

# Абсолютний імпорт базових схем для довідників
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryCreateSchema,
    DictionaryCreateSchema,
    DictionaryBaseResponseSchema,
    DictionaryUpdateSchema
)
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _
logger = get_logger(__name__)


class CalendarProviderResponseSchema(DictionaryBaseResponseSchema):
    """Pydantic схема для представлення запису довідника "Провайдер Календаря" у відповідях API.

    Успадковує всі поля від `DictionaryBaseResponseSchema`.
    Додає специфічні поля для провайдерів календарів.
    """
    is_active: bool = Field(..., description=_("dictionaries.calendars.fields.is_active.description"))
    credentials_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description=_("dictionaries.calendars.fields.credentials_schema.description")
    )
    sync_frequency_minutes: Optional[int] = Field(
        default=None,
        description=_("dictionaries.calendars.fields.sync_frequency_minutes.description")
    )
    # model_config успадковується


class CalendarProviderCreateSchema(DictionaryCreateSchema):
    """Pydantic схема для створення нового запису в довіднику "Провайдер Календаря".

    Успадковує поля від `DictionaryCreateSchema` (name, code, description, icon, color).
    Додає специфічні поля для провайдерів календарів.
    """
    is_active: bool = Field(default=True, description=_("dictionaries.calendars.fields.is_active.description")) # Reusing base key, _create can be added if specific text is needed
    credentials_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description=_("dictionaries.calendars.fields.credentials_schema.description_create")
    )
    sync_frequency_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        description=_("dictionaries.calendars.fields.sync_frequency_minutes.description_create")
    )


class CalendarProviderUpdateSchema(DictionaryUpdateSchema):
    """Pydantic схема для оновлення існуючого запису в довіднику "Провайдер Календаря".

    Успадковує поля від `DictionaryUpdateSchema` (всі поля з `DictionaryBaseSchema` опціональні).
    Додає опціональні версії специфічних полів для провайдерів календарів.
    """
    is_active: Optional[bool] = Field(default=None, description=_("dictionaries.calendars.fields.is_active.description_update"))
    credentials_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description=_("dictionaries.calendars.fields.credentials_schema.description_update")
    )
    sync_frequency_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        description=_("dictionaries.calendars.fields.sync_frequency_minutes.description_update")
    )


if __name__ == "__main__":
    # Демонстраційний блок для схем CalendarProviderModel.
    logger.info("--- Pydantic Схеми для Довідника: CalendarProviderModel ---")

    logger.info("\nCalendarProviderResponseSchema (приклад для відповіді API):")
    cp_response_data = {
        "id": 1, # id тепер int
        "name": "Google Calendar",  # TODO i18n: "Google Calendar"
        "code": "GOOGLE_CALENDAR",
        "description": "Інтеграція з сервісом Google Calendar.",  # TODO i18n
        # "icon": "fab fa-google", # Видалено
        # "color": "#4285F4",    # Видалено
        "is_active": True,
        "credentials_schema": {"type": "oauth2", "scopes": ["calendar.readonly"]},
        "sync_frequency_minutes": 60,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
        # "is_deleted": False # Видалено
    }
    cp_response_instance = CalendarProviderResponseSchema(**cp_response_data)
    logger.info(cp_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nCalendarProviderCreateSchema (приклад для створення):")
    cp_create_data = {
        "name": "Outlook Calendar",  # TODO i18n: "Outlook Calendar"
        "code": "OUTLOOK_CALENDAR",
        "description": "Інтеграція з сервісом Outlook Calendar.",  # TODO i18n
        "is_active": True,
        "sync_frequency_minutes": 120
    }
    cp_create_instance = CalendarProviderCreateSchema(**cp_create_data)
    logger.info(cp_create_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nCalendarProviderUpdateSchema (приклад для оновлення):")
    cp_update_data = {
        "description": "Оновлений опис для інтеграції з Outlook Calendar.",  # TODO i18n
        "is_active": False,
        "sync_frequency_minutes": 30
    }
    cp_update_instance = CalendarProviderUpdateSchema(**cp_update_data)
    logger.info(cp_update_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації даних на рівні API та для серіалізації.")
    logger.info("Вони успадковують поля та конфігурацію від базових схем довідників та додають специфічні поля.")
