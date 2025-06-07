# backend/app/src/models/bonuses/__init__.py

"""
This package contains SQLAlchemy models related to bonuses, user accounts (for points/currency),
rewards, and transactions.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Bonus models package initialized.")

# Example of re-exporting for easier access:
# from .bonus_rule import BonusRule
# from .account import UserAccount
# from .transaction import AccountTransaction
# from .reward import Reward

# __all__ = [
#     "BonusRule",
#     "UserAccount",
#     "AccountTransaction",
#     "Reward",
# ]
