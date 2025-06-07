# backend/app/src/models/gamification/__init__.py

"""
This package contains SQLAlchemy models related to gamification features,
such as levels, badges, user achievements, and ratings.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Gamification models package initialized.")

# Example of re-exporting for easier access:
# from .level import Level
# from .user_level import UserLevel
# from .badge import Badge
# from .user_achievement import UserAchievement # Corrected from plan's 'achievement.py'
# from .rating import UserGroupRating

# __all__ = [
#     "Level",
#     "UserLevel",
#     "Badge",
#     "UserAchievement",
#     "UserGroupRating",
# ]
