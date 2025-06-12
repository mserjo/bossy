# backend/app/src/schemas/gamification/__init__.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для сутностей, пов'язаних з гейміфікацією.

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються елементів
гейміфікації в додатку. Сюди входять схеми для:
- Бейджів (`Badge...Schema` з `badge.py`).
- Рівнів (`Level...Schema` з `level.py`).
- Рейтингів користувачів у групах (`UserGroupRating...Schema` з `rating.py`).
- Досягнень користувачів (зв'язок користувач-бейдж) (`UserAchievement...Schema` з `achievement.py`).
- Рівнів користувачів (зв'язок користувач-рівень) (`UserLevel...Schema` з `user_level.py`).

Моделі з цього пакету експортуються для використання в сервісному шарі,
API ендпоінтах та інших частинах додатку, що реалізують логіку гейміфікації.
"""

# Імпорт централізованого логера
from backend.app.src.config import logger

# Схеми, пов'язані з Рівнями
from backend.app.src.schemas.gamification.level import (
    LevelBaseSchema,
    LevelCreateSchema,
    LevelUpdateSchema,
    LevelResponseSchema  # Оновлено ім'я
)

# Схеми, пов'язані з Рівнями Користувачів
from backend.app.src.schemas.gamification.user_level import (
    UserLevelBaseSchema,
    UserLevelCreateSchema,
    UserLevelResponseSchema  # Оновлено ім'я
)

# Схеми, пов'язані з Бейджами
from backend.app.src.schemas.gamification.badge import (
    BadgeBaseSchema,
    BadgeCreateSchema,
    BadgeUpdateSchema,
    BadgeResponseSchema  # Оновлено ім'я
)

# Схеми, пов'язані з Досягненнями Користувачів (отриманням бейджів)
from backend.app.src.schemas.gamification.achievement import (
    UserAchievementBaseSchema,
    UserAchievementCreateSchema,
    UserAchievementResponseSchema  # Оновлено ім'я
)

# Схеми, пов'язані з Рейтингами Користувачів у Групах
from backend.app.src.schemas.gamification.rating import (
    UserGroupRatingBaseSchema,
    UserGroupRatingCreateSchema,
    UserGroupRatingUpdateSchema,
    UserGroupRatingResponseSchema  # Оновлено ім'я
)


__all__ = [
    # Level schemas
    "LevelBaseSchema",
    "LevelCreateSchema",
    "LevelUpdateSchema",
    "LevelResponseSchema", # Оновлено ім'я
    # UserLevel schemas
    "UserLevelBaseSchema",
    "UserLevelCreateSchema",
    "UserLevelResponseSchema", # Оновлено ім'я
    # Badge schemas
    "BadgeBaseSchema",
    "BadgeCreateSchema",
    "BadgeUpdateSchema",
    "BadgeResponseSchema", # Оновлено ім'я
    # UserAchievement schemas
    "UserAchievementBaseSchema",
    "UserAchievementCreateSchema",
    "UserAchievementResponseSchema", # Оновлено ім'я
    # UserGroupRating schemas
    "UserGroupRatingBaseSchema",
    "UserGroupRatingCreateSchema",
    "UserGroupRatingUpdateSchema",
    "UserGroupRatingResponseSchema", # Оновлено ім'я
]

logger.debug("Ініціалізація пакету схем Pydantic `gamification`...")
