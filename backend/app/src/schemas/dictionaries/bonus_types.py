# backend/app/src/schemas/dictionaries/bonus_types.py
"""
Pydantic схеми для довідника "Типи Бонусів".

Цей модуль визначає схеми для представлення, створення та оновлення
записів у довіднику типів бонусів (наприклад, "Нагорода", "Штраф").
"""

from typing import Optional
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Абсолютний імпорт базових схем для довідників
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryBaseResponseSchema,
    DictionaryCreateSchema,
    DictionaryUpdateSchema
)


# from pydantic import Field

# Схема для представлення запису Типу Бонусу (у відповідях API)
class BonusTypeResponseSchema(DictionaryBaseResponseSchema):
    """
    Pydantic схема для представлення запису довідника "Тип Бонусу".
    Успадковує всі поля від `DictionaryBaseResponseSchema`.
    """
    # Специфічні поля для BonusTypeSchema, якщо є, додаються тут.
    # Наприклад, чи є цей тип бонусу позитивним чи негативним за замовчуванням
    # is_positive_by_default: bool = Field(True, description="Чи є цей тип бонусу зазвичай нарахуванням.")
    pass


# Схема для створення нового запису Типу Бонусу
class BonusTypeCreateSchema(DictionaryCreateSchema):
    """
    Pydantic схема для створення нового запису в довіднику "Тип Бонусу".
    Успадковує всі поля від `DictionaryCreateSchema`.
    """
    # Специфічні поля для створення BonusType, якщо є, додаються тут.
    pass


# Схема для оновлення існуючого запису Типу Бонусу
class BonusTypeUpdateSchema(DictionaryUpdateSchema):
    """
    Pydantic схема для оновлення існуючого запису в довіднику "Тип Бонусу".
    Успадковує всі поля від `DictionaryUpdateSchema`.
    """
    # Специфічні поля для оновлення BonusType, якщо є, додаються тут.
    pass


if __name__ == "__main__":
    # Демонстраційний блок для схем BonusType.
    logger.info("--- Pydantic Схеми для Довідника: BonusType ---")

    logger.info("\nBonusTypeSchema (приклад для відповіді API):")
    bonus_type_data_from_db = {
        "id": 1,
        "name": "Бонус за активність",  # TODO i18n
        "code": "ACTIVITY_REWARD",
        "description": "Нараховується за регулярну участь у групових активностях.",  # TODO i18n
        "state": "active",
        "created_at": "2023-06-01T10:00:00Z",
        "updated_at": "2023-06-01T12:30:00Z",
    }
    from datetime import datetime  # Потрібно для конвертації рядків у datetime

    bonus_type_data_from_db['created_at'] = datetime.fromisoformat(
        bonus_type_data_from_db['created_at'].replace('Z', '+00:00'))
    bonus_type_data_from_db['updated_at'] = datetime.fromisoformat(
        bonus_type_data_from_db['updated_at'].replace('Z', '+00:00'))

    bonus_type_schema_instance = BonusTypeResponseSchema(**bonus_type_data_from_db) # Renamed
    logger.info(bonus_type_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nBonusTypeCreateSchema (приклад для створення):")
    create_data = {
        "name": "Штраф за запізнення",  # TODO i18n
        "code": "LATE_PENALTY",
        "description": "Списується за запізнення на командні зустрічі."  # TODO i18n
    }
    create_schema_instance = BonusTypeCreateSchema(**create_data)
    logger.info(create_schema_instance.model_dump_json(indent=2))

    logger.info("\nBonusTypeUpdateSchema (приклад для оновлення):")
    update_data = {
        "description": "Оновлений опис для штрафу за запізнення."  # TODO i18n
    }
    update_schema_instance = BonusTypeUpdateSchema(**update_data)
    logger.info(update_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації даних на рівні API та для серіалізації.")
