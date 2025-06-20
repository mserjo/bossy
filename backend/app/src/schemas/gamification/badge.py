# backend/app/src/schemas/gamification/badge.py
"""
Pydantic схеми для сутності "Бейдж" (Badge) в системі гейміфікації.

Цей модуль визначає схеми для:
- Створення нового бейджа (`BadgeCreateSchema`).
- Оновлення існуючого бейджа (`BadgeUpdateSchema`).
- Представлення даних про бейдж у відповідях API (`BadgeSchema`).
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

BADGE_NAME_MAX_LENGTH = 255
BADGE_ICON_URL_MAX_LENGTH = 512  # Збігається з моделлю


class BadgeBaseSchema(
    BaseSchema):  # Не успадковує BaseMainSchema, оскільки ID/timestamps не потрібні для Create/Update базових полів
    """
    Базова схема для полів бейджа, спільних для створення та оновлення.
    """
    name: str = Field(
        ...,
        max_length=BADGE_NAME_MAX_LENGTH,
        description=_("gamification.badge.fields.name.description"),
        examples=["Першопроходець", "Командний Гравець"]
    )
    description: Optional[str] = Field(
        None,
        description=_("gamification.badge.fields.description.description")
    )
    icon_file_id: Optional[int] = Field(None, description=_("gamification.badge.fields.icon_file_id.description"))
    group_id: Optional[int] = Field(
        None,
        description=_("gamification.badge.fields.group_id.description")
    )
    state: Optional[str] = Field(
        None,
        max_length=50,
        description=_("gamification.badge.fields.state.description"),
        examples=["active"]
    )
    notes: Optional[str] = Field(
        None,
        description=_("gamification.badge.fields.notes.description")
    )


class BadgeCreateSchema(BadgeBaseSchema):
    """
    Схема для створення нового бейджа гейміфікації.
    Успадковує всі поля від `BadgeBaseSchema`.
    """
    pass


class BadgeUpdateSchema(BadgeBaseSchema):
    """
    Схема для оновлення існуючого бейджа гейміфікації.
    Всі поля, успадковані з `BadgeBaseSchema`, стають опціональними.
    """
    name: Optional[str] = Field(None, max_length=BADGE_NAME_MAX_LENGTH, description=_("gamification.badge.fields.name.description")) # Reuse
    description: Optional[str] = Field(None, description=_("gamification.badge.fields.description.description")) # Reuse
    icon_file_id: Optional[int] = Field(None, description=_("gamification.badge.fields.icon_file_id.description")) # Reuse, or specific update key
    group_id: Optional[int] = Field(None,
                                    description=_("gamification.badge.fields.group_id.description")) # Reuse, or specific update key
    state: Optional[str] = Field(None, max_length=50, description=_("gamification.badge.fields.state.description")) # Reuse
    notes: Optional[str] = Field(None, description=_("gamification.badge.fields.notes.description")) # Reuse


class BadgeSchema(BaseMainSchema):  # Успадковує id, name, description, state, notes, group_id, timestamps
    """
    Схема для представлення даних про бейдж гейміфікації у відповідях API.
    Успадковує стандартні поля з `BaseMainSchema`.
    """
    # id, name, description, state, notes, group_id, created_at, updated_at, deleted_at - успадковані

    # Специфічні поля моделі Badge
    icon_url: Optional[AnyHttpUrl] = Field(None, description=_("gamification.badge.response.fields.icon_url.description"))

    # Пов'язані об'єкти
    group: Optional[GroupSchema] = Field(None,
                                         description=_("gamification.badge.response.fields.group.description"))

    # model_config успадковується з BaseMainSchema -> BaseSchema (from_attributes=True)


if __name__ == "__main__":
    # Демонстраційний блок для схем бейджів.
    logger.info("--- Pydantic Схеми для Бейджів Гейміфікації (Badge) ---")

    logger.info("\nBadgeCreateSchema (приклад для створення):")
    create_badge_data = {
        "name": "Зірка Спільноти",  # TODO i18n
        "description": "Надається за активну допомогу іншим учасникам.",  # TODO i18n
        "icon_file_id": 201, # Example file ID
        "state": "active"
        # group_id може бути None для глобального бейджа
    }
    create_badge_instance = BadgeCreateSchema(**create_badge_data)
    logger.info(create_badge_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nBadgeUpdateSchema (приклад для оновлення):")
    update_badge_data = {
        "description": "Оновлений опис для Зірки Спільноти: надається за 100 корисних відповідей.",  # TODO i18n
        "icon_file_id": 202 # Example new file ID
    }
    update_badge_instance = BadgeUpdateSchema(**update_badge_data)
    logger.info(update_badge_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nBadgeSchema (приклад відповіді API):")
    badge_response_data = {
        "id": 1,
        "name": "Ранній Птах",  # TODO i18n
        "description": "Надається за реєстрацію в перший тиждень роботи системи.",  # TODO i18n
        "state": "active",
        "group_id": None,  # Глобальний бейдж
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "icon_url": "https://example.com/icons/early_bird.png",
    }
    badge_response_instance = BadgeSchema(**badge_response_data)
    logger.info(badge_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схема для `group` тепер використовує `GroupSchema`.")
