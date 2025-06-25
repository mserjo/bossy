# backend/app/src/models/gamification/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету моделей, пов'язаних з гейміфікацією (`gamification`).

Цей файл робить доступними основні моделі гейміфікації для імпорту з пакету
`backend.app.src.models.gamification`. Це спрощує імпорти в інших частинах проекту.

Приклад імпорту:
from backend.app.src.models.gamification import LevelModel, BadgeModel, AchievementModel

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних моделей, пов'язаних з гейміфікацією
from backend.app.src.models.gamification.level import LevelModel
from backend.app.src.models.gamification.user_level import UserLevelModel
from backend.app.src.models.gamification.badge import BadgeModel
from backend.app.src.models.gamification.achievement import AchievementModel
from backend.app.src.models.gamification.rating import RatingModel

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    "LevelModel",
    "UserLevelModel",
    "BadgeModel",
    "AchievementModel",
    "RatingModel",
]

# TODO: Переконатися, що всі необхідні моделі з цього пакету створені та включені до `__all__`.
# На даний момент включені всі моделі, заплановані для створення в цьому пакеті.

# Цей `__init__.py` файл важливий для організації структури проекту та забезпечення
# зручного доступу до моделей, пов'язаних з гейміфікацією.
# Він також може бути корисним для інструментів статичного аналізу або автодоповнення коду.
