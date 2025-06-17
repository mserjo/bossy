# backend/app/src/schemas/dictionaries/user_types.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для довідника "Типи користувачів".

Цей модуль визначає схеми Pydantic для валідації даних під час створення,
оновлення та представлення записів у довіднику типів користувачів
(наприклад, "REGULAR_USER", "ADMIN_USER", "BOT_USER"). Ці типи можуть
використовуватися для класифікації користувачів та надання їм різних
базових наборів можливостей або обмежень на рівні системи.
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
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)

# from pydantic import Field # Розкоментувати, якщо будуть специфічні поля з Field атрибутами


class UserTypeResponseSchema(DictionaryBaseResponseSchema):
    """Pydantic схема для представлення запису довідника "Тип Користувача" у відповідях API.

    Успадковує всі поля від `DictionaryBaseResponseSchema`.
    Якщо для типів користувачів потрібні специфічні додаткові поля у відповідях API,
    їх можна визначити тут.
    """
    # Наприклад:
    # default_permissions_level: Optional[int] = Field(None, description="Рівень дозволів за замовчуванням для цього типу.")
    pass


class UserTypeCreateSchema(DictionaryCreateSchema):
    """Pydantic схема для створення нового запису в довіднику "Тип Користувача".

    Успадковує всі поля від `DictionaryCreateSchema`.
    """
    # Тут можна додати специфічні поля для створення UserTypeModel, якщо вони є,
    # або перевизначити поля з DictionaryCreateSchema для зміни обмежень/значень за замовчуванням.
    pass


class UserTypeUpdateSchema(DictionaryUpdateSchema):
    """Pydantic схема для оновлення існуючого запису в довіднику "Тип Користувача".

    Успадковує всі поля від `DictionaryUpdateSchema` (всі поля опціональні).
    """
    # Тут можна додати специфічні поля для оновлення UserTypeModel, якщо вони є.
    pass


if __name__ == "__main__":
    # Демонстраційний блок для схем UserTypeModel.
    logger.info("--- Pydantic Схеми для Довідника: UserTypeModel ---")

    logger.info("\nUserTypeResponseSchema (приклад для відповіді API):")
    user_type_data_from_db = {
        "id": 1, # ID тепер int
        "name": "Зареєстрований Користувач",  # TODO i18n: "Зареєстрований Користувач"
        "code": "REGULAR_USER",
        "description": "Стандартний тип для користувачів, що пройшли реєстрацію.",  # TODO i18n
        # "icon": "fas fa-user", # Видалено
        # "color": "#3498db",   # Видалено
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
        # "is_deleted": False # Видалено
    }

    user_type_response_instance = UserTypeResponseSchema(**user_type_data_from_db)
    logger.info(user_type_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nUserTypeCreateSchema (приклад для створення):")
    create_data = {
        "name": "Системний Бот",  # TODO i18n: "Системний Бот"
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
    logger.info("Вони успадковують поля та конфігурацію від базових схем довідників.")
