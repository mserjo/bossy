import uuid
import datetime
import logging
from pydantic import BaseModel, Field
from .badge import BadgeResponse # Assuming BadgeResponse is in badge.py

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Basic config for demonstration

class UserAchievementBase(BaseModel):
    """
    Base schema for a User's Achievement (earning a badge).
    Identifies the user and the badge they earned.
    """
    user_id: uuid.UUID = Field(..., description="The unique identifier of the user who earned the achievement.")
    badge_id: uuid.UUID = Field(..., description="The unique identifier of the badge that was earned.")

    class Config:
        orm_mode = True
        # For Pydantic V2:
        # model_config = { "from_attributes": True }

class UserAchievementCreate(UserAchievementBase):
    """
    Schema for creating a new UserAchievement.
    This typically happens when a user meets the criteria for a badge.
    The 'achieved_at' timestamp can be set automatically by the server.
    """
    achieved_at: datetime.datetime | None = Field(default_factory=datetime.datetime.now, description="Timestamp when the badge was earned. Defaults to current time.")


class UserAchievementResponse(UserAchievementBase):
    """
    Schema for representing a User's Achievement in API responses.
    Includes details from UserAchievementBase plus database-generated fields and potentially the badge details.
    """
    id: uuid.UUID = Field(..., description="The unique identifier of this achievement record.")
    achieved_at: datetime.datetime = Field(..., description="Timestamp when the badge was earned.")
    badge: BadgeResponse | None = Field(None, description="Detailed information about the badge earned. Included if requested.") # Nested schema

    # For Pydantic V2, the Config class would be nested here too if needed.
    # class Config:
    #     from_attributes = True
    #
    #     model_config = {
    #         "from_attributes": True,
    #         "json_schema_extra": {
    #             "examples": [
    #                 {
    #                     "id": "ua1b2c3d4-e5f6-7890-1234-567890abcdef",
    #                     "user_id": "u1a2b3c4-d5e6-f789-0123-456789abcdef",
    #                     "badge_id": "b1a2b3c4-d5e6-f789-0123-456789abcdef",
    #                     "achieved_at": "2023-03-20T14:30:00Z",
    #                     "badge": { # Example of nested BadgeResponse
    #                         "id": "b1a2b3c4-d5e6-f789-0123-456789abcdef",
    #                         "name": "Early Adopter",
    #                         "description": "Joined within the first month of launch.",
    #                         "icon_url": "https://example.com/icons/early_adopter.png",
    #                         "created_at": "2023-01-01T00:00:00Z",
    #                         "updated_at": "2023-01-01T00:00:00Z"
    #                     }
    #                 }
    #             ]
    #         }
    #     }

# Example usage
if __name__ == "__main__":
    logger.info("Logging example from achievement.py")

    # Example of creating a UserAchievementCreate instance
    try:
        user_achievement_data = {
            "user_id": uuid.uuid4(),
            "badge_id": uuid.uuid4()
            # achieved_at will use default_factory
        }
        new_achievement = UserAchievementCreate(**user_achievement_data)
        logger.info(f"Successfully created UserAchievementCreate instance: {new_achievement.model_dump_json(indent=2)}")
    except Exception as e:
        logger.error(f"Error creating UserAchievementCreate instance: {e}")

    # Example of a UserAchievementResponse instance
    try:
        # Dummy BadgeResponse data for the nested schema
        badge_resp_data = {
            "id": uuid.uuid4(),
            "name": "Bug Squasher",
            "description": "Reported a critical bug.",
            "icon_url": "https://example.com/icons/bug_squasher.png",
            "created_at": datetime.datetime.now() - datetime.timedelta(days=5),
            "updated_at": datetime.datetime.now() - datetime.timedelta(days=2)
        }

        achievement_response_data = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "badge_id": badge_resp_data["id"], # Link to the badge's ID
            "achieved_at": datetime.datetime.now(),
            "badge": badge_resp_data # Embed the full BadgeResponse object
        }
        achievement_resp = UserAchievementResponse(**achievement_response_data)
        logger.info(f"Successfully created UserAchievementResponse instance: {achievement_resp.model_dump_json(indent=2)}")
    except Exception as e:
        logger.error(f"Error creating UserAchievementResponse instance: {e}")
