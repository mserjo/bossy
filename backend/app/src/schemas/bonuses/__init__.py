# backend/app/src/schemas/bonuses/__init__.py

"""
This package contains Pydantic schemas related to bonus rules, user point/currency accounts,
account transactions, and redeemable rewards.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Bonus schemas package initialized.")

# Example of re-exporting for easier access:
# from .bonus_rule import BonusRuleResponse, BonusRuleCreate
# from .account import UserAccountResponse
# from .transaction import AccountTransactionResponse
# from .reward import RewardResponse, RewardCreate

# __all__ = [
#     "BonusRuleResponse", "BonusRuleCreate",
#     "UserAccountResponse",
#     "AccountTransactionResponse",
#     "RewardResponse", "RewardCreate",
#     # ... other bonus-related schemas
# ]
