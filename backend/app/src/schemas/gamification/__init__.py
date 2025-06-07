# Initializes the gamification schemas package
# This file also exports relevant Pydantic models from this package for easier access.

import logging

logger = logging.getLogger(__name__)
logger.info("Gamification schemas package initialized.")

from .level import LevelBase, LevelCreate, LevelUpdate, LevelResponse
from .user_level import UserLevelBase, UserLevelCreate, UserLevelUpdate, UserLevelResponse
from .badge import BadgeBase, BadgeCreate, BadgeUpdate, BadgeResponse
from .achievement import UserAchievementBase, UserAchievementCreate, UserAchievementResponse
from .rating import UserGroupRatingBase, UserGroupRatingCreate, UserGroupRatingUpdate, UserGroupRatingResponse

__all__ = [
    # Level Schemas
    "LevelBase",
    "LevelCreate",
    "LevelUpdate",
    "LevelResponse",
    # UserLevel Schemas
    "UserLevelBase",
    "UserLevelCreate",
    "UserLevelUpdate",
    "UserLevelResponse",
    # Badge Schemas
    "BadgeBase",
    "BadgeCreate",
    "BadgeUpdate",
    "BadgeResponse",
    # UserAchievement Schemas
    "UserAchievementBase",
    "UserAchievementCreate",
    "UserAchievementResponse",
    # UserGroupRating Schemas
    "UserGroupRatingBase",
    "UserGroupRatingCreate",
    "UserGroupRatingUpdate",
    "UserGroupRatingResponse",
]

logger.info(f"Exported schemas: {', '.join(__all__)}")
