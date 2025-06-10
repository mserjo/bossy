# backend/app/src/schemas/gamification/achievement.py
"""
Pydantic схеми для сутності "Досягнення Користувача" (UserAchievement).

Цей модуль визначає схеми для:
- Базового представлення запису про досягнення (`UserAchievementBaseSchema`).
- Створення нового запису про отримання бейджа (зазвичай виконується сервісом) (`UserAchievementCreateSchema`).
- Представлення даних про досягнення користувача у відповідях API (`UserAchievementSchema`).
"""
from datetime import datetime
from typing import Optional, Any  # Any для тимчасових полів

from pydantic import Field

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# TODO: Замінити Any на конкретні схеми, коли вони будуть доступні/рефакторені.
# from backend.app.src.schemas.auth.user import UserPublicProfileSchema
# from backend.app.src.schemas.gamification.badge import BadgeSchema
# from backend.app.src.schemas.groups.group import GroupBriefSchema

UserPublicProfileSchema = Any  # Тимчасовий заповнювач
BadgeSchema = Any  # Тимчасовий заповнювач
GroupBriefSchema = Any  # Тимчасовий заповнювач


class UserAchievementBaseSchema(BaseSchema):
    """
    Базова схема для полів запису про досягнення користувача (отримання бейджа).
    """
    user_id: int = Field(description="Ідентифікатор користувача, який отримав досягнення.")
    badge_id: int = Field(description="Ідентифікатор отриманого бейджа.")
    group_id: Optional[int] = Field(None,
                                    description="ID групи, в контексті якої отримано досягнення (якщо бейдж груповий).")
    # `created_at` з TimestampedSchemaMixin буде використовуватися як `achieved_at` у UserAchievementSchema.

    # model_config успадковується з BaseSchema (from_attributes=True)


class UserAchievementCreateSchema(UserAchievementBaseSchema):
    """
    Схема для створення нового запису про отримання бейджа користувачем.
    Зазвичай цей запис створюється автоматично сервісом гейміфікації.
    """
    # Успадковує user_id, badge_id, group_id.
    # Час досягнення (created_at) буде встановлено автоматично.
    pass


class UserAchievementSchema(UserAchievementBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про досягнення користувача у відповідях API.
    Поле `created_at` (з `TimestampedSchemaMixin`) позначає час отримання досягнення.
    """
    # id, created_at, updated_at успадковані.
    # user_id, badge_id, group_id успадковані.

    # TODO: Замінити Any на відповідні схеми.
    user: Optional[UserPublicProfileSchema] = Field(None, description="Публічний профіль користувача.")
    badge: Optional[BadgeSchema] = Field(None, description="Інформація про отриманий бейдж.")
    group: Optional[GroupBriefSchema] = Field(None,
                                              description="Коротка інформація про групу, в якій отримано досягнення (якщо є).")


if __name__ == "__main__":
    # Демонстраційний блок для схем досягнень користувача.
    logger.info("--- Pydantic Схеми для Досягнень Користувача (UserAchievement) ---")

    logger.info("\nUserAchievementCreateSchema (приклад для створення сервісом):")
    create_achievement_data = {
        "user_id": 101,
        "badge_id": 2,  # ID бейджа "Зірка Спільноти"
        "group_id": 1  # ID групи, якщо це групове досягнення
    }
    create_achievement_instance = UserAchievementCreateSchema(**create_achievement_data)
    logger.info(create_achievement_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nUserAchievementSchema (приклад відповіді API):")
    achievement_response_data = {
        "id": 1,
        "user_id": 101,
        "badge_id": 2,
        "group_id": 1,
        "created_at": datetime.now() - timedelta(days=5),  # Час отримання
        "updated_at": datetime.now() - timedelta(days=5),
        # "user": {"id": 101, "name": "Активний Користувач"}, # Приклад UserPublicProfileSchema
        # "badge": {"id": 2, "name": "Зірка Спільноти", "icon_url": "..."}, # Приклад BadgeSchema
        # "group": {"id": 1, "name": "Команда Розробки"} # Приклад GroupBriefSchema
    }
    achievement_response_instance = UserAchievementSchema(**achievement_response_data)
    logger.info(achievement_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми для пов'язаних об'єктів (UserPublicProfileSchema, BadgeSchema, GroupBriefSchema)")
    logger.info("наразі є заповнювачами (Any). Їх потрібно буде імпортувати після їх рефакторингу/визначення.")

# Потрібно для timedelta в __main__
from datetime import timedelta
