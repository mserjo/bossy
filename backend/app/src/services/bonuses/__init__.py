# backend/app/src/services/bonuses/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для модуля сервісів, пов'язаних з бонусною системою.

Цей модуль реекспортує основні класи сервісів для управління бонусними рахунками,
правилами нарахування бонусів, розрахунком бонусів, нагородами та транзакціями.
"""

from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Явний імпорт сервісів для кращої читабельності та статичного аналізу
from backend.app.src.services.bonuses.bonus_rule import BonusRuleService
from backend.app.src.services.bonuses.account import UserAccountService
from backend.app.src.services.bonuses.transaction import AccountTransactionService
from backend.app.src.services.bonuses.reward import RewardService
from backend.app.src.services.bonuses.calculation import BonusCalculationService

__all__ = [
    "BonusRuleService",
    "UserAccountService",
    "AccountTransactionService",
    "RewardService",
    "BonusCalculationService",
]

logger.info(f"Сервіси бонусної системи експортують: {__all__}")
