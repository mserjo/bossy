# backend/app/src/schemas/dictionaries/statuses.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для довідника "Статуси".

Цей модуль визначає схеми Pydantic для валідації даних під час створення,
оновлення та представлення записів у довіднику статусів (`StatusModel`).
Довідник статусів може використовуватися для різних сутностей в системі,
наприклад, для завдань, користувачів, груп тощо, якщо для них не передбачено
окремих Enum-станів або потрібні статуси, керовані через БД.
"""

from typing import Optional
from datetime import datetime # Для прикладу в __main__
import uuid # Для прикладу в __main__

# Абсолютний імпорт базових схем для довідників
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryCreateSchema,
    DictionaryResponseSchema,
    DictionaryUpdateSchema
)
# Імпорт централізованого логера
from backend.app.src.config import logger

# from pydantic import Field # Розкоментувати, якщо будуть специфічні поля з Field атрибутами


class StatusResponseSchema(DictionaryResponseSchema):
    """Pydantic схема для представлення запису довідника "Статус" у відповідях API.

    Успадковує всі поля від `DictionaryResponseSchema` (який, у свою чергу,
    включає поля з `DictionaryBaseSchema`, `IDSchema`, `TimestampSchema`, `SoftDeleteSchema`).
    Якщо для статусів потрібні специфічні додаткові поля у відповідях API,
    їх можна визначити тут.
    """
    # Наприклад, якщо б StatusModel мав унікальне поле:
    # is_system_status: bool = Field(description="Чи є цей статус системним (не можна видалити).")

    # model_config успадковується з DictionaryResponseSchema -> ... -> BaseSchema
    pass


class StatusCreateSchema(DictionaryCreateSchema):
    """Pydantic схема для створення нового запису в довіднику "Статус".

    Успадковує всі поля від `DictionaryCreateSchema` (name, code, description,
    icon, color). `state_id`, `group_id`, `notes` також можуть бути успадковані,
    якщо вони визначені в `DictionaryBaseSchema` або `DictionaryCreateSchema` в `base_dict.py`.
    """
    # Тут можна перевизначити поля з DictionaryCreateSchema, якщо потрібні інші
    # обмеження або значення за замовчуванням саме для Статусів.
    # Або додати нові поля, специфічні для створення Статусу.
    pass


class StatusUpdateSchema(DictionaryUpdateSchema):
    """Pydantic схема для оновлення існуючого запису в довіднику "Статус".

    Успадковує всі поля від `DictionaryUpdateSchema` (всі поля опціональні).
    """
    # Тут можна перевизначити поля з DictionaryUpdateSchema або додати нові,
    # специфічні для оновлення Статусу.
    pass


if __name__ == "__main__":
    # Демонстраційний блок для схем Статусів.
    logger.info("--- Pydantic Схеми для Довідника: StatusModel ---")

    logger.info("\nStatusResponseSchema (приклад для відповіді API):")
    status_data_from_db = {
        "id": uuid.uuid4(), # ID тепер UUID
        "name": "Активний", # TODO i18n: "Активний"
        "code": "ACTIVE",
        "description": "Запис активний і використовується.", # TODO i18n
        "icon": "fas fa-check",
        "color": "#00FF00",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_deleted": False
        # state_id, group_id, notes, deleted_at - опціональні або можуть бути None
    }

    status_response_instance = StatusResponseSchema(**status_data_from_db)
    logger.info(status_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nStatusCreateSchema (приклад для створення):")
    create_data = {
        "name": "Новий Статус", # TODO i18n: "Новий Статус"
        "code": "NEW_STATUS_01",
        "description": "Опис для нового статусу, що створюється." # TODO i18n
    }
    create_schema_instance = StatusCreateSchema(**create_data)
    logger.info(create_schema_instance.model_dump_json(indent=2))

    # Перевірка валідації (приклад)
    try:
        # Відсутнє обов'язкове поле 'name' та 'code'
        invalid_create_data = {"description": "Неповні дані"} # TODO i18n: "Неповні дані"
        StatusCreateSchema(**invalid_create_data)
    except Exception as e:
        logger.info("Помилка валідації StatusCreateSchema (очікувано): %s", e)

    logger.info("\nStatusUpdateSchema (приклад для оновлення):")
    update_data = {
        "description": "Оновлений опис для існуючого статусу.", # TODO i18n
        "color": "#FFA500"
        # "state_id": 2 # Наприклад, ID статусу "застарілий"
    }
    update_schema_instance = StatusUpdateSchema(**update_data)
    logger.info(update_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації даних на рівні API та для серіалізації.")
    logger.info("Вони успадковують поля та конфігурацію від базових схем довідників.")
