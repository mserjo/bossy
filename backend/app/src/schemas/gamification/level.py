# backend/app/src/schemas/gamification/level.py
import logging
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.src.schemas.base import BaseDBRead # Assuming you have a BaseDBRead schema for common DB fields like id, created_at, updated_at

# Initialize logger for this module
logger = logging.getLogger(__name__)

# --- Level Schemas ---

class LevelBase(BaseModel):
    """
    Base schema for game levels.
    Contains common attributes for all level-related schemas.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="The name of the level. Must be unique within a group if group-specific, or globally if system-wide."
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="A brief description of the level and its criteria or benefits."
    )
    min_points: int = Field(
        ...,
        ge=0,
        description="The minimum number of points required to reach this level."
    )
    # Example of a field that might be group-specific, if levels can be customized per group
    # group_id: Optional[UUID] = Field(None, description="Identifier of the group this level belongs to, if applicable.")

    class Config:
        orm_mode = True
        # Example for Pydantic V2, if you are using it
        # from_attributes = True
        anystr_strip_whitespace = True
        title = "Level"
        json_schema_extra = {
            "example": {
                "name": "Novice",
                "description": "Achieved by earning the first 100 points.",
                "min_points": 100,
                # "group_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"LevelBase instance created with data: {data}")

class LevelCreate(LevelBase):
    """
    Schema for creating a new level.
    Inherits all fields from LevelBase.
    No additional fields are required for creation beyond what's in LevelBase.
    """
    pass

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"LevelCreate instance created for level '{self.name}'.")

class LevelUpdate(BaseModel):
    """
    Schema for updating an existing level.
    All fields are optional for partial updates.
    """
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        description="The new name of the level."
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="The new description of the level."
    )
    min_points: Optional[int] = Field(
        None,
        ge=0,
        description="The new minimum number of points for this level."
    )
    # group_id: Optional[UUID] = Field(None, description="New group identifier if the level is being moved or its scope changed.")

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "LevelUpdate"
        json_schema_extra = {
            "example": {
                "name": "Apprentice",
                "min_points": 250
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"LevelUpdate instance created with update data: {data}")

class LevelResponse(LevelBase, BaseDBRead):
    """
    Schema for representing a level in API responses.
    Includes all fields from LevelBase and common database read fields (id, created_at, updated_at) from BaseDBRead.
    """
    # id: UUID # Already in BaseDBRead
    # created_at: datetime # Already in BaseDBRead
    # updated_at: datetime # Already in BaseDBRead

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        title = "LevelResponse"
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "name": "Novice",
                "description": "Achieved by earning the first 100 points.",
                "min_points": 100,
                # "group_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"LevelResponse instance created for level ID '{self.id}'.")

logger.info("Level schemas (LevelBase, LevelCreate, LevelUpdate, LevelResponse) defined successfully.")
