# backend/app/src/models/bonuses/__init__.py
# -*- coding: utf-8 -*-
"""Пакет моделей SQLAlchemy для сутностей, пов'язаних з бонусною системою.

Цей пакет містить моделі даних для управління:
- Правилами нарахування бонусів (`BonusRuleModel`).
- Бонусними рахунками користувачів (`UserAccountModel`).
- Транзакціями по бонусних рахунках (`AccountTransactionModel`).
- Нагородами, які можна придбати за бонуси (`RewardModel`).

Моделі з цього пакету експортуються для використання в сервісному шарі,
API ендпоінтах та інших частинах додатку, що реалізують логіку бонусної системи.
"""

# Імпорт централізованого логера
from backend.app.src.config import logger

# Імпорт моделей з відповідних файлів цього пакету, використовуючи нову конвенцію імен.
# Припускаємо, що класи в файлах будуть перейменовані на *Model.
from backend.app.src.models.bonuses.bonus_rule import BonusRuleModel
from backend.app.src.models.bonuses.account import UserAccountModel
from backend.app.src.models.bonuses.transaction import AccountTransactionModel
from backend.app.src.models.bonuses.reward import RewardModel

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.models.bonuses import *`.
__all__ = [
    "BonusRuleModel",
    "UserAccountModel",
    "AccountTransactionModel",
    "RewardModel",
]

logger.debug("Ініціалізація пакету моделей `bonuses`...")

# Коментар щодо можливого розширення:
# В майбутньому сюди можуть бути додані інші моделі,
# наприклад, для історії нарахування бонусів за конкретні дії (BonusAccrualLogModel)
# або для категорій нагород (RewardCategoryModel).
