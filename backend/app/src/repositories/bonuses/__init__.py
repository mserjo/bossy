# backend/app/src/repositories/bonuses/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет репозиторіїв для сутностей, пов'язаних з бонусами, рахунками,
транзакціями та нагородами.
"""

from .account import AccountRepository, account_repository
from .transaction import TransactionRepository, transaction_repository
from .reward import RewardRepository, reward_repository
from .bonus import BonusAdjustmentRepository, bonus_adjustment_repository # Файл bonus.py містить BonusAdjustmentModel

__all__ = [
    "AccountRepository",
    "account_repository",
    "TransactionRepository",
    "transaction_repository",
    "RewardRepository",
    "reward_repository",
    "BonusAdjustmentRepository",
    "bonus_adjustment_repository",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'repositories.bonuses' ініціалізовано.")
