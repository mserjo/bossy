# backend/app/src/schemas/files/upload.py
import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime # Required for FileUploadInitiateResponse example

from pydantic import BaseModel, Field, HttpUrl

from app.src.schemas.files.file import FileRecordResponse # To return file details after successful upload

# Initialize logger for this module
logger = logging.getLogger(__name__)

# --- File Upload Schemas ---

class FileUploadInitiateRequest(BaseModel):
    """
    Schema for requesting to initiate a file upload.
    Client provides metadata about the file they intend to upload.
    """
    file_name: str = Field(..., min_length=1, max_length=255, description="The name of the file to be uploaded.")
    mime_type: str = Field(..., min_length=3, max_length=100, description="MIME type of the file.")
    size_bytes: int = Field(..., gt=0, description="Total size of the file in bytes.")
    # entity_type: Optional[str] = Field(None, max_length=50, description="Optional: Type of entity this file is for (e.g., 'user_avatar', 'group_icon'). Helps in applying specific limits or storage rules.")
    # entity_id: Optional[UUID] = Field(None, description="Optional: ID of the entity, if relevant for pre-upload checks or linking.")
    # group_id: Optional[UUID] = Field(None, description="Optional: Group ID if the file is associated with a specific group context.")

    class Config:
        orm_mode = True # Though not directly mapping to DB, useful for consistency
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "FileUploadInitiateRequest"
        json_schema_extra = {
            "example": {
                "file_name": "new_avatar.png",
                "mime_type": "image/png",
                "size_bytes": 51200, # 50KB
                # "entity_type": "user_avatar"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"FileUploadInitiateRequest instance created: {data}")

class FileUploadInitiateResponse(BaseModel):
    """
    Response after successfully initiating an upload.
    May contain a temporary upload ID or token, and potentially a presigned URL if direct-to-storage.
    """
    upload_id: UUID = Field(..., description="A unique identifier for this upload session/transaction.")
    # presigned_url: Optional[HttpUrl] = Field(None, description="A presigned URL for direct client upload to cloud storage (e.g., S3). If None, upload might be chunked through server.")
    # chunk_size_bytes: Optional[int] = Field(None, description="Recommended or required chunk size if using chunked upload through the server.")
    # expires_at: Optional[datetime] = Field(None, description="Timestamp when the upload_id or presigned_url expires.")
    message: str = Field("Upload initiated successfully. Proceed with file data.", description="User-friendly message.")


    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        title = "FileUploadInitiateResponse"
        json_schema_extra = {
            "example": {
                "upload_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                # "presigned_url": "https://s3.amazonaws.com/bucket/path?signature...",
                # "expires_at": "2023-07-15T12:30:00Z",
                "message": "Upload session created. Use the upload_id for subsequent requests."
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"FileUploadInitiateResponse instance created: {data}")


class PresignedUrlRequest(BaseModel):
    """
    Schema for requesting a presigned URL for a specific file upload.
    This might be used if the upload process is separate from initiation, or for chunked uploads.
    """
    upload_id: UUID = Field(..., description="The upload session ID obtained from initiation.")
    # part_number: Optional[int] = Field(None, ge=1, description="For S3 multipart uploads, the part number being uploaded.")
    # content_md5: Optional[str] = Field(None, description="MD5 hash of the part/file being uploaded, if required by storage.")

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "PresignedUrlRequest"
        json_schema_extra = {
            "example": {
                "upload_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                # "part_number": 1
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"PresignedUrlRequest instance created: {data}")


class PresignedUrlResponse(BaseModel):
    """
    Response containing a presigned URL for file upload.
    """
    presigned_url: HttpUrl = Field(..., description="The presigned URL to use for uploading the file/part.")
    # expires_in_seconds: Optional[int] = Field(None, description="Duration for which the URL is valid.")
    # required_headers: Optional[Dict[str, str]] = Field(None, description="Any specific headers that must be sent with the PUT request to the presigned URL.")

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        title = "PresignedUrlResponse"
        json_schema_extra = {
            "example": {
                "presigned_url": "https://s3.example.com/uploads/some_file?AWSAccessKeyId=...&Expires=...&Signature=...",
                # "expires_in_seconds": 300
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"PresignedUrlResponse instance created with URL: {self.presigned_url}")


class FileUploadCompleteRequest(BaseModel): # Added based on common patterns for confirming upload
    """
    Request to confirm that file parts (if multipart) or the entire file has been uploaded.
    This triggers final processing and FileRecord creation by the server.
    """
    upload_id: UUID = Field(..., description="The upload session ID.")
    file_name: str = Field(..., min_length=1, max_length=255, description="Original name of the file being confirmed.")
    mime_type: str = Field(..., min_length=3, max_length=100, description="MIME type of the file.")
    size_bytes: int = Field(..., gt=0, description="Total size of the uploaded file in bytes.")
    # For S3 multipart uploads, a list of eTags and part numbers might be needed here.
    # e.g., parts: List[Dict[str, Any]] = Field(None, description="List of part numbers and ETags for multipart uploads.")
    # entity_type: Optional[str] = Field(None, description="Type of entity this file is linked to, passed from initiation or here.")
    # entity_id: Optional[UUID] = Field(None, description="ID of the entity this file is linked to.")
    # group_id: Optional[UUID] = Field(None, description="Group ID if relevant.")

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        title = "FileUploadCompleteRequest"
        json_schema_extra = {
            "example": {
                "upload_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "file_name": "final_report.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 1234567
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"FileUploadCompleteRequest instance created: {data}")


class FileUploadResponse(BaseModel):
    """
    Response after a file upload is fully processed and confirmed.
    Returns the details of the created file record.
    """
    message: str = Field("File uploaded and processed successfully.", description="User-friendly confirmation message.")
    file_record: FileRecordResponse = Field(..., description="Details of the created file record.")

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        title = "FileUploadResponse"
        json_schema_extra = {
            "example": {
                "message": "File 'final_report.pdf' uploaded successfully.",
                "file_record": { # This is an example of FileRecordResponse
                    "id": "f0e1d2c3-b4a5-6789-0123-456789abcdef01",
                    "file_name": "final_report.pdf",
                    "mime_type": "application/pdf",
                    "size_bytes": 1234567,
                    "file_url": "https://kudos-cdn.example.com/files/f0e1d2c3-b4a5-6789-0123-456789abcdef01/final_report.pdf",
                    "uploader_user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                    "created_at": "2023-07-15T10:00:00Z",
                    "updated_at": "2023-07-15T10:00:00Z"
                }
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"FileUploadResponse created for file: {self.file_record.file_name}")

logger.info("File upload schemas (Initiate, PresignedUrl, Complete, Response) defined successfully.")
