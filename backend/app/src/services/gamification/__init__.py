# backend/app/src/services/gamification/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет сервісів для сутностей, пов'язаних з гейміфікацією.
Включає сервіси для управління рівнями, бейджами, досягненнями користувачів та рейтингами.
"""

from .level_service import LevelService, level_service
from .user_level_service import UserLevelService, user_level_service
from .badge_service import BadgeService, badge_service
from .achievement_service import AchievementService, achievement_service
from .rating_service import RatingService, rating_service

__all__ = [
    "LevelService",
    "level_service",
    "UserLevelService",
    "user_level_service",
    "BadgeService",
    "badge_service",
    "AchievementService",
    "achievement_service",
    "RatingService",
    "rating_service",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'services.gamification' ініціалізовано.")
