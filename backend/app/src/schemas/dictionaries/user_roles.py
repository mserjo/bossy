# backend/app/src/schemas/dictionaries/user_roles.py
"""
Pydantic схеми для довідника "Системні Ролі Користувачів".

Цей модуль визначає схеми для представлення, створення та оновлення
записів у довіднику системних ролей користувачів (наприклад, "superuser", "user").
"""

from typing import Optional  # Необхідно для опціональних полів в Update схемі
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _
logger = get_logger(__name__)

# Абсолютний імпорт базових схем для довідників
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryBaseResponseSchema,
    DictionaryCreateSchema,
    DictionaryUpdateSchema
)


# from pydantic import Field # Може знадобитися, якщо додаватимуться специфічні поля з валідацією

# Схема для представлення запису Системної Ролі Користувача (у відповідях API)
class UserRoleResponseSchema(DictionaryBaseResponseSchema):
    """
    Pydantic схема для представлення запису довідника "Системна Роль Користувача".
    Успадковує всі поля від `DictionaryBaseResponseSchema`.
    """
    # Якщо для системних ролей потрібні специфічні додаткові поля у відповідях API,
    # наприклад, перелік дозволів за замовчуванням для цієї ролі,
    # їх можна визначити тут.
    # default_permissions: Optional[List[str]] = Field(None, description="Список кодів дозволів за замовчуванням.")

    # model_config успадковується з DictionaryBaseResponseSchema
    pass


# Схема для створення нового запису Системної Ролі Користувача
class UserRoleCreateSchema(DictionaryCreateSchema):
    """
    Pydantic схема для створення нового запису в довіднику "Системна Роль Користувача".
    Успадковує всі поля від `DictionaryCreateSchema`.
    """
    # Тут можна додати специфічні поля для створення UserRole, якщо вони є.
    pass


# Схема для оновлення існуючого запису Системної Ролі Користувача
class UserRoleUpdateSchema(DictionaryUpdateSchema):
    """
    Pydantic схема для оновлення існуючого запису в довіднику "Системна Роль Користувача".
    Успадковує всі поля від `DictionaryUpdateSchema`.
    """
    # Тут можна додати специфічні поля для оновлення UserRole, якщо вони є.
    pass


if __name__ == "__main__":
    # Демонстраційний блок для схем UserRole.
    logger.info("--- Pydantic Схеми для Довідника: UserRole ---")

    logger.info("\nUserRoleSchema (приклад для відповіді API):")
    user_role_data_from_db = {
        "id": 1,
        "name": "Супер Адміністратор",  # TODO i18n
        "code": "SUPERUSER",
        "description": "Роль з максимальними повноваженнями в системі.",  # TODO i18n
        "state": "active",
        "created_at": "2023-02-01T10:00:00Z",
        "updated_at": "2023-02-01T12:30:00Z",
    }
    # Для from_attributes=True, очікується datetime об'єкт
    from datetime import datetime

    user_role_data_from_db['created_at'] = datetime.fromisoformat(
        user_role_data_from_db['created_at'].replace('Z', '+00:00'))
    user_role_data_from_db['updated_at'] = datetime.fromisoformat(
        user_role_data_from_db['updated_at'].replace('Z', '+00:00'))

    user_role_schema_instance = UserRoleResponseSchema(**user_role_data_from_db) # Renamed
    logger.info(user_role_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nUserRoleCreateSchema (приклад для створення):")
    create_data = {
        "name": "Менеджер Контенту",  # TODO i18n
        "code": "CONTENT_MANAGER",
        "description": "Роль для управління контентом на сайті."  # TODO i18n
    }
    create_schema_instance = UserRoleCreateSchema(**create_data)
    logger.info(create_schema_instance.model_dump_json(indent=2))

    logger.info("\nUserRoleUpdateSchema (приклад для оновлення):")
    update_data = {
        "description": "Оновлений опис для ролі Менеджера Контенту."  # TODO i18n
    }
    update_schema_instance = UserRoleUpdateSchema(**update_data)
    logger.info(update_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації даних на рівні API та для серіалізації.")
