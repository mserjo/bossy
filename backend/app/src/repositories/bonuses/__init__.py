# backend/app/src/repositories/bonuses/__init__.py
"""
Репозиторії для моделей, пов'язаних з "Бонусами", в програмі Kudos.

Цей пакет містить класи репозиторіїв для кожної моделі, що стосується
бонусної системи: правил нарахування бонусів, рахунків користувачів,
транзакцій по рахунках та нагород.

Кожен репозиторій успадковує `BaseRepository` та надає спеціалізований
інтерфейс для роботи з конкретною моделлю даних.
"""

from .bonus_rule_repository import BonusRuleRepository
from .user_account_repository import UserAccountRepository
from .account_transaction_repository import AccountTransactionRepository
from .reward_repository import RewardRepository

__all__ = [
    "BonusRuleRepository",
    "UserAccountRepository",
    "AccountTransactionRepository",
    "RewardRepository",
]
