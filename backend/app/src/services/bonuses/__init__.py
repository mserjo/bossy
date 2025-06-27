# backend/app/src/services/bonuses/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет сервісів для сутностей, пов'язаних з бонусами.
Включає сервіси для управління рахунками, транзакціями, нагородами
та ручними коригуваннями бонусів.
"""

from .account_service import AccountService, account_service
from .transaction_service import TransactionService, transaction_service
from .reward_service import RewardService, reward_service
from .bonus_adjustment_service import BonusAdjustmentService, bonus_adjustment_service

__all__ = [
    "AccountService",
    "account_service",
    "TransactionService",
    "transaction_service",
    "RewardService",
    "reward_service",
    "BonusAdjustmentService",
    "bonus_adjustment_service",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'services.bonuses' ініціалізовано.")
