# backend/app/src/models/gamification/__init__.py
# -*- coding: utf-8 -*-
"""Пакет моделей SQLAlchemy для сутностей, пов'язаних з гейміфікацією.

Цей пакет містить моделі даних для представлення різноманітних елементів
гейміфікації в системі, таких як:
- Рівні користувачів (`LevelModel`).
- Записи про досягнення користувачами певних рівнів (`UserLevelModel`).
- Бейджі або досягнення, які користувачі можуть отримувати (`BadgeModel`).
- Записи про отримання користувачами конкретних бейджів (`UserAchievementModel`).
- Рейтинги користувачів у групах (`UserGroupRatingModel`).

Моделі з цього пакету експортуються для використання в сервісному шарі,
API ендпоінтах та інших частинах додатку, що реалізують логіку гейміфікації.
"""

# Імпорт моделей з відповідних файлів цього пакету.
from backend.app.src.models.gamification.level import Level
from backend.app.src.models.gamification.user_level import UserLevel
from backend.app.src.models.gamification.badge import Badge
from backend.app.src.models.gamification.user_achievement import UserAchievement
from backend.app.src.models.gamification.rating import UserGroupRating
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.models.gamification import *`.
__all__ = [
    "Level",
    "UserLevel",
    "Badge",
    "UserAchievement",
    "UserGroupRating",
]

logger.debug("Ініціалізація пакету моделей `gamification`...")

# Коментар щодо можливого розширення:
# В майбутньому сюди можуть бути додані інші моделі, пов'язані з гейміфікацією,
# наприклад, для зберігання історії нарахування балів (PointLedgerModel),
# або для знімків лідербордів (LeaderboardSnapshotModel).
