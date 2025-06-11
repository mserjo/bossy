# backend/app/src/schemas/dictionaries/task_types.py
"""
Pydantic схеми для довідника "Типи Завдань".

Цей модуль визначає схеми для представлення, створення та оновлення
записів у довіднику типів завдань (наприклад, "Звичайне завдання", "Подія").
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

# Схема для представлення запису Типу Завдання (у відповідях API)
class TaskTypeSchema(BaseDictionarySchema):
    """
    Pydantic схема для представлення запису довідника "Тип Завдання".
    Успадковує всі поля від `BaseDictionarySchema`.
    """
    # Специфічні поля для TaskTypeSchema, якщо є, додаються тут.
    pass


# Схема для створення нового запису Типу Завдання
class TaskTypeCreateSchema(DictionaryCreateSchema):
    """
    Pydantic схема для створення нового запису в довіднику "Тип Завдання".
    Успадковує всі поля від `DictionaryCreateSchema`.
    """
    # Специфічні поля для створення TaskType, якщо є, додаються тут.
    pass


# Схема для оновлення існуючого запису Типу Завдання
class TaskTypeUpdateSchema(DictionaryUpdateSchema):
    """
    Pydantic схема для оновлення існуючого запису в довіднику "Тип Завдання".
    Успадковує всі поля від `DictionaryUpdateSchema`.
    """
    # Специфічні поля для оновлення TaskType, якщо є, додаються тут.
    pass


if __name__ == "__main__":
    # Демонстраційний блок для схем TaskType.
    logger.info("--- Pydantic Схеми для Довідника: TaskType ---")

    logger.info("\nTaskTypeSchema (приклад для відповіді API):")
    task_type_data_from_db = {
        "id": 1,
        "name": "Термінове Завдання",  # TODO i18n
        "code": "URGENT_TASK",
        "description": "Тип для завдань з високим пріоритетом.",  # TODO i18n
        "state": "active",
        "created_at": "2023-05-01T10:00:00Z",
        "updated_at": "2023-05-01T12:30:00Z",
    }
    from datetime import datetime  # Потрібно для конвертації рядків у datetime

    task_type_data_from_db['created_at'] = datetime.fromisoformat(
        task_type_data_from_db['created_at'].replace('Z', '+00:00'))
    task_type_data_from_db['updated_at'] = datetime.fromisoformat(
        task_type_data_from_db['updated_at'].replace('Z', '+00:00'))

    task_type_schema_instance = TaskTypeSchema(**task_type_data_from_db)
    logger.info(task_type_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nTaskTypeCreateSchema (приклад для створення):")
    create_data = {
        "name": "Подія",  # TODO i18n
        "code": "EVENT",
        "description": "Тип для відстеження подій."  # TODO i18n
    }
    create_schema_instance = TaskTypeCreateSchema(**create_data)
    logger.info(create_schema_instance.model_dump_json(indent=2))

    logger.info("\nTaskTypeUpdateSchema (приклад для оновлення):")
    update_data = {
        "description": "Оновлений опис для типу Подія."  # TODO i18n
    }
    update_schema_instance = TaskTypeUpdateSchema(**update_data)
    logger.info(update_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації даних на рівні API та для серіалізації.")
