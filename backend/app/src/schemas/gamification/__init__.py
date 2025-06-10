# backend/app/src/schemas/gamification/__init__.py
import logging

# Initialize logger for this module
logger = logging.getLogger(__name__)

logger.info("Gamification schemas package initialized.")

# Import all schemas from this package to make them easily accessible
from .level import LevelBase, LevelCreate, LevelUpdate, LevelResponse
from .user_level import UserLevelBase, UserLevelResponse
from .badge import BadgeBase, BadgeCreate, BadgeUpdate, BadgeResponse
from .achievement import UserAchievementBase, UserAchievementResponse
from .rating import UserGroupRatingBase, UserGroupRatingResponse

__all__ = [
    # Level schemas
    "LevelBase",
    "LevelCreate",
    "LevelUpdate",
    "LevelResponse",
    # UserLevel schemas
    "UserLevelBase",
    "UserLevelResponse",
    # Badge schemas
    "BadgeBase",
    "BadgeCreate",
    "BadgeUpdate",
    "BadgeResponse",
    # UserAchievement schemas
    "UserAchievementBase",
    "UserAchievementResponse",
    # UserGroupRating schemas
    "UserGroupRatingBase",
    "UserGroupRatingResponse",
]

logger.info(f"Successfully imported gamification schemas: {__all__}")
