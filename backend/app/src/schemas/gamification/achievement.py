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
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)

# Імпорти для конкретних схем
from backend.app.src.schemas.auth.user import UserPublicProfileSchema
from backend.app.src.schemas.gamification.badge import BadgeSchema
from backend.app.src.schemas.groups.group import GroupSchema


# Placeholder assignments removed
# UserPublicProfileSchema = Any
# BadgeSchema = Any
# GroupBriefSchema = Any


class UserAchievementBaseSchema(BaseSchema):
    """
    Базова схема для полів запису про досягнення користувача (отримання бейджа).
    """
    user_id: int = Field(description=_("gamification.achievement.fields.user_id.description"))
    badge_id: int = Field(description=_("gamification.achievement.fields.badge_id.description"))
    group_id: Optional[int] = Field(None,
                                    description=_("gamification.achievement.fields.group_id.description"))
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

    user: Optional[UserPublicProfileSchema] = Field(None, description=_("gamification.achievement.response.fields.user.description"))
    badge: Optional[BadgeSchema] = Field(None, description=_("gamification.achievement.response.fields.badge.description"))
    group: Optional[GroupSchema] = Field(None, # Changed from GroupBriefSchema
                                         description=_("gamification.achievement.response.fields.group.description"))


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
        # Приклади для пов'язаних об'єктів (закоментовано, бо потребують повних даних схем)
        # "user": {"id": 101, "username": "achiever", "name": "Активний Користувач"},
        # "badge": {"id": 2, "name": "Зірка Спільноти", "icon_url": "...",
        #           "created_at": str(datetime.now()), "updated_at": str(datetime.now())},
        # "group": {"id": 1, "name": "Команда Розробки", "group_type_code": "PROJECT",
        #           "created_at": str(datetime.now()), "updated_at": str(datetime.now())}
    }
    achievement_response_instance = UserAchievementSchema(**achievement_response_data)
    logger.info(achievement_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми для пов'язаних об'єктів тепер імпортовані.")
    logger.info("Приклади даних для цих полів у `achievement_response_data` закоментовані,")
    logger.info("оскільки потребують повної структури відповідних схем.")

# timedelta імпортовано на початку файлу
