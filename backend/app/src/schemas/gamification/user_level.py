import uuid
import datetime
import logging
from pydantic import BaseModel, Field
from .level import LevelResponse # Assuming LevelResponse is in level.py in the same directory

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Basic config for demonstration

class UserLevelBase(BaseModel):
    """
    Base schema for a User's Level.
    Contains common attributes for identifying the user and their level.
    """
    user_id: uuid.UUID = Field(..., description="The unique identifier of the user.")
    level_id: uuid.UUID = Field(..., description="The unique identifier of the level achieved by the user.")

    class Config:
        orm_mode = True
        # For Pydantic V2:
        # model_config = { "from_attributes": True }

class UserLevelCreate(UserLevelBase):
    """
    Schema for associating a user with a level, potentially at creation.
    Often, points_accumulated might start at a default or be set by a service.
    """
    points_accumulated: int = Field(0, description="Points accumulated by the user towards this level or overall.", ge=0)

class UserLevelUpdate(BaseModel):
    """
    Schema for updating a user's level progress.
    Typically, only points are updated, and level_id might change based on points.
    """
    points_accumulated: int | None = Field(None, description="New total points accumulated by the user.", ge=0)
    level_id: uuid.UUID | None = Field(None, description="Explicitly set a new level ID for the user, if business logic allows.")


class UserLevelResponse(UserLevelBase):
    """
    Schema for representing a User's Level in API responses.
    Includes attributes from UserLevelBase plus additional details.
    """
    id: uuid.UUID = Field(..., description="The unique identifier of this user-level association.")
    points_accumulated: int = Field(..., description="Total points accumulated by the user.", ge=0)
    unlocked_at: datetime.datetime | None = Field(None, description="Timestamp when the user officially unlocked this level. Can be null if level is assigned but not formally 'unlocked' through points.")
    level: LevelResponse | None = Field(None, description="Detailed information about the level. Included if requested via query parameters or by default.") # Nested schema

    # For Pydantic V2, the Config class would be nested here too if needed,
    # or use model_config at the top level of UserLevelResponse.
    # class Config:
    #     from_attributes = True
    #
    #     model_config = {
    #         "from_attributes": True,
    #         "json_schema_extra": {
    #             "examples": [
    #                 {
    #                     "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    #                     "user_id": "u1a2b3c4-d5e6-f789-0123-456789abcdef",
    #                     "level_id": "l1a2b3c4-d5e6-f789-0123-456789abcdef",
    #                     "points_accumulated": 150,
    #                     "unlocked_at": "2023-01-15T10:00:00Z",
    #                     "level": { # Example of nested LevelResponse
    #                         "id": "l1a2b3c4-d5e6-f789-0123-456789abcdef",
    #                         "name": "Apprentice",
    #                         "description": "Users who completed the tutorial.",
    #                         "required_points": 100,
    #                         "created_at": "2023-01-01T00:00:00Z",
    #                         "updated_at": "2023-01-01T00:00:00Z"
    #                     }
    #                 }
    #             ]
    #         }
    #     }

# Example usage
if __name__ == "__main__":
    logger.info("Logging example from user_level.py")

    # Example of creating a UserLevelCreate instance
    try:
        user_level_data = {
            "user_id": uuid.uuid4(),
            "level_id": uuid.uuid4(),
            "points_accumulated": 50
        }
        new_user_level = UserLevelCreate(**user_level_data)
        logger.info(f"Successfully created UserLevelCreate instance: {new_user_level.model_dump_json(indent=2)}")
    except Exception as e:
        logger.error(f"Error creating UserLevelCreate instance: {e}")

    # Example of a UserLevelResponse instance
    try:
        # Dummy LevelResponse data for the nested schema
        level_resp_data = {
            "id": uuid.uuid4(),
            "name": "Master",
            "description": "Top tier level.",
            "required_points": 10000,
            "created_at": datetime.datetime.now() - datetime.timedelta(days=10),
            "updated_at": datetime.datetime.now() - datetime.timedelta(days=1)
        }

        user_level_response_data = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "level_id": level_resp_data["id"], # Link to the level's ID
            "points_accumulated": 12000,
            "unlocked_at": datetime.datetime.now(),
            "level": level_resp_data # Embed the full LevelResponse object
        }
        user_level_resp = UserLevelResponse(**user_level_response_data)
        logger.info(f"Successfully created UserLevelResponse instance: {user_level_resp.model_dump_json(indent=2)}")
    except Exception as e:
        logger.error(f"Error creating UserLevelResponse instance: {e}")
