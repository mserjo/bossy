# backend/app/src/schemas/gamification/achievement.py
import logging
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from app.src.schemas.base import BaseDBRead  # Common DB fields
from app.src.schemas.gamification.badge import BadgeResponse # To nest badge details
# from app.src.schemas.auth.user import UserResponse # Assuming user schema for nesting

# Initialize logger for this module
logger = logging.getLogger(__name__)

# --- UserAchievement Schemas ---

class UserAchievementBase(BaseModel):
    """
    Base schema for user achievements, linking a user to a badge they've earned.
    """
    user_id: UUID = Field(..., description="The unique identifier of the user who earned the achievement.")
    badge_id: UUID = Field(..., description="The unique identifier of the badge that was awarded.")
    achieved_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the user was awarded this badge/achievement."
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional dictionary to store additional context about the achievement, e.g., related task ID, event details."
    )

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "UserAchievement"
        json_schema_extra = {
            "example": {
                "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "badge_id": "d4e5f6a7-b8c9-0123-4567-890abcdef0123",
                "achieved_at": "2023-04-01T09:30:00Z",
                "context": {"task_id": "f0e1d2c3-b4a5-6789-0123-456789abcdef01"}
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"UserAchievementBase instance created with data: {data}")

# UserAchievementCreate is typically handled by business logic when a badge is awarded.
# If direct API creation is needed, it would look like:
# class UserAchievementCreate(UserAchievementBase):
#     pass

# UserAchievementUpdate is usually not applicable as achievements are milestones.
# If updates were needed (e.g., to context), it would be defined here.

class UserAchievementResponse(UserAchievementBase, BaseDBRead):
    """
    Schema for representing a user's achievement in API responses.
    Includes all fields from UserAchievementBase, common DB read fields,
    and can nest badge and user details.
    """
    # id: UUID # From BaseDBRead
    # created_at: datetime # From BaseDBRead
    # updated_at: datetime # From BaseDBRead

    badge: Optional[BadgeResponse] = Field(None, description="Detailed information about the awarded badge.")
    # user: Optional[UserResponse] = Field(None, description="Detailed information about the user. Consider privacy implications.")

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        title = "UserAchievementResponse"
        json_schema_extra = {
            "example": {
                "id": "e5f6a7b8-c9d0-1234-5678-90abcdef01234",
                "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "badge_id": "d4e5f6a7-b8c9-0123-4567-890abcdef0123",
                "achieved_at": "2023-04-01T09:30:00Z",
                "context": {"task_id": "f0e1d2c3-b4a5-6789-0123-456789abcdef01", "comment": "Completed with bonus"},
                "created_at": "2023-04-01T09:30:05Z",
                "updated_at": "2023-04-01T09:30:05Z",
                "badge": {
                    "id": "d4e5f6a7-b8c9-0123-4567-890abcdef0123",
                    "name": "Early Bird",
                    "description": "Awarded for completing a task before 8 AM.",
                    "icon_url": "https://example.com/icons/early_bird.png",
                    "created_at": "2023-01-05T10:00:00Z",
                    "updated_at": "2023-01-05T10:00:00Z"
                }
                # "user": { ... user details ... }
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"UserAchievementResponse instance created for UserAchievement ID '{self.id}'.")

logger.info("UserAchievement schemas (UserAchievementBase, UserAchievementResponse) defined successfully.")
