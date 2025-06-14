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
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Схеми, пов'язані з Рівнями
from backend.app.src.schemas.gamification.level import (
    LevelBaseSchema,
    LevelCreateSchema,
    LevelUpdateSchema,
    LevelSchema  # Використовуємо фактичну назву
)

# Схеми, пов'язані з Рівнями Користувачів
from backend.app.src.schemas.gamification.user_level import (
    UserLevelBaseSchema,
    UserLevelCreateSchema,
    UserLevelSchema  # Використовуємо фактичну назву
)

# Схеми, пов'язані з Бейджами
from backend.app.src.schemas.gamification.badge import (
    BadgeBaseSchema,
    BadgeCreateSchema,
    BadgeUpdateSchema,
    BadgeSchema  # Використовуємо фактичну назву
)

# Схеми, пов'язані з Досягненнями Користувачів (отриманням бейджів)
from backend.app.src.schemas.gamification.user_achievement import ( # Змінено шлях з achievement.py
    UserAchievementBaseSchema,
    UserAchievementCreateSchema,
    UserAchievementSchema  # Використовуємо фактичну назву
)

# Схеми, пов'язані з Рейтингами Користувачів у Групах
from backend.app.src.schemas.gamification.rating import (
    UserGroupRatingBaseSchema,
    UserGroupRatingCreateSchema,
    UserGroupRatingUpdateSchema,
    UserGroupRatingSchema  # Використовуємо фактичну назву
)


__all__ = [
    # Level schemas
    "LevelBaseSchema",
    "LevelCreateSchema",
    "LevelUpdateSchema",
    "LevelSchema",
    # UserLevel schemas
    "UserLevelBaseSchema",
    "UserLevelCreateSchema",
    "UserLevelSchema",
    # Badge schemas
    "BadgeBaseSchema",
    "BadgeCreateSchema",
    "BadgeUpdateSchema",
    "BadgeSchema",
    # UserAchievement schemas
    "UserAchievementBaseSchema",
    "UserAchievementCreateSchema",
    "UserAchievementSchema",
    # UserGroupRating schemas
    "UserGroupRatingBaseSchema",
    "UserGroupRatingCreateSchema",
    "UserGroupRatingUpdateSchema",
    "UserGroupRatingSchema",
]

logger.debug("Ініціалізація пакету схем Pydantic `gamification`...")
