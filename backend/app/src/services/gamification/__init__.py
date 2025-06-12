# backend/app/src/services/gamification/__init__.py
"""
Ініціалізаційний файл для модуля сервісів, пов'язаних з гейміфікацією.

Цей модуль реекспортує основні класи сервісів для управління рівнями,
досягненнями користувачів, бейджами та рейтингами.
"""

from backend.app.src.config import logger

# Явний імпорт сервісів для кращої читабельності та статичного аналізу
from backend.app.src.services.gamification.level import LevelService
from backend.app.src.services.gamification.user_level import UserLevelService
from backend.app.src.services.gamification.badge import BadgeService
from backend.app.src.services.gamification.achievement import UserAchievementService
from backend.app.src.services.gamification.rating import RatingService # Відповідно до списку файлів завдання

__all__ = [
    "LevelService",
    "UserLevelService",
    "BadgeService",
    "UserAchievementService",
    "RatingService", # Відповідно до списку файлів завдання
]

logger.info(f"Сервіси гейміфікації експортують: {__all__}")
