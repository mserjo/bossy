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

# Імпорт централізованого логера
from backend.app.src.config import logger

# Імпорт моделей з відповідних файлів цього пакету, використовуючи нову конвенцію імен.
# Припускаємо, що класи в файлах будуть перейменовані на *Model.
from backend.app.src.models.gamification.level import LevelModel
from backend.app.src.models.gamification.user_level import UserLevelModel
from backend.app.src.models.gamification.badge import BadgeModel
from backend.app.src.models.gamification.user_achievement import UserAchievementModel
from backend.app.src.models.gamification.rating import UserGroupRatingModel

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.models.gamification import *`.
__all__ = [
    "LevelModel",
    "UserLevelModel",
    "BadgeModel",
    "UserAchievementModel",
    "UserGroupRatingModel",
]

logger.debug("Ініціалізація пакету моделей `gamification`...")

# Коментар щодо можливого розширення:
# В майбутньому сюди можуть бути додані інші моделі, пов'язані з гейміфікацією,
# наприклад, для зберігання історії нарахування балів (PointLedgerModel),
# або для знімків лідербордів (LeaderboardSnapshotModel).
