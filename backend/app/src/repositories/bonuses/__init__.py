# backend/app/src/repositories/bonuses/__init__.py

"""
This package contains repository classes for bonus and reward-related entities.

Modules within this package will define repositories for bonus rules, user accounts (points),
account transactions, and redeemable rewards.
"""

# Import and re-export repository classes here as they are created.
# This allows for cleaner imports from other parts of the application,
# e.g., `from app.src.repositories.bonuses import UserAccountRepository`.

from .bonus_rule_repository import BonusRuleRepository
from .user_account_repository import UserAccountRepository
from .account_transaction_repository import AccountTransactionRepository
from .reward_repository import RewardRepository


# Define __all__ to specify which names are exported when `from .bonuses import *` is used.
# This also helps linters and IDEs understand the public API of this package.
__all__ = [
    "BonusRuleRepository",
    "UserAccountRepository",
    "AccountTransactionRepository",
    "RewardRepository",
]

# Detailed comments:
# This __init__.py file initializes the 'bonuses' sub-package within the
# 'repositories' package. Its primary roles are:
#
# 1. Package Recognition:
#    It makes Python treat the 'repositories/bonuses' directory as a sub-package.
#
# 2. Namespace Management:
#    It serves as a central point for importing and re-exporting repository
#    classes defined in other modules within this sub-package. This simplifies
#    access for other application layers.
#
# 3. Public API Definition (`__all__`):
#    The `__all__` list explicitly declares which symbols are part of the public
#    interface of this sub-package.
#
# This structure promotes a clean and organized data access layer for
# bonus, points, and reward management components.
