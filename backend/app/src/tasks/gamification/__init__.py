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
"""

# На даний момент, відповідні класи завдань ще не створені в модулях,
# тому імпорти будуть додані або розкоментовані, коли класи будуть реалізовані.

from .levels import RecalculateUserLevelsTask
from .badges import AwardBadgesTask
from .ratings import UpdateUserRatingsTask

__all__ = [
    'RecalculateUserLevelsTask',
    'AwardBadgesTask',
    'UpdateUserRatingsTask',
]

import logging

logger = logging.getLogger(__name__)
logger.info("Підпакет 'tasks.gamification' ініціалізовано.")
