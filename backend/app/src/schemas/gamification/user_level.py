# backend/app/src/schemas/gamification/user_level.py
import logging
from uuid import UUID
from datetime import datetime
from typing import Optional # Added Optional for LevelResponse and UserResponse

from pydantic import BaseModel, Field

from app.src.schemas.base import BaseDBRead  # Common DB fields
from app.src.schemas.gamification.level import LevelResponse # To nest level details
# Assuming user schema for nesting, replace with actual path if different
# from app.src.schemas.auth.user import UserResponse

# Initialize logger for this module
logger = logging.getLogger(__name__)

# --- UserLevel Schemas ---

class UserLevelBase(BaseModel):
    """
    Base schema for the relationship between a user and a level.
    This typically represents a user achieving a certain level.
    """
    user_id: UUID = Field(..., description="The unique identifier of the user.")
    level_id: UUID = Field(..., description="The unique identifier of the level achieved by the user.")
    achieved_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the user achieved this level."
    )

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "UserLevel"
        json_schema_extra = {
            "example": {
                "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "level_id": "b2c3d4e5-f6a7-8901-2345-67890abcdef01",
                "achieved_at": "2023-03-15T10:00:00Z"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"UserLevelBase instance created with data: {data}")

# No UserLevelCreate or UserLevelUpdate schemas are typically needed if this is purely a link table record created by business logic.
# If direct creation/update via API is intended, they would be defined similarly to other schemas.
# For now, we assume it's managed internally.

class UserLevelResponse(UserLevelBase, BaseDBRead):
    """
    Schema for representing a user's achieved level in API responses.
    Includes all fields from UserLevelBase and common DB read fields.
    It can also include nested information about the level and user.
    """
    # id: UUID # From BaseDBRead
    # created_at: datetime # From BaseDBRead
    # updated_at: datetime # From BaseDBRead

    level: Optional[LevelResponse] = Field(None, description="Detailed information about the achieved level.")
    # user: Optional[UserResponse] = Field(None, description="Detailed information about the user. Be cautious about exposing sensitive user data.")


    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        title = "UserLevelResponse"
        json_schema_extra = {
            "example": {
                "id": "c3d4e5f6-a7b8-9012-3456-7890abcdef012",
                "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "level_id": "b2c3d4e5-f6a7-8901-2345-67890abcdef01",
                "achieved_at": "2023-03-15T10:00:00Z",
                "created_at": "2023-03-15T10:00:05Z",
                "updated_at": "2023-03-15T10:00:05Z",
                "level": {
                    "id": "b2c3d4e5-f6a7-8901-2345-67890abcdef01",
                    "name": "Novice",
                    "description": "Achieved by earning the first 100 points.",
                    "min_points": 100,
                    "created_at": "2023-01-01T12:00:00Z",
                    "updated_at": "2023-01-01T12:00:00Z"
                }
                # User details example (if UserResponse is defined and included)
                # "user": {
                #     "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                #     "username": "john_doe",
                #     "email": "john.doe@example.com"
                # }
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"UserLevelResponse instance created for UserLevel ID '{self.id}'.")

logger.info("UserLevel schemas (UserLevelBase, UserLevelResponse) defined successfully.")
