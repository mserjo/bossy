# backend/app/src/schemas/files/__init__.py
import logging

# Initialize logger for this module
logger = logging.getLogger(__name__)

logger.info("File schemas package initialized.")

# Import all schemas from this package to make them easily accessible
from .file import (
    FileRecordBase,
    FileRecordCreate,
    FileRecordResponse,
)
from .upload import (
    PresignedUrlRequest,
    PresignedUrlResponse,
    FileUploadResponse,
    FileUploadInitiateRequest, # Added based on common patterns
    FileUploadInitiateResponse # Added based on common patterns
)
from .avatar import (
    UserAvatarBase,
    UserAvatarCreate,
    UserAvatarResponse,
)

__all__ = [
    # FileRecord schemas
    "FileRecordBase",
    "FileRecordCreate",
    "FileRecordResponse",

    # Upload process schemas
    "PresignedUrlRequest", # May or may not be used depending on final upload strategy
    "PresignedUrlResponse",
    "FileUploadResponse",
    "FileUploadInitiateRequest",
    "FileUploadInitiateResponse",


    # UserAvatar schemas
    "UserAvatarBase",
    "UserAvatarCreate",
    "UserAvatarResponse",
]

logger.info(f"Successfully imported file schemas: {__all__}")
