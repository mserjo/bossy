# backend/app/src/repositories/gamification/__init__.py
"""
Репозиторії для моделей, пов'язаних з "Гейміфікацією", в програмі Kudos.

Цей пакет містить класи репозиторіїв для кожної моделі, що стосується
елементів гейміфікації: рівнів, досягнень рівнів користувачами,
бейджиків та їх отримання користувачами, а також рейтингів.

Кожен репозиторій успадковує `BaseRepository` та надає спеціалізований
інтерфейс для роботи з конкретною моделлю даних.
"""

from backend.app.src.repositories.gamification.level_repository import LevelRepository
from backend.app.src.repositories.gamification.user_level_repository import UserLevelRepository
from backend.app.src.repositories.gamification.badge_repository import BadgeRepository
from backend.app.src.repositories.gamification.user_achievement_repository import UserAchievementRepository
from backend.app.src.repositories.gamification.rating_repository import UserGroupRatingRepository

__all__ = [
    "LevelRepository",
    "UserLevelRepository",
    "BadgeRepository",
    "UserAchievementRepository",
    "UserGroupRatingRepository",
]
