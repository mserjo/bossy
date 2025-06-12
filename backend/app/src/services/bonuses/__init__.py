# backend/app/src/services/bonuses/__init__.py
"""
Ініціалізаційний файл для модуля сервісів, пов'язаних з бонусною системою.

Цей модуль реекспортує основні класи сервісів для управління бонусними рахунками,
правилами нарахування бонусів, розрахунком бонусів, нагородами та транзакціями.
"""

from backend.app.src.config import logger

# Явний імпорт сервісів для кращої читабельності та статичного аналізу
from backend.app.src.services.bonuses.bonus_rule import BonusRuleService
from backend.app.src.services.bonuses.account import UserAccountService # Або UserBonusAccountService, уточнити назву класу
from backend.app.src.services.bonuses.transaction import AccountTransactionService # Або BonusTransactionService, уточнити
from backend.app.src.services.bonuses.reward import RewardService
from backend.app.src.services.bonuses.calculation import BonusCalculationService

__all__ = [
    "BonusRuleService",
    "UserAccountService",       # Уточнити фактичну назву класу у файлі account.py
    "AccountTransactionService",# Уточнити фактичну назву класу у файлі transaction.py
    "RewardService",
    "BonusCalculationService",
]

logger.info(f"Сервіси бонусної системи експортують: {__all__}")
