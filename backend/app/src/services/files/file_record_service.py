# backend/app/src/services/files/file_record_service.py
import logging
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.files.file import FileRecord # SQLAlchemy FileRecord model
from app.src.models.auth.user import User # For uploader_user relationship
from app.src.models.groups.group import Group # For group relationship

from app.src.schemas.files.file import ( # Pydantic Schemas
    FileRecordCreate,
    FileRecordUpdate, # For updating metadata like name, description
    FileRecordResponse
)
# FileUploadService might be needed for deleting actual file from storage
# from .file_upload_service import FileUploadService # Avoid circular if possible

# Initialize logger for this module
logger = logging.getLogger(__name__)

class FileRecordService(BaseService):
    """
    Service for managing file metadata records (FileRecord entities).
    Handles CRUD operations for these records. Actual file storage/deletion
    is typically coordinated with a FileUploadService or storage utility.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("FileRecordService initialized.")

    async def get_file_record_by_id(self, file_id: UUID) -> Optional[FileRecordResponse]:
        """Retrieves a file record by its ID, with related uploader/group loaded."""
        logger.debug(f"Attempting to retrieve file record by ID: {file_id}")

        stmt = select(FileRecord).options(
            selectinload(FileRecord.uploader_user).options(selectinload(User.user_type)) if hasattr(FileRecord, 'uploader_user') else None,
            selectinload(FileRecord.group) if hasattr(FileRecord, 'group') else None
        ).where(FileRecord.id == file_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))

        record_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if record_db:
            logger.info(f"File record with ID '{file_id}' (Name: '{record_db.file_name}') found.")
            # return FileRecordResponse.model_validate(record_db) # Pydantic v2
            return FileRecordResponse.from_orm(record_db) # Pydantic v1
        logger.info(f"File record with ID '{file_id}' not found.")
        return None

    async def create_file_record(self, record_data: FileRecordCreate) -> Optional[FileRecordResponse]: # Return Optional
        """
        Creates a new file record.
        This is typically called *after* a file has been successfully uploaded to storage,
        and `record_data` includes the `storage_path` and other metadata.
        """
        logger.debug(f"Attempting to create new file record for file: '{record_data.file_name}'")

        if record_data.uploader_user_id and hasattr(FileRecord, 'uploader_user_id'):
            if not await self.db_session.get(User, record_data.uploader_user_id):
                raise ValueError(f"Uploader user with ID '{record_data.uploader_user_id}' not found.")
        if record_data.group_id and hasattr(FileRecord, 'group_id'):
            if not await self.db_session.get(Group, record_data.group_id):
                raise ValueError(f"Group with ID '{record_data.group_id}' not found.")

        if hasattr(FileRecord, 'storage_path') and hasattr(record_data, 'storage_path'):
            stmt_path_check = select(FileRecord.id).where(FileRecord.storage_path == record_data.storage_path) # Select only ID
            if (await self.db_session.execute(stmt_path_check)).scalar_one_or_none():
                logger.warning(f"File record with storage_path '{record_data.storage_path}' already exists.")
                raise ValueError(f"File record with storage_path '{record_data.storage_path}' already exists.")

        record_db_data = record_data.dict()

        new_record_db = FileRecord(**record_db_data)

        self.db_session.add(new_record_db)
        try:
            await self.commit()
            # Refresh to load relationships for the response
            refresh_attrs = []
            if hasattr(FileRecord, 'uploader_user'): refresh_attrs.append('uploader_user')
            if hasattr(FileRecord, 'group'): refresh_attrs.append('group')
            if refresh_attrs: await self.db_session.refresh(new_record_db, attribute_names=refresh_attrs)
            else: await self.db_session.refresh(new_record_db)

            created_record = await self.get_file_record_by_id(new_record_db.id) # Use get for consistent response
            if created_record:
                logger.info(f"File record '{new_record_db.file_name}' (ID: {new_record_db.id}) created successfully.")
                return created_record
            else: # Should not happen
                logger.error(f"Failed to retrieve newly created file record ID {new_record_db.id} after commit.")
                return None
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error creating file record '{record_data.file_name}': {e}", exc_info=True)
            raise ValueError(f"Could not create file record due to a data conflict: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Unexpected error creating file record '{record_data.file_name}': {e}", exc_info=True)
            raise

    async def update_file_record_metadata(
        self,
        file_id: UUID,
        metadata_update_data: FileRecordUpdate,
        current_user_id: Optional[UUID] = None # For audit, made optional
    ) -> Optional[FileRecordResponse]:
        logger.debug(f"Attempting to update metadata for file record ID: {file_id} by user ID: {current_user_id or 'System'}")

        record_db = await self.db_session.get(FileRecord, file_id)
        if not record_db:
            logger.warning(f"File record ID '{file_id}' not found for metadata update.")
            return None

        update_data = metadata_update_data.dict(exclude_unset=True)

        updated_fields_count = 0
        for field, value in update_data.items():
            if field in ['id', 'storage_path', 'uploader_user_id', 'created_at', 'updated_at', 'group_id']: # Added group_id to restricted
                logger.warning(f"Attempt to update restricted field '{field}' for file record ID '{file_id}' was ignored.")
                continue
            if hasattr(record_db, field):
                setattr(record_db, field, value)
                updated_fields_count +=1
            else:
                logger.warning(f"Field '{field}' not found on FileRecord model for update of record ID '{file_id}'.")

        if updated_fields_count == 0 and not any(key in update_data for key in ['file_name', 'description', 'metadata']): # Check if any actual data field was in input
            logger.info(f"No updatable metadata fields provided or no changes needed for file record ID '{file_id}'.")
            return await self.get_file_record_by_id(file_id)

        if hasattr(record_db, 'updated_by_user_id') and current_user_id:
            record_db.updated_by_user_id = current_user_id
        if hasattr(record_db, 'updated_at'):
            record_db.updated_at = datetime.now(timezone.utc)

        self.db_session.add(record_db)
        try:
            await self.commit()
            logger.info(f"Metadata for file record ID '{file_id}' updated by user ID '{current_user_id or 'System'}'.")
            return await self.get_file_record_by_id(file_id)
        except Exception as e:
            await self.rollback()
            logger.error(f"Error updating file record metadata for ID '{file_id}': {e}", exc_info=True)
            raise


    async def delete_file_record(
        self,
        file_id: UUID,
        current_user_id: Optional[UUID] = None, # For audit, made optional
        delete_from_storage: bool = True
    ) -> bool:
        logger.debug(f"User ID '{current_user_id or 'System'}' attempting to delete file record ID: {file_id}. Delete from storage: {delete_from_storage}")

        record_db = await self.db_session.get(FileRecord, file_id)
        if not record_db:
            logger.warning(f"File record ID '{file_id}' not found for deletion.")
            return False

        storage_path_to_delete = getattr(record_db, 'storage_path', None)

        await self.db_session.delete(record_db)
        try:
            await self.commit()
            logger.info(f"File record ID '{file_id}' (Path: {storage_path_to_delete}) deleted from database by '{current_user_id or 'System'}'.")
        except Exception as e: # Catch issues on DB delete commit
            await self.rollback()
            logger.error(f"Error committing deletion of file record ID '{file_id}' from database: {e}", exc_info=True)
            return False # DB delete failed, so don't proceed to storage deletion

        if delete_from_storage and storage_path_to_delete:
            logger.info(f"Proceeding to delete actual file from storage for path: {storage_path_to_delete}")
            # from .file_upload_service import FileUploadService
            # upload_service = FileUploadService(self.db_session)
            # delete_success = await upload_service.delete_actual_file(storage_path_to_delete)
            # if not delete_success:
            #     logger.warning(f"Failed to delete actual file at '{storage_path_to_delete}' from storage. DB record was already deleted.")
            logger.warning(f"[Placeholder] Actual file deletion from storage for path '{storage_path_to_delete}' needs implementation.")
            # delete_success_placeholder = True # Assume success for now
            # if not delete_success_placeholder:
            #     pass # Logged already

        return True

    async def list_file_records(
        self,
        uploader_user_id: Optional[UUID] = None,
        group_id: Optional[UUID] = None,
        mime_type_pattern: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[FileRecordResponse]:
        logger.debug(f"Listing file records: user={uploader_user_id}, group={group_id}, mime_pattern='{mime_type_pattern}'")

        stmt = select(FileRecord).options(
            selectinload(FileRecord.uploader_user).options(selectinload(User.user_type)) if hasattr(FileRecord, 'uploader_user') else None,
            selectinload(FileRecord.group) if hasattr(FileRecord, 'group') else None
        )
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))


        conditions = []
        if uploader_user_id and hasattr(FileRecord, 'uploader_user_id'):
            conditions.append(FileRecord.uploader_user_id == uploader_user_id)
        if group_id and hasattr(FileRecord, 'group_id'):
            conditions.append(FileRecord.group_id == group_id)
        if mime_type_pattern and hasattr(FileRecord, 'mime_type'):
            conditions.append(FileRecord.mime_type.ilike(mime_type_pattern)) # type: ignore

        if conditions:
            stmt = stmt.where(*conditions)

        stmt = stmt.order_by(FileRecord.created_at.desc()).offset(skip).limit(limit)

        records_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # response_list = [FileRecordResponse.model_validate(r) for r in records_db] # Pydantic v2
        response_list = [FileRecordResponse.from_orm(r) for r in records_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} file records.")
        return response_list

logger.info("FileRecordService class defined.")
