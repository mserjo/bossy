# backend/app/src/schemas/dictionaries/user_types.py
"""
Pydantic схеми для довідника "Типи Користувачів".

Цей модуль визначає схеми для представлення, створення та оновлення
записів у довіднику типів користувачів (наприклад, "REGULAR_USER", "BOT_USER").
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

# Схема для представлення запису Типу Користувача (у відповідях API)
class UserTypeSchema(BaseDictionarySchema):
    """
    Pydantic схема для представлення запису довідника "Тип Користувача".
    Успадковує всі поля від `BaseDictionarySchema`.
    """
    # Специфічні поля для UserTypeSchema, якщо є, додаються тут.
    pass


# Схема для створення нового запису Типу Користувача
class UserTypeCreateSchema(DictionaryCreateSchema):
    """
    Pydantic схема для створення нового запису в довіднику "Тип Користувача".
    Успадковує всі поля від `DictionaryCreateSchema`.
    """
    # Специфічні поля для створення UserType, якщо є, додаються тут.
    pass


# Схема для оновлення існуючого запису Типу Користувача
class UserTypeUpdateSchema(DictionaryUpdateSchema):
    """
    Pydantic схема для оновлення існуючого запису в довіднику "Тип Користувача".
    Успадковує всі поля від `DictionaryUpdateSchema`.
    """
    # Специфічні поля для оновлення UserType, якщо є, додаються тут.
    pass


if __name__ == "__main__":
    # Демонстраційний блок для схем UserType.
    logger.info("--- Pydantic Схеми для Довідника: UserType ---")

    logger.info("\nUserTypeSchema (приклад для відповіді API):")
    user_type_data_from_db = {
        "id": 1,
        "name": "Зареєстрований Користувач",  # TODO i18n
        "code": "REGULAR_USER",
        "description": "Стандартний тип для користувачів, що пройшли реєстрацію.",  # TODO i18n
        "state": "active",
        "created_at": "2023-03-01T10:00:00Z",
        "updated_at": "2023-03-01T12:30:00Z",
    }
    from datetime import datetime  # Потрібно для конвертації рядків у datetime

    user_type_data_from_db['created_at'] = datetime.fromisoformat(
        user_type_data_from_db['created_at'].replace('Z', '+00:00'))
    user_type_data_from_db['updated_at'] = datetime.fromisoformat(
        user_type_data_from_db['updated_at'].replace('Z', '+00:00'))

    user_type_schema_instance = UserTypeSchema(**user_type_data_from_db)
    logger.info(user_type_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nUserTypeCreateSchema (приклад для створення):")
    create_data = {
        "name": "Системний Бот",  # TODO i18n
        "code": "BOT_USER",
        "description": "Тип для автоматизованих системних облікових записів."  # TODO i18n
    }
    create_schema_instance = UserTypeCreateSchema(**create_data)
    logger.info(create_schema_instance.model_dump_json(indent=2))

    logger.info("\nUserTypeUpdateSchema (приклад для оновлення):")
    update_data = {
        "description": "Оновлений опис для типу Системний Бот."  # TODO i18n
    }
    update_schema_instance = UserTypeUpdateSchema(**update_data)
    logger.info(update_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації даних на рівні API та для серіалізації.")
