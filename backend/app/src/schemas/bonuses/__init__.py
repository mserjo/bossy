# backend/app/src/schemas/bonuses/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету схем, пов'язаних з бонусами, рахунками та нагородами (`bonuses`).

Цей файл робить доступними основні схеми цієї категорії для імпорту з пакету
`backend.app.src.schemas.bonuses`.

Приклад імпорту:
from backend.app.src.schemas.bonuses import AccountSchema, TransactionSchema

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних схем
from backend.app.src.schemas.bonuses.account import (
    AccountSchema,
    AccountCreateSchema,
    AccountUpdateSchema,
)
from backend.app.src.schemas.bonuses.transaction import (
    TransactionSchema,
    TransactionCreateSchema,
    # TransactionUpdateSchema, # Зазвичай не використовується
)
from backend.app.src.schemas.bonuses.reward import (
    RewardSchema,
    RewardCreateSchema,
    RewardUpdateSchema,
)
from backend.app.src.schemas.bonuses.bonus_adjustment import (
    BonusAdjustmentSchema,
    BonusAdjustmentCreateSchema,
    # BonusAdjustmentUpdateSchema, # Зазвичай не використовується
)

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    # Account Schemas
    "AccountSchema",
    "AccountCreateSchema",
    "AccountUpdateSchema",

    # Transaction Schemas
    "TransactionSchema",
    "TransactionCreateSchema",
    # "TransactionUpdateSchema",

    # Reward Schemas
    "RewardSchema",
    "RewardCreateSchema",
    "RewardUpdateSchema",

    # Bonus Adjustment Schemas
    "BonusAdjustmentSchema",
    "BonusAdjustmentCreateSchema",
    # "BonusAdjustmentUpdateSchema",
]

# Виклик model_rebuild для схем, що використовують ForwardRef.
# from typing import ForwardRef, List, Optional, Union, Any, Dict # Потрібні імпорти для контексту
# import uuid
# from datetime import datetime, timedelta
# from decimal import Decimal
# from pydantic import BaseModel as PydanticBaseModel

# schemas_to_rebuild = [
#     AccountSchema,
#     TransactionSchema,
#     RewardSchema,
#     BonusAdjustmentSchema,
# ]

# for schema in schemas_to_rebuild:
#     try:
#         # schema.model_rebuild(force=True) # Pydantic v2
#         pass # Pydantic v2 зазвичай справляється
#     except Exception as e:
#         print(f"Warning: Could not rebuild schema {schema.__name__}: {e}")

# Поки що залишаю без явних викликів `model_rebuild`.
# Якщо виникнуть проблеми з ForwardRef, їх потрібно буде додати.
# Головне, що всі схеми експортуються через `__all__`.
#
# `TransactionUpdateSchema` та `BonusAdjustmentUpdateSchema` закоментовані в `__all__`,
# оскільки ці операції зазвичай не передбачені (транзакції та коригування є незмінними).
# Якщо вони все ж будуть потрібні, їх можна буде розкоментувати.
# Самі файли схем містять ці класи (закоментовані або з приміткою).
#
# Назва файлу `bonus_adjustment.py` (замість `bonus_rule.py`) була узгоджена.
# Схеми `BonusAdjustmentSchema` та `BonusAdjustmentCreateSchema` експортуються.
