import uuid
import datetime
import logging
from pydantic import BaseModel, Field, HttpUrl # HttpUrl for icon_url

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Basic config for demonstration

class BadgeBase(BaseModel):
    """
    Base schema for a Badge.
    Contains common attributes for badge creation and updates.
    """
    name: str = Field(..., description="The name of the badge.", min_length=1, max_length=100)
    description: str | None = Field(None, description="A brief description of what this badge represents or how it's earned.", max_length=500)
    icon_url: HttpUrl | None = Field(None, description="A URL pointing to an image/icon for the badge.")
    # required_level_id: uuid.UUID | None = Field(None, description="Optional: ID of a level required to be eligible for this badge.")

    class Config:
        orm_mode = True
        # For Pydantic V2:
        # model_config = {
        #     "from_attributes": True,
        #     "json_schema_extra": {
        #         "examples": [
        #             {
        #                 "name": "First Steps",
        #                 "description": "Awarded for completing the onboarding tutorial.",
        #                 "icon_url": "https://example.com/icons/first_steps.png"
        #             }
        #         ]
        #     }
        # }

class BadgeCreate(BadgeBase):
    """
    Schema for creating a new Badge.
    Inherits all attributes from BadgeBase.
    """
    pass # No additional fields needed for creation beyond BadgeBase

class BadgeUpdate(BadgeBase):
    """
    Schema for updating an existing Badge.
    All fields are optional for updates.
    """
    name: str | None = Field(None, description="The new name of the badge.", min_length=1, max_length=100)
    # description, icon_url can be updated via BadgeBase's optional nature.

class BadgeResponse(BadgeBase):
    """
    Schema for representing a Badge in API responses.
    Includes attributes from BadgeBase plus database-generated fields.
    """
    id: uuid.UUID = Field(..., description="The unique identifier of the badge.")
    created_at: datetime.datetime = Field(..., description="The timestamp when the badge was created.")
    updated_at: datetime.datetime = Field(..., description="The timestamp when the badge was last updated.")

    # For Pydantic V2, the Config class would be nested here too if needed.
    # class Config:
    #     from_attributes = True


# Example usage
if __name__ == "__main__":
    logger.info("Logging example from badge.py")

    # Example of creating a BadgeCreate instance
    try:
        badge_data = {
            "name": "Community Helper",
            "description": "Awarded for helping 10 users in the community forum.",
            "icon_url": "https://example.com/icons/helper.png"
        }
        new_badge = BadgeCreate(**badge_data)
        logger.info(f"Successfully created BadgeCreate instance: {new_badge.model_dump_json(indent=2)}")
    except Exception as e:
        logger.error(f"Error creating BadgeCreate instance: {e}")

    # Example of a BadgeResponse instance
    try:
        badge_response_data = {
            "id": uuid.uuid4(),
            "name": "Super User",
            "description": "Recognizes exceptional contribution and activity.",
            "icon_url": "https://example.com/icons/superuser.png",
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now()
        }
        badge_resp = BadgeResponse(**badge_response_data)
        logger.info(f"Successfully created BadgeResponse instance: {badge_resp.model_dump_json(indent=2)}")
    except Exception as e:
        logger.error(f"Error creating BadgeResponse instance: {e}")
