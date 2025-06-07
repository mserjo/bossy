import uuid
import datetime
import logging
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Basic config for demonstration

class LevelBase(BaseModel):
    """
    Base schema for a Level.
    Contains common attributes for level creation and updates.
    """
    name: str = Field(..., description="The name of the level.", min_length=1, max_length=100)
    description: str | None = Field(None, description="A brief description of the level.", max_length=500)
    required_points: int = Field(..., description="The number of points required to reach this level.", ge=0)

    class Config:
        orm_mode = True # Pydantic V1 style, or `from_attributes = True` for V2
        # For Pydantic V2, use:
        # model_config = {
        #     "from_attributes": True,
        #     "json_schema_extra": {
        #         "examples": [
        #             {
        #                 "name": "Novice",
        #                 "description": "Starting level for new users.",
        #                 "required_points": 0
        #             }
        #         ]
        #     }
        # }

class LevelCreate(LevelBase):
    """
    Schema for creating a new Level.
    Inherits all attributes from LevelBase.
    """
    pass # No additional fields needed for creation beyond LevelBase

class LevelUpdate(LevelBase):
    """
    Schema for updating an existing Level.
    All fields are optional for updates.
    """
    name: str | None = Field(None, description="The new name of the level.", min_length=1, max_length=100)
    required_points: int | None = Field(None, description="The new number of points required for this level.", ge=0)
    # description can be updated via LevelBase's optional nature

class LevelResponse(LevelBase):
    """
    Schema for representing a Level in API responses.
    Includes attributes from LevelBase plus database-generated fields.
    """
    id: uuid.UUID = Field(..., description="The unique identifier of the level.")
    created_at: datetime.datetime = Field(..., description="The timestamp when the level was created.")
    updated_at: datetime.datetime = Field(..., description="The timestamp when the level was last updated.")

    # For Pydantic V2, the Config class would be nested here too if needed,
    # or use model_config at the top level of LevelResponse.
    # class Config:
    #     from_attributes = True


# Example usage (for demonstration, not part of the actual schema file usually)
if __name__ == "__main__":
    logger.info("Logging example from level.py")

    # Example of creating a LevelCreate instance
    try:
        level_data = {
            "name": "Expert",
            "description": "For users who have mastered the platform.",
            "required_points": 1000
        }
        new_level = LevelCreate(**level_data)
        logger.info(f"Successfully created LevelCreate instance: {new_level.model_dump_json(indent=2)}")
    except Exception as e:
        logger.error(f"Error creating LevelCreate instance: {e}")

    # Example of a LevelResponse instance
    try:
        level_response_data = {
            "id": uuid.uuid4(),
            "name": "Pro",
            "description": "Professional tier.",
            "required_points": 5000,
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now()
        }
        level_resp = LevelResponse(**level_response_data)
        logger.info(f"Successfully created LevelResponse instance: {level_resp.model_dump_json(indent=2)}")
    except Exception as e:
        logger.error(f"Error creating LevelResponse instance: {e}")
