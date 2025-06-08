# backend/app/src/repositories/gamification/__init__.py

"""
This package contains repository classes for gamification-related entities.

Modules within this package will define repositories for levels, badges,
user achievements, user levels, and ratings.
"""

# Import and re-export repository classes here as they are created.
# This allows for cleaner imports from other parts of the application,
# e.g., `from app.src.repositories.gamification import LevelRepository`.

from .level_repository import LevelRepository
from .user_level_repository import UserLevelRepository
from .badge_repository import BadgeRepository
# from .user_achievement_repository import UserAchievementRepository
# from .user_group_rating_repository import UserGroupRatingRepository


# Define __all__ to specify which names are exported when `from .gamification import *` is used.
# This also helps linters and IDEs understand the public API of this package.
__all__ = [
    "LevelRepository",
    "UserLevelRepository",
    "BadgeRepository",
    # "UserAchievementRepository",
    # "UserGroupRatingRepository",
]

# Detailed comments:
# This __init__.py file initializes the 'gamification' sub-package within the
# 'repositories' package. Its primary roles are:
#
# 1. Package Recognition:
#    It makes Python treat the 'repositories/gamification' directory as a sub-package.
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
# gamification components.
