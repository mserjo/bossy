# backend/app/src/schemas/gamification/badge.py
import logging
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.src.schemas.base import BaseDBRead # Common DB fields
# Assuming BaseMainModel from technical_task.txt implies some fields are in models,
# schemas will reflect what's needed for API interaction.
# Fields like 'state', 'group_id', 'deleted_at', 'notes' mentioned for BaseMainModel
# would be added here if they are part of the Badge's API contract.
# For now, focusing on core badge attributes.

# Initialize logger for this module
logger = logging.getLogger(__name__)

# --- Badge Schemas ---

class BadgeBase(BaseModel):
    """
    Base schema for badges.
    Contains common attributes for all badge-related schemas.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="The name of the badge. Should be unique."
    )
    description: str = Field(
        ...,
        max_length=500,
        description="A detailed description of how the badge is earned and what it represents."
    )
    icon_url: Optional[HttpUrl] = Field(
        None,
        description="URL to an image/icon representing the badge. Must be a valid HTTP/HTTPS URL."
    )
    # group_id: Optional[UUID] = Field(None, description="Identifier of the group this badge is specific to, if applicable. If null, it's a system-wide badge.")
    # criteria: Optional[str] = Field(None, max_length=1000, description="Textual description of the criteria to earn the badge, if not covered by description.")
    # state: Optional[str] = Field(None, description="State of the badge (e.g., active, retired). From BaseMainModel concept.")

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "Badge"
        json_schema_extra = {
            "example": {
                "name": "Early Bird",
                "description": "Awarded for completing a task before 8 AM.",
                "icon_url": "https://example.com/icons/early_bird.png",
                # "group_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"BadgeBase instance created with data: {data}")

class BadgeCreate(BadgeBase):
    """
    Schema for creating a new badge.
    Inherits all fields from BadgeBase.
    """
    pass

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"BadgeCreate instance created for badge '{self.name}'.")

class BadgeUpdate(BaseModel):
    """
    Schema for updating an existing badge.
    All fields are optional for partial updates.
    """
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="The new name of the badge."
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="The new description of the badge."
    )
    icon_url: Optional[HttpUrl] = Field(
        None,
        description="New URL for the badge icon."
    )
    # group_id: Optional[UUID] = Field(None, description="New group identifier if the badge's scope is changed.")
    # criteria: Optional[str] = Field(None, max_length=1000, description="New criteria description.")
    # state: Optional[str] = Field(None, description="New state of the badge.")


    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "BadgeUpdate"
        json_schema_extra = {
            "example": {
                "name": "Super Early Bird",
                "icon_url": "https://example.com/icons/super_early_bird_v2.png"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"BadgeUpdate instance created with update data: {data}")

class BadgeResponse(BadgeBase, BaseDBRead):
    """
    Schema for representing a badge in API responses.
    Includes all fields from BadgeBase and common database read fields.
    """
    # id: UUID # From BaseDBRead
    # created_at: datetime # From BaseDBRead
    # updated_at: datetime # From BaseDBRead

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        title = "BadgeResponse"
        json_schema_extra = {
            "example": {
                "id": "d4e5f6a7-b8c9-0123-4567-890abcdef0123",
                "name": "Early Bird",
                "description": "Awarded for completing a task before 8 AM.",
                "icon_url": "https://example.com/icons/early_bird.png",
                # "group_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                # "state": "active",
                "created_at": "2023-01-05T10:00:00Z",
                "updated_at": "2023-01-05T10:00:00Z"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"BadgeResponse instance created for badge ID '{self.id}'.")

logger.info("Badge schemas (BadgeBase, BadgeCreate, BadgeUpdate, BadgeResponse) defined successfully.")
