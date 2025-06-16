# backend/app/src/tasks/gamification/__init__.py
# -*- coding: utf-8 -*-
"""
Підпакет для фонових завдань, пов'язаних з гейміфікацією.

Цей пакет містить завдання для розрахунку та оновлення
ігрових елементів системи, таких як рівні користувачів,
бейджи, рейтинги тощо.

Модулі:
    levels.py: Завдання для перерахунку рівнів користувачів.
    badges.py: Завдання для автоматичної видачі бейджів.
    ratings.py: Завдання для оновлення рейтингів користувачів.

Імпорт основних класів завдань:
    З .levels імпортується RecalculateUserLevelsTask.
    З .badges імпортується AwardBadgesTask.
    З .ratings імпортується UpdateUserRatingsTask.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

from backend.app.src.tasks.gamification.levels import RecalculateUserLevelsTask
from backend.app.src.tasks.gamification.badges import AwardBadgesTask
from backend.app.src.tasks.gamification.ratings import UpdateUserRatingsTask

from backend.app.src.config import logger # Централізований логер

__all__ = [
    'RecalculateUserLevelsTask',
    'AwardBadgesTask',
    'UpdateUserRatingsTask',
]

# import logging # Видалено

# logger = logging.getLogger(__name__) # Видалено
logger.info("Підпакет 'tasks.gamification' ініціалізовано та експортує 'RecalculateUserLevelsTask', 'AwardBadgesTask', 'UpdateUserRatingsTask'.")
