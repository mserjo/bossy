# backend/app/src/repositories/gamification/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет репозиторіїв для сутностей, пов'язаних з гейміфікацією.
Включає репозиторії для рівнів, бейджів, досягнень користувачів та рейтингів.
"""

from .level import LevelRepository, level_repository
from .user_level import UserLevelRepository, user_level_repository
from .badge import BadgeRepository, badge_repository
from .achievement import AchievementRepository, achievement_repository
from .rating import RatingRepository, rating_repository

__all__ = [
    "LevelRepository",
    "level_repository",
    "UserLevelRepository",
    "user_level_repository",
    "BadgeRepository",
    "badge_repository",
    "AchievementRepository",
    "achievement_repository",
    "RatingRepository",
    "rating_repository",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'repositories.gamification' ініціалізовано.")
