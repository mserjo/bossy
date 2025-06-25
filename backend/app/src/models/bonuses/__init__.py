# backend/app/src/models/bonuses/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету моделей, пов'язаних з бонусами, рахунками та нагородами (`bonuses`).

Цей файл робить доступними основні моделі цієї категорії для імпорту з пакету
`backend.app.src.models.bonuses`. Це спрощує імпорти в інших частинах проекту.

Приклад імпорту:
from backend.app.src.models.bonuses import AccountModel, TransactionModel, RewardModel

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних моделей
from backend.app.src.models.bonuses.account import AccountModel
from backend.app.src.models.bonuses.transaction import TransactionModel
from backend.app.src.models.bonuses.reward import RewardModel
from backend.app.src.models.bonuses.bonus import BonusAdjustmentModel # Модель для ручних коригувань

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    "AccountModel",
    "TransactionModel",
    "RewardModel",
    "BonusAdjustmentModel",
]

# TODO: Переконатися, що всі необхідні моделі з цього пакету створені та включені до `__all__`.
# На даний момент включені AccountModel, TransactionModel, RewardModel та BonusAdjustmentModel.
# Модель BonusTypeModel знаходиться в пакеті `dictionaries`.

# Цей `__init__.py` файл важливий для організації структури проекту та забезпечення
# зручного доступу до моделей, пов'язаних з бонусною системою.
# Він також може бути корисним для інструментів статичного аналізу або автодоповнення коду.
