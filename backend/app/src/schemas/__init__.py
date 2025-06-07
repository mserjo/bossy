# backend/app/src/schemas/__init__.py

"""
This package will contain Pydantic schemas used for data validation,
serialization, and API request/response models.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Schemas package initialized.")

# It can be useful to re-export base schemas or common schemas from here, for example:
# from .base import BaseSchema, PaginatedResponse, MessageResponse

from .gamification import (
    LevelBase,
    LevelCreate,
    LevelUpdate,
    LevelResponse,
    UserLevelBase,
    UserLevelResponse,
    BadgeBase,
    BadgeCreate,
    BadgeUpdate,
    BadgeResponse,
    UserAchievementBase,
    UserAchievementResponse,
    UserGroupRatingBase,
    UserGroupRatingResponse,
    GroupLeaderboardResponse,
)

__all__ = [
    # Base schemas (example, uncomment if you have them in .base)
    # "BaseSchema",
    # "PaginatedResponse",
    # "MessageResponse",

    # Gamification Schemas
    "LevelBase",
    "LevelCreate",
    "LevelUpdate",
    "LevelResponse",
    "UserLevelBase",
    "UserLevelResponse",
    "BadgeBase",
    "BadgeCreate",
    "BadgeUpdate",
    "BadgeResponse",
    "UserAchievementBase",
    "UserAchievementResponse",
    "UserGroupRatingBase",
    "UserGroupRatingResponse",
    "GroupLeaderboardResponse",
]

logger.info(f"Successfully exported schemas: {__all__}")
