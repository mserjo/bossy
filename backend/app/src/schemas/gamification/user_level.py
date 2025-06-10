# backend/app/src/schemas/gamification/user_level.py
"""
Pydantic схеми для сутності "Рівень Користувача" (UserLevel).

Цей модуль визначає схеми для:
- Базового представлення запису про рівень користувача (`UserLevelBaseSchema`).
- Створення нового запису про досягнення рівня (зазвичай виконується сервісом) (`UserLevelCreateSchema`).
- Представлення даних про рівень користувача у відповідях API (`UserLevelSchema`).
"""
from datetime import datetime
from typing import Optional, Any  # Any для тимчасових полів

from pydantic import Field

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin

# TODO: Замінити Any на конкретні схеми, коли вони будуть доступні/рефакторені.
# from backend.app.src.schemas.auth.user import UserPublicProfileSchema
# from backend.app.src.schemas.gamification.level import LevelSchema
# from backend.app.src.schemas.groups.group import GroupBriefSchema

UserPublicProfileSchema = Any  # Тимчасовий заповнювач
LevelSchema = Any  # Тимчасовий заповнювач
GroupBriefSchema = Any  # Тимчасовий заповнювач


class UserLevelBaseSchema(BaseSchema):
    """
    Базова схема для полів запису про рівень користувача.
    """
    user_id: int = Field(description="Ідентифікатор користувача, який досяг рівня.")
    level_id: int = Field(description="Ідентифікатор досягнутого рівня гейміфікації.")
    group_id: int = Field(description="Ідентифікатор групи, в межах якої досягнуто рівень.")
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

    # TODO: Замінити Any на відповідні схеми.
    user: Optional[UserPublicProfileSchema] = Field(None, description="Публічний профіль користувача.")
    level: Optional[LevelSchema] = Field(None, description="Інформація про досягнутий рівень.")
    group: Optional[GroupBriefSchema] = Field(None,
                                              description="Коротка інформація про групу, в якій досягнуто рівень.")


if __name__ == "__main__":
    # Демонстраційний блок для схем рівнів користувача.
    print("--- Pydantic Схеми для Рівнів Користувача (UserLevel) ---")

    print("\nUserLevelCreateSchema (приклад для створення сервісом):")
    create_user_level_data = {
        "user_id": 101,
        "level_id": 5,  # ID рівня "Золотий Рівень"
        "group_id": 1  # ID групи
    }
    create_user_level_instance = UserLevelCreateSchema(**create_user_level_data)
    print(create_user_level_instance.model_dump_json(indent=2))

    print("\nUserLevelSchema (приклад відповіді API):")
    user_level_response_data = {
        "id": 1,
        "user_id": 101,
        "level_id": 5,
        "group_id": 1,
        "created_at": datetime.now() - timedelta(days=1),  # Час досягнення
        "updated_at": datetime.now() - timedelta(days=1),
        # "user": {"id": 101, "name": "Гравець Один"}, # Приклад UserPublicProfileSchema
        # "level": {"id": 5, "name": "Золотий Рівень", "required_points": 10000}, # Приклад LevelSchema
        # "group": {"id": 1, "name": "Ігрова Група"} # Приклад GroupBriefSchema
    }
    user_level_response_instance = UserLevelSchema(**user_level_response_data)
    print(user_level_response_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nПримітка: Схеми для пов'язаних об'єктів (UserPublicProfileSchema, LevelSchema, GroupBriefSchema)")
    print("наразі є заповнювачами (Any). Їх потрібно буде імпортувати після їх рефакторингу/визначення.")

# Потрібно для timedelta в __main__
from datetime import timedelta
