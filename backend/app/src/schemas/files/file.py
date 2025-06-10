# backend/app/src/schemas/files/file.py
import logging
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, HttpUrl

from app.src.schemas.base import BaseDBRead # Common DB fields

# Initialize logger for this module
logger = logging.getLogger(__name__)

# --- FileRecord Schemas ---

class FileRecordBase(BaseModel):
    """
    Base schema for file records. Represents metadata about a stored file.
    """
    file_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original name of the file."
    )
    mime_type: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="MIME type of the file (e.g., 'image/jpeg', 'application/pdf')."
    )
    size_bytes: int = Field(
        ...,
        gt=0,
        description="Size of the file in bytes."
    )
    # storage_path: str = Field(..., description="Internal storage path or key in the storage system (e.g., S3 key). Not typically exposed directly to clients.")
    file_url: Optional[HttpUrl] = Field(
        None,
        description="Publicly accessible URL for the file. This might be generated on demand or stored if static."
    )
    uploader_user_id: Optional[UUID] = Field(
        None,
        description="Identifier of the user who uploaded the file."
    )
    group_id: Optional[UUID] = Field(
        None,
        description="Identifier of the group this file is associated with (e.g., group icon, group-specific file)."
    )
    # entity_type: Optional[str] = Field(None, max_length=50, description="Type of entity this file is linked to (e.g., 'user_avatar', 'group_icon', 'task_attachment').")
    # entity_id: Optional[UUID] = Field(None, description="ID of the entity this file is linked to.")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional dictionary for additional metadata (e.g., image dimensions, EXIF data)."
    )

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "FileRecordBase"
        json_schema_extra = {
            "example": {
                "file_name": "profile_picture.jpg",
                "mime_type": "image/jpeg",
                "size_bytes": 102400, # 100KB
                "file_url": "https://example.com/storage/profile_picture.jpg",
                "uploader_user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "group_id": None,
                "metadata": {"width": 800, "height": 600}
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"FileRecordBase instance created with data: {data}")


class FileRecordCreate(FileRecordBase):
    """
    Schema for creating a new file record.
    This is typically used internally by a service after a file has been successfully uploaded and processed.
    It includes the internal storage_path.
    """
    storage_path: str = Field(
        ...,
        description="Internal storage path or key in the storage system (e.g., S3 key)."
    )
    # Fields from FileRecordBase are inherited.
    # file_url might be set by the service after creation if it's dynamically generated.

    class Config(FileRecordBase.Config):
        title = "FileRecordCreate"
        json_schema_extra = { # Extend or override example
            "example": {
                "file_name": "important_document.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 2048000, # 2MB
                "storage_path": "secure_files/user_xyz/important_document_uuid.pdf",
                "uploader_user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "metadata": {"pages": 10}
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"FileRecordCreate instance for file '{self.file_name}' at path '{self.storage_path}'.")


class FileRecordResponse(FileRecordBase, BaseDBRead):
    """
    Schema for representing a file record in API responses.
    Excludes sensitive internal fields like `storage_path` if it's not meant to be public.
    `file_url` should be present if the file is accessible.
    """
    # id: UUID # From BaseDBRead
    # created_at: datetime # From BaseDBRead
    # updated_at: datetime # From BaseDBRead

    # Ensure file_url is always present in response if the file is meant to be accessible
    file_url: HttpUrl = Field(..., description="Publicly accessible URL for the file.")


    class Config(FileRecordBase.Config):
        title = "FileRecordResponse"
        json_schema_extra = { # Override or extend example
            "example": {
                "id": "f0e1d2c3-b4a5-6789-0123-456789abcdef01",
                "file_name": "profile_picture.jpg",
                "mime_type": "image/jpeg",
                "size_bytes": 102400,
                "file_url": "https://kudos-cdn.example.com/files/f0e1d2c3-b4a5-6789-0123-456789abcdef01/profile_picture.jpg",
                "uploader_user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "group_id": None,
                "metadata": {"width": 800, "height": 600, "source": "upload"},
                "created_at": "2023-07-15T09:30:00Z",
                "updated_at": "2023-07-15T09:30:00Z"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"FileRecordResponse instance created for file ID '{self.id}'.")

logger.info("FileRecord schemas (FileRecordBase, FileRecordCreate, FileRecordResponse) defined successfully.")
