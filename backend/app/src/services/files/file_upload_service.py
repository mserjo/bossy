# backend/app/src/services/files/file_upload_service.py
import logging
import os
import aiofiles # For async file operations if storing locally
import shutil # For moving files if storing locally
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta # Not directly used but good for general availability
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.src.services.base import BaseService
from app.src.config.settings import settings
from app.src.schemas.files.upload import (
    FileUploadInitiateRequest,
    FileUploadInitiateResponse,
    PresignedUrlRequest,
    PresignedUrlResponse,
    FileUploadCompleteRequest,
    FileUploadResponse
)
from app.src.schemas.files.file import FileRecordCreate
# from app.src.services.files.file_record_service import FileRecordService

logger = logging.getLogger(__name__)

class FileUploadService(BaseService):
    """
    Service for handling the file upload process.
    This includes initiating uploads, potentially generating presigned URLs (for cloud storage),
    processing uploaded files (moving from temp to permanent storage), and coordinating
    with FileRecordService to save metadata.
    Actual file I/O for local storage is placeholder. S3/Cloud integration is conceptual.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self._setup_local_storage_paths()
        logger.info("FileUploadService initialized.")


    def _setup_local_storage_paths(self):
        """Sets up local storage paths from settings and ensures directories exist."""
        # Ensure settings attributes are accessed safely with defaults if not present
        _base_path_str = getattr(settings, 'LOCAL_FILE_STORAGE_PATH', "./uploads")
        self.local_storage_base_path = Path(_base_path_str)
        self.temp_upload_dir = self.local_storage_base_path / "temp"
        self.permanent_storage_dir = self.local_storage_base_path / "permanent"

        _max_size_setting = getattr(settings, 'MAX_FILE_SIZE_BYTES', None)
        self.max_file_size_bytes = _max_size_setting if isinstance(_max_size_setting, int) else (10 * 1024 * 1024) # 10MB default

        _allowed_mimes_setting = getattr(settings, 'ALLOWED_MIME_TYPES', None)
        self.allowed_mime_types = _allowed_mimes_setting if isinstance(_allowed_mimes_setting, set) else {"image/jpeg", "image/png", "application/pdf"}


        try:
            self.temp_upload_dir.mkdir(parents=True, exist_ok=True)
            self.permanent_storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Local storage paths initialized: TEMP='{self.temp_upload_dir}', PERMANENT='{self.permanent_storage_dir}'")
        except Exception as e:
            logger.error(f"Failed to create local storage directories: {e}", exc_info=True)


    async def initiate_upload(
        self,
        initiate_data: FileUploadInitiateRequest,
        uploader_user_id: UUID # Added uploader_user_id based on usage in complete_upload
    ) -> FileUploadInitiateResponse:
        logger.info(f"Initiating upload for file '{initiate_data.file_name}' by user '{uploader_user_id}'.")

        if initiate_data.size_bytes > self.max_file_size_bytes:
            raise ValueError(f"File size {initiate_data.size_bytes} bytes exceeds maximum of {self.max_file_size_bytes} bytes.")

        if initiate_data.mime_type not in self.allowed_mime_types:
            logger.warning(f"MIME type '{initiate_data.mime_type}' not in allowed list: {self.allowed_mime_types}. Proceeding with caution.")
            # For now, just a warning. Could be a ValueError in stricter implementations.

        upload_id = uuid4()

        temp_file_path_dir = self.temp_upload_dir / str(upload_id)
        # No file created yet, just an ID to track. Client will send data to an endpoint using this ID.
        logger.info(f"Upload ID '{upload_id}' generated for local storage. Expected temp dir: {temp_file_path_dir}")

        # In a real S3 scenario, presigned URL would be generated here.
        # For local, this response indicates server is ready for data associated with upload_id.
        return FileUploadInitiateResponse(upload_id=upload_id, message="Upload initiated. Send file data.")


    async def handle_file_data_upload(
        self,
        upload_id: UUID,
        file_name: str,
        file_data_chunk: bytes,
        is_last_chunk: bool = True,
        chunk_number: Optional[int] = None
    ) -> Dict[str, Any]:
        logger.info(f"Handling file data for upload ID '{upload_id}', file '{file_name}', chunk: {chunk_number if chunk_number is not None else 'N/A'}, is_last: {is_last_chunk}.")

        temp_dir_for_upload = self.temp_upload_dir / str(upload_id)
        try:
            temp_dir_for_upload.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Could not create temp directory {temp_dir_for_upload} for upload {upload_id}: {e}")
            raise ValueError(f"Upload preparation failed for {upload_id}")

        temp_file_path = temp_dir_for_upload / file_name

        try:
            mode = 'wb' if (chunk_number == 1 or chunk_number is None) else 'ab'
            async with aiofiles.open(temp_file_path, mode) as f:
                await f.write(file_data_chunk)
            logger.info(f"Data written to temporary file: {temp_file_path} (mode: {mode})")

            if is_last_chunk:
                return {"status": "success", "message": "File data received. Ready for completion.", "temp_path": str(temp_file_path)}
            else:
                return {"status": "chunk_received", "message": f"Chunk {chunk_number} received. Awaiting next.", "next_chunk_expected": (chunk_number or 0) + 1}

        except Exception as e:
            logger.error(f"Error writing file data for upload ID '{upload_id}' to {temp_file_path}: {e}", exc_info=True)
            if temp_file_path.exists():
                try: os.remove(temp_file_path)
                except Exception as e_del: logger.error(f"Failed to cleanup partial temp file {temp_file_path}: {e_del}")
            raise ValueError(f"Failed to save uploaded file data for {upload_id}.")


    async def complete_upload(
        self,
        upload_id: UUID,
        completion_data: FileUploadCompleteRequest,
        uploader_user_id: UUID
    ) -> FileUploadResponse:
        logger.info(f"Completing upload for ID '{upload_id}', file '{completion_data.file_name}' by user '{uploader_user_id}'.")

        temp_file_path = self.temp_upload_dir / str(upload_id) / completion_data.file_name

        if not temp_file_path.exists() or not temp_file_path.is_file():
            logger.error(f"Temporary file for upload ID '{upload_id}' at {temp_file_path} not found or is not a file.")
            raise ValueError(f"Uploaded file data not found for session {upload_id}.")

        actual_size = temp_file_path.stat().st_size
        if actual_size != completion_data.size_bytes:
            logger.warning(f"File size mismatch for upload ID '{upload_id}'. Client: {completion_data.size_bytes}, Actual: {actual_size}. Using actual size.")

        permanent_file_dir_name = str(uuid4())
        permanent_file_storage_dir = self.permanent_storage_dir / permanent_file_dir_name
        permanent_file_storage_dir.mkdir(parents=True, exist_ok=True)
        permanent_file_path = permanent_file_storage_dir / completion_data.file_name # Use original client-provided filename

        temp_dir_for_upload = self.temp_upload_dir / str(upload_id) # Define for finally block

        try:
            shutil.move(str(temp_file_path), str(permanent_file_path))
            logger.info(f"File moved from '{temp_file_path}' to permanent storage: '{permanent_file_path}'.")
        except Exception as e:
            logger.error(f"Failed to move file from temp to permanent storage for upload ID '{upload_id}': {e}", exc_info=True)
            raise ValueError("Failed to finalize file storage.")
        finally:
            if temp_dir_for_upload.exists():
                try: shutil.rmtree(temp_dir_for_upload)
                except Exception as e_rm: logger.error(f"Failed to cleanup temp dir {temp_dir_for_upload}: {e_rm}")

        storage_path_for_record = str(permanent_file_path.relative_to(self.local_storage_base_path))
        file_url_for_record = f"/static/{storage_path_for_record}" # Example if /static serves local_storage_base_path

        from app.src.services.files.file_record_service import FileRecordService
        file_record_service = FileRecordService(self.db_session)

        file_record_create_data = FileRecordCreate(
            file_name=completion_data.file_name,
            mime_type=completion_data.mime_type,
            size_bytes=actual_size,
            storage_path=storage_path_for_record,
            file_url=file_url_for_record,
            uploader_user_id=uploader_user_id,
            group_id=getattr(completion_data, 'group_id', None), # Safely access group_id
            metadata=getattr(completion_data, 'metadata', None)  # Safely access metadata
        )

        created_file_record_response: Optional[FileRecordResponse] = None
        try:
            created_file_record_response = await file_record_service.create_file_record(file_record_create_data)
            if not created_file_record_response: # Should not happen if create_file_record raises on failure
                raise ValueError("File record creation returned None unexpectedly.")
        except ValueError as ve:
            logger.error(f"Failed to create file record after upload {upload_id}: {ve}", exc_info=True)
            await self.delete_actual_file(str(permanent_file_path)) # Pass absolute path to ensure correct deletion
            raise

        logger.info(f"Upload ID '{upload_id}' completed. FileRecord ID '{created_file_record_response.id}' created.")
        return FileUploadResponse(
            message=f"File '{created_file_record_response.file_name}' uploaded successfully.",
            file_record=created_file_record_response
        )

    async def delete_actual_file(self, storage_path_or_key: str) -> bool:
        logger.info(f"Attempting to delete actual file from storage: '{storage_path_or_key}'")

        try:
            # Treat storage_path_or_key as potentially absolute if passed from complete_upload's error handling,
            # or relative if passed from FileRecordService (where it's stored relative).
            if os.path.isabs(storage_path_or_key):
                abs_file_path = Path(storage_path_or_key)
            else:
                abs_file_path = (self.local_storage_base_path / storage_path_or_key).resolve()

            # Security check: ensure path is within permanent_storage_dir or local_storage_base_path
            # This check is important to prevent directory traversal with relative paths.
            # A file could be in permanent_storage_dir or potentially other subdirs of local_storage_base_path
            # if storage_path_for_record was constructed differently.
            # For now, let's assume it must be under local_storage_base_path.
            if not str(abs_file_path).startswith(str(self.local_storage_base_path.resolve())):
                 logger.error(f"Attempt to delete file outside designated storage area: '{storage_path_or_key}' resolved to '{abs_file_path}'. Deletion aborted.")
                 return False

            if abs_file_path.is_file():
                os.remove(abs_file_path)
                logger.info(f"Local file '{abs_file_path}' deleted successfully.")
                parent_dir = abs_file_path.parent
                # Only remove parent if it's within permanent_storage_dir and not permanent_storage_dir itself
                if parent_dir != self.permanent_storage_dir and str(parent_dir).startswith(str(self.permanent_storage_dir.resolve())):
                    if not any(parent_dir.iterdir()):
                        try:
                            parent_dir.rmdir()
                            logger.info(f"Empty parent directory '{parent_dir}' deleted.")
                        except OSError as e_rmdir:
                            logger.warning(f"Could not remove empty parent directory '{parent_dir}': {e_rmdir}")
                return True
            else:
                logger.warning(f"Local file not found at '{abs_file_path}' for deletion based on path '{storage_path_or_key}'.")
                return False
        except Exception as e:
            logger.error(f"Error deleting local file '{storage_path_or_key}': {e}", exc_info=True)
            return False

logger.info("FileUploadService class defined.")
