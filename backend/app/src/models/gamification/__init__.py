# backend/app/src/models/gamification/__init__.py
"""
Пакет моделей SQLAlchemy для сутностей, пов'язаних з "Гейміфікацією".

Цей пакет містить моделі для представлення елементів гейміфікації
в програмі Kudos, таких як рівні, досягнення користувачів (бейджі),
та рейтинги користувачів у групах.

Моделі експортуються для зручного доступу з інших частин програми.
"""

from .level import Level
from .user_level import UserLevel
from .badge import Badge
from .user_achievement import UserAchievement
from .rating import UserGroupRating

__all__ = [
    "Level",
    "UserLevel",
    "Badge",
    "UserAchievement",
    "UserGroupRating",
]

# Майбутні моделі, пов'язані з гейміфікацією (наприклад, LeaderboardSnapshot),
# також можуть бути додані сюди для експорту.
