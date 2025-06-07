# backend/app/src/schemas/files/avatar.py
import logging
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field

from app.src.schemas.base import BaseDBRead # Common DB fields
from app.src.schemas.files.file import FileRecordResponse # To nest avatar image details

# Initialize logger for this module
logger = logging.getLogger(__name__)

# --- UserAvatar Schemas ---

class UserAvatarBase(BaseModel):
    """
    Base schema for user avatars. Links a user to a file record representing their avatar.
    """
    user_id: UUID = Field(..., description="The unique identifier of the user to whom this avatar belongs.")
    file_id: UUID = Field(..., description="The unique identifier of the file record used as the avatar image.")
    is_active: bool = Field(
        True,
        description="Indicates if this is the currently active avatar for the user. Allows for multiple avatar uploads with one active."
    )
    # position: Optional[int] = Field(None, ge=0, description="Optional: If users can have multiple avatars, this could define display order.")

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "UserAvatarBase"
        json_schema_extra = {
            "example": {
                "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "file_id": "f0e1d2c3-b4a5-6789-0123-456789abcdef01",
                "is_active": True
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"UserAvatarBase instance created with data: {data}")


class UserAvatarCreate(BaseModel): # Does not inherit BaseDBRead as it's for creation
    """
    Schema for creating a new user avatar link.
    This would typically be used after an avatar image file has been uploaded and a FileRecord created.
    Only `file_id` is needed, `user_id` usually comes from the authenticated user context.
    """
    file_id: UUID = Field(..., description="The unique identifier of the (newly uploaded) file record to be used as the avatar.")
    # user_id will likely be injected by the service based on the current authenticated user.
    # is_active might be set by the service (e.g., new uploads become active, others inactive).

    class Config:
        orm_mode = True # Useful if the service layer expects ORM-compatible data
        # from_attributes = True # For Pydantic V2
        title = "UserAvatarCreate"
        json_schema_extra = {
            "example": {
                "file_id": "f0e1d2c3-b4a5-6789-0123-456789abcdef01"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"UserAvatarCreate instance created for file_id '{self.file_id}'.")

class UserAvatarUpdate(BaseModel):
    """
    Schema for updating user avatar properties, primarily for setting an existing avatar record as active/inactive.
    """
    is_active: bool = Field(..., description="Set to true to make this avatar active, false to deactivate.")

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        title = "UserAvatarUpdate"
        json_schema_extra = {
            "example": {
                "is_active": True
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"UserAvatarUpdate instance created with data: {data}")


class UserAvatarResponse(UserAvatarBase, BaseDBRead):
    """
    Schema for representing a user's avatar in API responses.
    Includes all fields from UserAvatarBase, common DB read fields,
    and nests the actual file record details.
    """
    # id: UUID # From BaseDBRead (ID of the UserAvatar link record)
    # created_at: datetime # From BaseDBRead
    # updated_at: datetime # From BaseDBRead

    file: Optional[FileRecordResponse] = Field(None, description="Detailed information about the avatar image file.")

    class Config(UserAvatarBase.Config):
        title = "UserAvatarResponse"
        json_schema_extra = { # Override or extend example
            "example": {
                "id": "e5f6a7b8-c9d0-1234-5678-90abcdef01234", # ID of the UserAvatar record
                "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "file_id": "f0e1d2c3-b4a5-6789-0123-456789abcdef01",
                "is_active": True,
                "created_at": "2023-07-15T10:30:00Z",
                "updated_at": "2023-07-15T10:35:00Z",
                "file": { # Nested FileRecordResponse example
                    "id": "f0e1d2c3-b4a5-6789-0123-456789abcdef01",
                    "file_name": "profile_picture.jpg",
                    "mime_type": "image/jpeg",
                    "size_bytes": 102400,
                    "file_url": "https://kudos-cdn.example.com/files/f0e1d2c3-b4a5-6789-0123-456789abcdef01/profile_picture.jpg",
                    "uploader_user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                    "created_at": "2023-07-15T09:30:00Z",
                    "updated_at": "2023-07-15T09:30:00Z"
                }
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"UserAvatarResponse instance created for UserAvatar ID '{self.id}'.")

logger.info("UserAvatar schemas (UserAvatarBase, UserAvatarCreate, UserAvatarUpdate, UserAvatarResponse) defined successfully.")
