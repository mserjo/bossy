# backend/app/src/schemas/dictionaries/statuses.py
"""
Pydantic схеми для довідника "Статуси".

Цей модуль визначає схеми для представлення, створення та оновлення
записів у довіднику статусів.
"""

from typing import Optional  # Необхідно для опціональних полів в Update схемі
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Абсолютний імпорт базових схем для довідників
from backend.app.src.schemas.dictionaries.base_dict import (
    BaseDictionarySchema,
    DictionaryCreateSchema,
    DictionaryUpdateSchema
)


# from pydantic import Field # Може знадобитися, якщо додаватимуться специфічні поля з валідацією

# Схема для представлення запису Статусу (наприклад, у відповідях API)
class StatusSchema(BaseDictionarySchema):
    """
    Pydantic схема для представлення запису довідника "Статус".
    Успадковує всі поля від `BaseDictionarySchema`.
    """
    # Якщо для статусів потрібні специфічні додаткові поля у відповідях API,
    # їх можна визначити тут. Наприклад:
    # is_final_status: bool = Field(description="Чи є цей статус кінцевим (не можна змінити далі).")

    # model_config успадковується з BaseDictionarySchema -> BaseMainSchema -> BaseSchema
    pass


# Схема для створення нового запису Статусу
class StatusCreateSchema(DictionaryCreateSchema):
    """
    Pydantic схема для створення нового запису в довіднику "Статус".
    Успадковує всі поля від `DictionaryCreateSchema` (name, code, description, state, notes).
    """
    # Тут можна перевизначити поля з DictionaryCreateSchema, якщо потрібні інші
    # обмеження або значення за замовчуванням саме для Статусів.
    # Або додати нові поля, специфічні для створення Статусу.
    pass


# Схема для оновлення існуючого запису Статусу
class StatusUpdateSchema(DictionaryUpdateSchema):
    """
    Pydantic схема для оновлення існуючого запису в довіднику "Статус".
    Успадковує всі поля від `DictionaryUpdateSchema` (всі поля опціональні).
    """
    # Тут можна перевизначити поля з DictionaryUpdateSchema або додати нові,
    # специфічні для оновлення Статусу.
    pass


if __name__ == "__main__":
    # Демонстраційний блок для схем Статусів.
    logger.info("--- Pydantic Схеми для Довідника: Status ---")

    logger.info("\nStatusSchema (приклад для відповіді API):")
    status_data_from_db = {
        "id": 1,
        "name": "Активний",
        "code": "ACTIVE",
        "description": "Запис активний і використовується.",
        "state": "enabled",
        "created_at": "2023-01-01T10:00:00Z",  # У реальності це буде datetime об'єкт
        "updated_at": "2023-01-05T12:30:00Z",
        # "is_final_status": False # Якщо б таке поле було додано
    }
    # Для from_attributes=True, очікується datetime об'єкт, а не рядок
    status_data_from_db['created_at'] = datetime.fromisoformat(status_data_from_db['created_at'].replace('Z', '+00:00'))
    status_data_from_db['updated_at'] = datetime.fromisoformat(status_data_from_db['updated_at'].replace('Z', '+00:00'))

    status_schema_instance = StatusSchema(**status_data_from_db)
    logger.info(status_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nStatusCreateSchema (приклад для створення):")
    create_data = {
        "name": "Новий Статус",
        "code": "NEW_STATUS_01",
        "description": "Опис для нового статусу, що створюється."
    }
    create_schema_instance = StatusCreateSchema(**create_data)
    logger.info(create_schema_instance.model_dump_json(indent=2))
    # Перевірка валідації (приклад)
    try:
        invalid_create_data = {"code": "INVALID"}  # Відсутнє обов'язкове поле 'name'
        StatusCreateSchema(**invalid_create_data)
    except Exception as e:
        logger.info(f"Помилка валідації StatusCreateSchema (очікувано): {e}")

    logger.info("\nStatusUpdateSchema (приклад для оновлення):")
    update_data = {
        "description": "Оновлений опис для існуючого статусу.",
        "state": "deprecated"
    }
    update_schema_instance = StatusUpdateSchema(**update_data)
    logger.info(update_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації даних на рівні API та для серіалізації.")

# Необхідно додати datetime для прикладу в __main__
from datetime import datetime
