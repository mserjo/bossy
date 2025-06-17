# backend/app/src/schemas/dictionaries/group_types.py
"""
Pydantic схеми для довідника "Типи Груп".

Цей модуль визначає схеми для представлення, створення та оновлення
записів у довіднику типів груп (наприклад, "Сім'я", "Відділ").
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

# Схема для представлення запису Типу Групи (у відповідях API)
class GroupTypeResponseSchema(DictionaryBaseResponseSchema):
    """
    Pydantic схема для представлення запису довідника "Тип Групи".
    Успадковує всі поля від `DictionaryBaseResponseSchema`.
    """
    # Специфічні поля для GroupTypeSchema, якщо є, додаються тут.
    pass


# Схема для створення нового запису Типу Групи
class GroupTypeCreateSchema(DictionaryCreateSchema):
    """
    Pydantic схема для створення нового запису в довіднику "Тип Групи".
    Успадковує всі поля від `DictionaryCreateSchema`.
    """
    # Специфічні поля для створення GroupType, якщо є, додаються тут.
    pass


# Схема для оновлення існуючого запису Типу Групи
class GroupTypeUpdateSchema(DictionaryUpdateSchema):
    """
    Pydantic схема для оновлення існуючого запису в довіднику "Тип Групи".
    Успадковує всі поля від `DictionaryUpdateSchema`.
    """
    # Специфічні поля для оновлення GroupType, якщо є, додаються тут.
    pass


if __name__ == "__main__":
    # Демонстраційний блок для схем GroupType.
    logger.info("--- Pydantic Схеми для Довідника: GroupType ---")

    logger.info("\nGroupTypeSchema (приклад для відповіді API):")
    group_type_data_from_db = {
        "id": 1,
        "name": "Команда Розробки",  # TODO i18n
        "code": "DEV_TEAM",
        "description": "Тип групи для команд розробників програмного забезпечення.",  # TODO i18n
        "state": "active",
        "created_at": "2023-04-01T10:00:00Z",
        "updated_at": "2023-04-01T12:30:00Z",
    }
    from datetime import datetime  # Потрібно для конвертації рядків у datetime

    group_type_data_from_db['created_at'] = datetime.fromisoformat(
        group_type_data_from_db['created_at'].replace('Z', '+00:00'))
    group_type_data_from_db['updated_at'] = datetime.fromisoformat(
        group_type_data_from_db['updated_at'].replace('Z', '+00:00'))

    group_type_schema_instance = GroupTypeResponseSchema(**group_type_data_from_db) # Renamed
    logger.info(group_type_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nGroupTypeCreateSchema (приклад для створення):")
    create_data = {
        "name": "Сім'я",  # TODO i18n
        "code": "FAMILY",
        "description": "Група для членів сім'ї."  # TODO i18n
    }
    create_schema_instance = GroupTypeCreateSchema(**create_data)
    logger.info(create_schema_instance.model_dump_json(indent=2))

    logger.info("\nGroupTypeUpdateSchema (приклад для оновлення):")
    update_data = {
        "description": "Оновлений опис для типу групи Сім'я."  # TODO i18n
    }
    update_schema_instance = GroupTypeUpdateSchema(**update_data)
    logger.info(update_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації даних на рівні API та для серіалізації.")
