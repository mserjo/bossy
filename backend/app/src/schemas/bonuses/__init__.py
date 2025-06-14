# backend/app/src/schemas/bonuses/__init__.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для сутностей, пов'язаних з бонусною системою.

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються:
- Правил нарахування бонусів (`BonusRule...Schema` з `bonus_rule.py`).
- Бонусних рахунків користувачів (`UserAccount...Schema` з `account.py`).
- Транзакцій по бонусних рахунках (`AccountTransaction...Schema` з `transaction.py`).
- Нагород, які можна придбати за бонуси (`Reward...Schema` з `reward.py`).

Моделі з цього пакету експортуються для використання в сервісному шарі та API.
"""

# Імпорт централізованого логера
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Схеми, пов'язані з Правилами Нарахування Бонусів
from backend.app.src.schemas.bonuses.bonus_rule import (
    BonusRuleBaseSchema,
    BonusRuleCreateSchema,
    BonusRuleUpdateSchema,
    BonusRuleResponseSchema  # Оновлено ім'я
)

# Схеми, пов'язані з Рахунками Користувачів
from backend.app.src.schemas.bonuses.account import (
    UserAccountBaseSchema,
    UserAccountCreateSchema,
    UserAccountUpdateSchema,
    UserAccountResponseSchema,  # Оновлено ім'я
    UserAccountTransactionHistorySchema # Допоміжна схема, залишаємо як є
)

# Схеми, пов'язані з Транзакціями по Рахунках
from backend.app.src.schemas.bonuses.transaction import (
    AccountTransactionBaseSchema,
    AccountTransactionCreateSchema,
    # AccountTransactionUpdateSchema, # Зазвичай транзакції не оновлюються
    AccountTransactionResponseSchema  # Оновлено ім'я
)

# Схеми, пов'язані з Нагородами
from backend.app.src.schemas.bonuses.reward import (
    RewardBaseSchema,
    RewardCreateSchema,
    RewardUpdateSchema,
    RewardResponseSchema,  # Оновлено ім'я
    RedeemRewardRequestSchema # Допоміжна схема, залишаємо як є
)


__all__ = [
    # BonusRule schemas
    "BonusRuleBaseSchema",
    "BonusRuleCreateSchema",
    "BonusRuleUpdateSchema",
    "BonusRuleResponseSchema",
    # UserAccount schemas
    "UserAccountBaseSchema",
    "UserAccountCreateSchema",
    "UserAccountUpdateSchema",
    "UserAccountResponseSchema",
    "UserAccountTransactionHistorySchema",
    # AccountTransaction schemas
    "AccountTransactionBaseSchema",
    "AccountTransactionCreateSchema",
    # "AccountTransactionUpdateSchema",
    "AccountTransactionResponseSchema",
    # Reward schemas
    "RewardBaseSchema",
    "RewardCreateSchema",
    "RewardUpdateSchema",
    "RewardResponseSchema",
    "RedeemRewardRequestSchema",
]

logger.debug("Ініціалізація пакету схем Pydantic `bonuses`...")
