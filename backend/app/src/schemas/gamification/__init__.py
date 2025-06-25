# backend/app/src/schemas/gamification/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету схем, пов'язаних з гейміфікацією (`gamification`).

Цей файл робить доступними основні схеми гейміфікації для імпорту з пакету
`backend.app.src.schemas.gamification`.

Приклад імпорту:
from backend.app.src.schemas.gamification import LevelSchema, BadgeSchema

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних схем, пов'язаних з гейміфікацією
from backend.app.src.schemas.gamification.level import (
    LevelSchema,
    LevelCreateSchema,
    LevelUpdateSchema,
)
from backend.app.src.schemas.gamification.user_level import (
    UserLevelSchema,
    UserLevelCreateSchema,
    # UserLevelUpdateSchema, # Зазвичай не оновлюється напряму
)
from backend.app.src.schemas.gamification.badge import (
    BadgeSchema,
    BadgeCreateSchema,
    BadgeUpdateSchema,
)
from backend.app.src.schemas.gamification.achievement import (
    AchievementSchema,
    AchievementCreateSchema,
    # AchievementUpdateSchema, # Зазвичай не оновлюється напряму
)
from backend.app.src.schemas.gamification.rating import (
    RatingSchema,
    RatingCreateSchema,
    # RatingUpdateSchema, # Зазвичай не оновлюється напряму
)

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    # Level Schemas
    "LevelSchema",
    "LevelCreateSchema",
    "LevelUpdateSchema",

    # UserLevel Schemas
    "UserLevelSchema",
    "UserLevelCreateSchema",
    # "UserLevelUpdateSchema",

    # Badge Schemas
    "BadgeSchema",
    "BadgeCreateSchema",
    "BadgeUpdateSchema",

    # Achievement Schemas
    "AchievementSchema",
    "AchievementCreateSchema",
    # "AchievementUpdateSchema",

    # Rating Schemas
    "RatingSchema",
    "RatingCreateSchema",
    # "RatingUpdateSchema",
]

# Виклик model_rebuild для схем, що використовують ForwardRef.
# from typing import ForwardRef, List, Optional, Union, Any, Dict # Потрібні імпорти для контексту
# import uuid
# from datetime import datetime, timedelta
# from decimal import Decimal
# from pydantic import BaseModel as PydanticBaseModel

# schemas_to_rebuild = [
#     LevelSchema,
#     UserLevelSchema,
#     BadgeSchema,
#     AchievementSchema,
#     RatingSchema,
# ]

# for schema in schemas_to_rebuild:
#     try:
#         # schema.model_rebuild(force=True) # Pydantic v2
#         pass # Pydantic v2 зазвичай справляється
#     except Exception as e:
#         print(f"Warning: Could not rebuild schema {schema.__name__}: {e}")

# Поки що залишаю без явних викликів `model_rebuild`.
# Схеми Update для `UserLevel`, `Achievement`, `Rating` закоментовані в `__all__`,
# оскільки ці записи зазвичай створюються системою і не оновлюються через API,
# або оновлюються специфічною логікою (наприклад, `is_current` для `UserLevel`).
# Самі класи схем Update можуть існувати (закоментовані) у відповідних файлах.
#
# Все виглядає добре.
