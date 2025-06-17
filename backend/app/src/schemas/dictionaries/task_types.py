# backend/app/src/schemas/dictionaries/task_types.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для довідника "Типи Завдань".

Цей модуль визначає схеми Pydantic для валідації даних під час створення,
оновлення та представлення записів у довіднику типів завдань
(наприклад, "Звичайне завдання", "Складне завдання", "Подія", "Штраф").
Ці типи використовуються для класифікації завдань та подій в системі.
"""

from typing import Optional
from datetime import datetime, timezone # timezone для прикладу в __main__

# Абсолютний імпорт базових схем для довідників
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryCreateSchema,
    DictionaryBaseResponseSchema,
    DictionaryUpdateSchema
)
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# from pydantic import Field # Розкоментувати, якщо будуть специфічні поля з Field атрибутами


class TaskTypeResponseSchema(DictionaryBaseResponseSchema):
    """Pydantic схема для представлення запису довідника "Тип Завдання" у відповідях API.

    Успадковує всі поля від `DictionaryBaseResponseSchema`.
    Якщо для типів завдань потрібні специфічні додаткові поля у відповідях API,
    їх можна визначити тут.
    """
    # Наприклад:
    # default_priority: Optional[int] = Field(None, description="Пріоритет за замовчуванням для цього типу завдання.")
    pass


class TaskTypeCreateSchema(DictionaryCreateSchema):
    """Pydantic схема для створення нового запису в довіднику "Тип Завдання".

    Успадковує всі поля від `DictionaryCreateSchema`.
    """
    # Тут можна додати специфічні поля для створення TaskTypeModel, якщо вони є.
    pass


class TaskTypeUpdateSchema(DictionaryUpdateSchema):
    """Pydantic схема для оновлення існуючого запису в довіднику "Тип Завдання".

    Успадковує всі поля від `DictionaryUpdateSchema` (всі поля опціональні).
    """
    # Тут можна додати специфічні поля для оновлення TaskTypeModel, якщо вони є.
    pass


if __name__ == "__main__":
    # Демонстраційний блок для схем TaskTypeModel.
    logger.info("--- Pydantic Схеми для Довідника: TaskTypeModel ---")

    logger.info("\nTaskTypeResponseSchema (приклад для відповіді API):")
    task_type_data_from_db = {
        "id": 1, # ID тепер int
        "name": "Термінове Завдання",  # TODO i18n: "Термінове Завдання"
        "code": "URGENT_TASK",
        "description": "Тип для завдань з високим пріоритетом.",  # TODO i18n
        # "icon": "fas fa-exclamation-triangle", # Видалено
        # "color": "#FF0000",                   # Видалено
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
        # "is_deleted": False                 # Видалено
    }

    task_type_response_instance = TaskTypeResponseSchema(**task_type_data_from_db)
    logger.info(task_type_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nTaskTypeCreateSchema (приклад для створення):")
    create_data = {
        "name": "Подія",  # TODO i18n: "Подія"
        "code": "EVENT",
        "description": "Тип для відстеження подій, а не завдань з конкретним результатом."  # TODO i18n
    }
    create_schema_instance = TaskTypeCreateSchema(**create_data)
    logger.info(create_schema_instance.model_dump_json(indent=2))

    logger.info("\nTaskTypeUpdateSchema (приклад для оновлення):")
    update_data = {
        "description": "Оновлений опис для типу 'Подія'."  # TODO i18n
    }
    update_schema_instance = TaskTypeUpdateSchema(**update_data)
    logger.info(update_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації даних на рівні API та для серіалізації.")
    logger.info("Вони успадковують поля та конфігурацію від базових схем довідників.")
