# backend/app/src/schemas/gamification/__init__.py
"""
Pydantic схеми для сутностей, пов'язаних з "Гейміфікацією".

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються елементів
гейміфікації в програмі Kudos, таких як рівні, бейджі (досягнення)
та рейтинги користувачів.
"""

# Схеми, пов'язані з Рівнями
from .level import (
    LevelBaseSchema,
    LevelCreateSchema,
    LevelUpdateSchema,
    LevelSchema
)

# Схеми, пов'язані з Рівнями Користувачів
from .user_level import (
    UserLevelBaseSchema,
    UserLevelCreateSchema,
    UserLevelSchema
)

# Схеми, пов'язані з Бейджами
from .badge import (
    BadgeBaseSchema,
    BadgeCreateSchema,
    BadgeUpdateSchema,
    BadgeSchema
)

# Схеми, пов'язані з Досягненнями Користувачів (отриманням бейджів)
# Файл називається achievement.py, але схеми стосуються UserAchievement
from .achievement import (
    UserAchievementBaseSchema,
    UserAchievementCreateSchema,
    UserAchievementSchema
)

# Схеми, пов'язані з Рейтингами Користувачів у Групах
from .rating import (
    UserGroupRatingBaseSchema,
    UserGroupRatingCreateSchema,
    UserGroupRatingUpdateSchema,
    UserGroupRatingSchema
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
