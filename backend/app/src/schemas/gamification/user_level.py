# backend/app/src/schemas/gamification/user_level.py
"""
Pydantic схеми для сутності "Рівень Користувача" (UserLevel).

Цей модуль визначає схеми для:
- Базового представлення запису про рівень користувача (`UserLevelBaseSchema`).
- Створення нового запису про досягнення рівня (зазвичай виконується сервісом) (`UserLevelCreateSchema`).
- Представлення даних про рівень користувача у відповідях API (`UserLevelSchema`).
"""
from datetime import datetime, timedelta # Moved timedelta here
from typing import Optional, Any  # Any для тимчасовых полів

from pydantic import Field

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)

# Імпорти для конкретних схем
from backend.app.src.schemas.auth.user import UserPublicProfileSchema
from backend.app.src.schemas.gamification.level import LevelSchema # Relative import if in same dir, else full path
from backend.app.src.schemas.groups.group import GroupSchema


# Placeholder assignments removed
# UserPublicProfileSchema = Any
# LevelSchema = Any
# GroupBriefSchema = Any


class UserLevelBaseSchema(BaseSchema):
    """
    Базова схема для полів запису про рівень користувача.
    """
    user_id: int = Field(description=_("gamification.user_level.fields.user_id.description"))
    level_id: int = Field(description=_("gamification.user_level.fields.level_id.description"))
    group_id: Optional[int] = Field(None, description=_("gamification.user_level.fields.group_id.description"))
    # `created_at` з TimestampedSchemaMixin буде використовуватися як `achieved_at` у UserLevelSchema.

    # model_config успадковується з BaseSchema (from_attributes=True)


class UserLevelCreateSchema(UserLevelBaseSchema):
    """
    Схема для створення нового запису про досягнення рівня користувачем.
    Зазвичай цей запис створюється автоматично сервісом гейміфікації.
    """
    # Успадковує user_id, level_id, group_id.
    # Час досягнення (created_at) буде встановлено автоматично.
    pass


class UserLevelSchema(UserLevelBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про досягнутий користувачем рівень у відповідях API.
    Поле `created_at` (з `TimestampedSchemaMixin`) позначає час досягнення рівня.
    """
    # id, created_at, updated_at успадковані.
    # user_id, level_id, group_id успадковані.

    user: Optional[UserPublicProfileSchema] = Field(None, description=_("gamification.user_level.response.fields.user.description"))
    level: Optional[LevelSchema] = Field(None, description=_("gamification.user_level.response.fields.level.description"))
    group: Optional[GroupSchema] = Field(None, # Changed from GroupBriefSchema to GroupSchema
                                         description=_("gamification.user_level.response.fields.group.description"))


if __name__ == "__main__":
    # Демонстраційний блок для схем рівнів користувача.
    logger.info("--- Pydantic Схеми для Рівнів Користувача (UserLevel) ---")

    logger.info("\nUserLevelCreateSchema (приклад для створення сервісом):")
    create_user_level_data = {
        "user_id": 101,
        "level_id": 5,  # ID рівня "Золотий Рівень"
        "group_id": 1  # ID групи
    }
    create_user_level_instance = UserLevelCreateSchema(**create_user_level_data)
    logger.info(create_user_level_instance.model_dump_json(indent=2))

    logger.info("\nUserLevelSchema (приклад відповіді API):")
    user_level_response_data = {
        "id": 1,
        "user_id": 101,
        "level_id": 5,
        "group_id": 1,
        "created_at": datetime.now() - timedelta(days=1),  # Час досягнення
        "updated_at": datetime.now() - timedelta(days=1),
        # Приклади для пов'язаних об'єктів (закоментовано, бо потребують повних даних схем)
        # "user": {"id": 101, "username": "player1", "name": "Гравець Один"},
        # "level": {"id": 5, "name": "Золотий Рівень", "required_points": 10000,
        #           "created_at": str(datetime.now()), "updated_at": str(datetime.now())},
        # "group": {"id": 1, "name": "Ігрова Група", "group_type_code": "GAMING",
        #           "created_at": str(datetime.now()), "updated_at": str(datetime.now())}
    }
    user_level_response_instance = UserLevelSchema(**user_level_response_data)
    logger.info(user_level_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми для пов'язаних об'єктів тепер імпортовані.")
    logger.info("Приклади даних для цих полів у `user_level_response_data` закоментовані,")
    logger.info("оскільки потребують повної структури відповідних схем.")
