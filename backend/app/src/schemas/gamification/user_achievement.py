# backend/app/src/schemas/gamification/user_achievement.py
"""
Pydantic схеми для сутності "Досягнення Користувача" (UserAchievement).

Цей модуль визначає схеми для:
- Базового представлення запису про досягнення (`UserAchievementBaseSchema`).
- Створення нового запису про досягнення (зазвичай виконується сервісом) (`UserAchievementCreateSchema`).
- Представлення даних про досягнення у відповідях API (`UserAchievementResponseSchema`).
"""
from datetime import datetime
from typing import Optional, Any

from pydantic import Field

from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.config.logging import get_logger

logger = get_logger(__name__)

# Тимчасові заповнювачі для пов'язаних схем
UserPublicProfileSchema = Any
BadgeSchema = Any # Має бути BadgeResponseSchema
GroupBriefSchema = Any


class UserAchievementBaseSchema(BaseSchema):
    """
    Базова схема для полів запису про досягнення користувача.
    """
    user_id: int = Field(description="Ідентифікатор користувача, який отримав досягнення.")
    badge_id: int = Field(description="Ідентифікатор отриманого бейджа.")
    group_id: Optional[int] = Field(None, description="ID групи, в контексті якої отримано досягнення (якщо бейдж груповий).")
    # `created_at` з TimestampedSchemaMixin буде використовуватися як `achieved_at`


class UserAchievementCreateSchema(UserAchievementBaseSchema):
    """
    Схема для створення нового запису про досягнення користувачем.
    Зазвичай цей запис створюється автоматично сервісом гейміфікації.
    """
    # Успадковує user_id, badge_id, group_id.
    # Час досягнення (created_at) буде встановлено автоматично.
    pass


class UserAchievementResponseSchema(UserAchievementBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про досягнення користувача у відповідях API.
    Поле `created_at` (з `TimestampedSchemaMixin`) позначає час отримання досягнення.
    """
    # id, created_at, updated_at успадковані.
    # user_id, badge_id, group_id успадковані.

    user: Optional[UserPublicProfileSchema] = Field(None, description="Публічний профіль користувача.")
    badge: Optional[BadgeSchema] = Field(None, description="Інформація про отриманий бейдж.") # Має бути BadgeResponseSchema
    group: Optional[GroupBriefSchema] = Field(None, description="Коротка інформація про групу, в якій отримано досягнення (якщо є).")


if __name__ == "__main__":
    from datetime import timedelta

    logger.info("--- Pydantic Схеми для Досягнень Користувачів (UserAchievement) ---")

    logger.info("\nUserAchievementCreateSchema (приклад для створення сервісом):")
    create_ua_data = {
        "user_id": 101,
        "badge_id": 22,
        "group_id": 1
    }
    create_ua_instance = UserAchievementCreateSchema(**create_ua_data)
    logger.info(create_ua_instance.model_dump_json(indent=2))

    logger.info("\nUserAchievementResponseSchema (приклад відповіді API):")
    ua_response_data = {
        "id": 1,
        "user_id": 101,
        "badge_id": 22,
        "group_id": 1,
        "created_at": datetime.now() - timedelta(hours=5),
        "updated_at": datetime.now() - timedelta(hours=5),
        # "user": {"id": 101, "name": "Гравець-Досягатор"},
        # "badge": {"id": 22, "name": "Супер Бейдж"},
        # "group": {"id": 1, "name": "Група Досягнень"}
    }
    ua_response_instance = UserAchievementResponseSchema(**ua_response_data)
    logger.info(ua_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми для пов'язаних об'єктів наразі є заповнювачами (Any).")
