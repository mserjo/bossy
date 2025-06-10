# backend/app/src/schemas/gamification/rating.py
import logging
from uuid import UUID
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.src.schemas.base import BaseDBRead # Common DB fields
# from app.src.schemas.auth.user import UserPublicProfile # For user details in rating entry
# from app.src.schemas.groups.group import GroupResponse # For group details

# Initialize logger for this module
logger = logging.getLogger(__name__)

# --- UserGroupRating Schemas ---

class UserGroupRatingBase(BaseModel):
    """
    Base schema for user ratings within a group.
    This represents a user's score or rank in a specific group's leaderboard or rating system.
    """
    user_id: UUID = Field(..., description="The unique identifier of the user.")
    group_id: UUID = Field(..., description="The unique identifier of the group for which this rating applies.")
    rating_score: int = Field(
        ...,
        description="The calculated rating or score for the user in this group. Can be points, rank, etc."
    )
    # rank: Optional[int] = Field(None, ge=1, description="The user's rank within the group based on the rating_score.")
    period_start_date: Optional[datetime] = Field(
        None,
        description="Start date of the period for which this rating is valid (e.g., weekly, monthly ratings)."
    )
    period_end_date: Optional[datetime] = Field(
        None,
        description="End date of the period for which this rating is valid."
    )
    # season_id: Optional[UUID] = Field(None, description="Identifier for a 'season' or specific rating cycle, if applicable.")

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "UserGroupRating"
        json_schema_extra = {
            "example": {
                "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "group_id": "b2c3d4e5-f6a7-8901-2345-67890abcdef01",
                "rating_score": 1500,
                # "rank": 1,
                "period_start_date": "2023-05-01T00:00:00Z",
                "period_end_date": "2023-05-31T23:59:59Z"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"UserGroupRatingBase instance created with data: {data}")

# UserGroupRatingCreate and UserGroupRatingUpdate are likely managed by internal processes
# that calculate ratings periodically or based on events. Direct API manipulation might not be standard.
# If needed, they would be defined here. For example:
# class UserGroupRatingCreate(UserGroupRatingBase):
#     pass
#
# class UserGroupRatingUpdate(BaseModel):
#     rating_score: Optional[int] = None
#     rank: Optional[int] = Field(None, ge=1)
#     # etc.

class UserGroupRatingResponse(UserGroupRatingBase, BaseDBRead):
    """
    Schema for representing a user's group rating in API responses.
    Includes all fields from UserGroupRatingBase, common DB read fields,
    and can nest user and group details.
    """
    # id: UUID # From BaseDBRead
    # created_at: datetime # From BaseDBRead
    # updated_at: datetime # From BaseDBRead

    # user: Optional[UserPublicProfile] = Field(None, description="Public profile information of the user.")
    # group: Optional[GroupResponse] = Field(None, description="Detailed information about the group.")

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        title = "UserGroupRatingResponse"
        json_schema_extra = {
            "example": {
                "id": "f6a7b8c9-d0e1-2345-6789-0abcdef012345",
                "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "group_id": "b2c3d4e5-f6a7-8901-2345-67890abcdef01",
                "rating_score": 1500,
                # "rank": 1,
                "period_start_date": "2023-05-01T00:00:00Z",
                "period_end_date": "2023-05-31T23:59:59Z",
                "created_at": "2023-05-01T00:05:00Z",
                "updated_at": "2023-05-28T10:15:00Z"
                # "user": { "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef", "username": "top_player", "avatar_url": "..." },
                # "group": { "id": "b2c3d4e5-f6a7-8901-2345-67890abcdef01", "name": "Elite Gamers Club" }
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"UserGroupRatingResponse instance created for UserGroupRating ID '{self.id}'.")

# Schema for a leaderboard or a list of ratings
class GroupLeaderboardResponse(BaseModel):
    """
    Schema for representing a group leaderboard.
    """
    group_id: UUID = Field(..., description="The unique identifier of the group for this leaderboard.")
    # group_name: Optional[str] = Field(None, description="Name of the group.") # Could be fetched and added by the service
    ratings: List[UserGroupRatingResponse] = Field(..., description="List of user ratings in the group, typically sorted.")
    total_participants: int = Field(..., ge=0, description="Total number of participants in this rating period/group.")
    # generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when this leaderboard snapshot was generated.")

    class Config:
        orm_mode = True # if this schema might be mapped from an ORM model directly (less likely for this aggregate)
        # from_attributes = True # For Pydantic V2
        title = "GroupLeaderboardResponse"
        json_schema_extra = {
            "example": {
                "group_id": "b2c3d4e5-f6a7-8901-2345-67890abcdef01",
                # "group_name": "Elite Gamers Club",
                "ratings": [
                    {
                        "id": "f6a7b8c9-d0e1-2345-6789-0abcdef012345",
                        "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                        "group_id": "b2c3d4e5-f6a7-8901-2345-67890abcdef01",
                        "rating_score": 1500,
                        # "rank": 1,
                        "period_start_date": "2023-05-01T00:00:00Z",
                        "period_end_date": "2023-05-31T23:59:59Z",
                        "created_at": "2023-05-01T00:05:00Z",
                        "updated_at": "2023-05-28T10:15:00Z"
                    }
                ],
                "total_participants": 1,
                # "generated_at": "2023-05-29T00:00:00Z"
            }
        }
    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"GroupLeaderboardResponse instance created for group ID '{self.group_id}'.")


logger.info("UserGroupRating schemas (UserGroupRatingBase, UserGroupRatingResponse, GroupLeaderboardResponse) defined successfully.")
