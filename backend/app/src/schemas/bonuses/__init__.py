# backend/app/src/schemas/bonuses/__init__.py
"""
Pydantic схеми для сутностей, пов'язаних з "Бонусами".

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються правил нарахування бонусів,
рахунків користувачів, транзакцій по цих рахунках та нагород в програмі Kudos.
"""

# Схеми, пов'язані з Правилами Нарахування Бонусів
from .bonus_rule import (
    BonusRuleBaseSchema,
    BonusRuleCreateSchema,
    BonusRuleUpdateSchema,
    BonusRuleSchema
)

# Схеми, пов'язані з Рахунками Користувачів
from .account import (
    UserAccountBaseSchema,
    UserAccountCreateSchema,
    UserAccountUpdateSchema,
    UserAccountSchema,
    UserAccountTransactionHistorySchema
)

# Схеми, пов'язані з Транзакціями по Рахунках
from .transaction import (
    AccountTransactionBaseSchema,
    AccountTransactionCreateSchema,
    AccountTransactionSchema
)

# Схеми, пов'язані з Нагородами
from .reward import (
    RewardBaseSchema,
    RewardCreateSchema,
    RewardUpdateSchema,
    RewardSchema,
    RedeemRewardRequestSchema
)


__all__ = [
    # BonusRule schemas
    "BonusRuleBaseSchema",
    "BonusRuleCreateSchema",
    "BonusRuleUpdateSchema",
    "BonusRuleSchema",
    # UserAccount schemas
    "UserAccountBaseSchema",
    "UserAccountCreateSchema",
    "UserAccountUpdateSchema",
    "UserAccountSchema",
    "UserAccountTransactionHistorySchema",
    # AccountTransaction schemas
    "AccountTransactionBaseSchema",
    "AccountTransactionCreateSchema",
    "AccountTransactionSchema",
    # Reward schemas
    "RewardBaseSchema",
    "RewardCreateSchema",
    "RewardUpdateSchema",
    "RewardSchema",
    "RedeemRewardRequestSchema",
]
