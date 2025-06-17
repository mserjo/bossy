# backend/app/src/schemas/gamification/level.py
"""
Pydantic схеми для сутності "Рівень" (Level) в системі гейміфікації.

Цей модуль визначає схеми для:
- Створення нового рівня (`LevelCreateSchema`).
- Оновлення існуючого рівня (`LevelUpdateSchema`).
- Представлення даних про рівень у відповідях API (`LevelSchema`).
"""
from datetime import datetime  # Потрібен для TimestampedSchemaMixin через BaseMainSchema
from typing import Optional, Any  # Any для тимчасових полів

from pydantic import Field, AnyHttpUrl

# Абсолютний імпорт базових схем
from backend.app.src.schemas.base import BaseSchema, BaseMainSchema
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)

# Імпорт для конкретної схеми
from backend.app.src.schemas.groups.group import GroupSchema

# Placeholder GroupBriefSchema = Any removed

LEVEL_NAME_MAX_LENGTH = 255
LEVEL_ICON_URL_MAX_LENGTH = 512


class LevelBaseSchema(BaseSchema):
    """
    Базова схема для полів рівня, спільних для створення та оновлення.
    """
    name: str = Field(
        ...,
        max_length=LEVEL_NAME_MAX_LENGTH,
        description=_("gamification.level.fields.name.description"),
        examples=["Новачок", "Досвідчений Гравець"]
    )
    description: Optional[str] = Field(
        None,
        description=_("gamification.level.fields.description.description")
    )
    required_points: int = Field(
        ...,
        ge=0,
        description=_("gamification.level.fields.required_points.description")
    )
    level_number: Optional[int] = Field(
        None,
        ge=0,
        description=_("gamification.level.fields.level_number.description")
    )
    icon_url: Optional[AnyHttpUrl] = Field(
        None,
        description=_("gamification.level.fields.icon_url.description")
    )
    group_id: Optional[int] = Field(
        None,
        description=_("gamification.level.fields.group_id.description")
    )
    state: Optional[str] = Field(
        None,
        max_length=50,
        description=_("gamification.level.fields.state.description"),
        examples=["active"]
    )
    notes: Optional[str] = Field(
        None,
        description=_("gamification.level.fields.notes.description")
    )


class LevelCreateSchema(LevelBaseSchema):
    """
    Схема для створення нового рівня гейміфікації.
    Успадковує всі поля від `LevelBaseSchema`.
    """
    pass


class LevelUpdateSchema(LevelBaseSchema):
    """
    Схема для оновлення існуючого рівня гейміфікації.
    Всі поля, успадковані з `LevelBaseSchema`, стають опціональними.
    """
    name: Optional[str] = Field(None, max_length=LEVEL_NAME_MAX_LENGTH)
    description: Optional[str] = Field(None, description=_("gamification.level.fields.description.description")) # Reusing base
    required_points: Optional[int] = Field(None, ge=0, description=_("gamification.level.fields.required_points.description")) # Reusing base
    level_number: Optional[int] = Field(None, ge=0, description=_("gamification.level.fields.level_number.description")) # Reusing base
    icon_url: Optional[AnyHttpUrl] = Field(None, description=_("gamification.level.fields.icon_url.description")) # Reusing base
    group_id: Optional[int] = Field(None,
                                    description=_("gamification.level.fields.group_id.description")) # Reusing base, specific update description can be added if needed
    state: Optional[str] = Field(None, max_length=50, description=_("gamification.level.fields.state.description")) # Reusing base
    notes: Optional[str] = Field(None, description=_("gamification.level.fields.notes.description")) # Reusing base


class LevelSchema(BaseMainSchema):  # Успадковує id, name, description, state, notes, group_id, timestamps
    """
    Схема для представлення даних про рівень гейміфікації у відповідях API.
    Успадковує стандартні поля з `BaseMainSchema`.
    """
    # id, name, description, state, notes, group_id, created_at, updated_at, deleted_at - успадковані

    # Специфічні поля моделі Level
    required_points: int = Field(description=_("gamification.level.fields.required_points.description")) # Reuse
    level_number: Optional[int] = Field(description=_("gamification.level.fields.level_number.description")) # Reuse
    icon_url: Optional[AnyHttpUrl] = Field(None, description=_("gamification.level.fields.icon_url.description")) # Reuse

    # Пов'язані об'єкти
    group: Optional[GroupSchema] = Field(None,
                                         description=_("gamification.level.response.fields.group.description"))

    # model_config успадковується з BaseMainSchema -> BaseSchema (from_attributes=True)


if __name__ == "__main__":
    # Демонстраційний блок для схем рівнів.
    logger.info("--- Pydantic Схеми для Рівнів Гейміфікації (Level) ---")

    logger.info("\nLevelCreateSchema (приклад для створення):")
    create_level_data = {
        "name": "Золотий Рівень",  # TODO i18n
        "description": "Визначний рівень для найактивніших учасників.",  # TODO i18n
        "required_points": 10000,
        "level_number": 5,
        "icon_url": "https://example.com/icons/gold_level.png",
        "group_id": 1,  # Припустимо, специфічний для групи 1
        "state": "active"
    }
    create_level_instance = LevelCreateSchema(**create_level_data)
    logger.info(create_level_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nLevelUpdateSchema (приклад для оновлення):")
    update_level_data = {
        "description": "Оновлений опис для Золотого Рівня, тепер вимагає більше балів.",  # TODO i18n
        "required_points": 12000
    }
    update_level_instance = LevelUpdateSchema(**update_level_data)
    logger.info(update_level_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nLevelSchema (приклад відповіді API):")
    level_response_data = {
        "id": 1,
        "name": "Срібний Рівень",  # TODO i18n
        "description": "Рівень для активних учасників.",  # TODO i18n
        "state": "active",
        "group_id": 1,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "required_points": 5000,
        "level_number": 3,
        "icon_url": "https://example.com/icons/silver_level.png",
        # "group": {"id": 1, "name": "Команда Альфа", "group_type_code": "TEAM",
        #           "created_at": str(datetime.now()), "updated_at": str(datetime.now())} # Приклад GroupSchema
    }
    level_response_instance = LevelSchema(**level_response_data)
    logger.info(level_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схема для `group` тепер використовує `GroupSchema`.")
