# backend/app/src/models/bonuses/__init__.py
"""
Пакет моделей SQLAlchemy для сутностей, пов'язаних з "Бонусами".

Цей пакет містить моделі для представлення правил нарахування бонусів,
рахунків користувачів, транзакцій по цих рахунках та нагород,
які можна отримати за бонуси в програмі Kudos.

Моделі експортуються для зручного доступу з інших частин програми.
"""

from .bonus_rule import BonusRule
from .account import UserAccount
from .transaction import AccountTransaction
from .reward import Reward

__all__ = [
    "BonusRule",
    "UserAccount",
    "AccountTransaction",
    "Reward",
]

# Майбутні моделі, пов'язані з бонусною системою (наприклад, BonusAccrualLog),
# також можуть бути додані сюди для експорту.
