# backend/app/src/repositories/files/file_record_repository.py

"""
Repository for FileRecord entities.
Provides CRUD operations and specific methods for managing file metadata.
"""

import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.src.models.files.file import FileRecord
from backend.app.src.schemas.files.file import FileRecordCreate
from pydantic import BaseModel as PydanticBaseModel
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class FileRecordUpdateSchema(PydanticBaseModel):
    original_filename: Optional[str] = None
    is_public: Optional[bool] = None

class FileRecordRepository(BaseRepository[FileRecord, FileRecordCreate, FileRecordUpdateSchema]):
    """
    Repository for managing FileRecord metadata.
    """

    def __init__(self):
        super().__init__(FileRecord)

    async def get_by_stored_filename(self, db: AsyncSession, *, stored_filename: str) -> Optional[FileRecord]:
        """
        Retrieves a file record by its unique stored filename.

        Args:
            db: The SQLAlchemy asynchronous database session.
            stored_filename: The filename used for storage (e.g., UUID-based name).

        Returns:
            The FileRecord object if found, otherwise None.
        """
        statement = select(self.model).where(self.model.stored_filename == stored_filename) # type: ignore[attr-defined]
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_files_for_uploader(
        self, db: AsyncSession, *, uploader_user_id: int, skip: int = 0, limit: int = 100
    ) -> List[FileRecord]:
        """
        Retrieves all file records uploaded by a specific user.

        Args:
            db: The SQLAlchemy asynchronous database session.
            uploader_user_id: The ID of the user who uploaded the files.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of FileRecord objects.
        """
        statement = (
            select(self.model)
            .where(self.model.uploader_user_id == uploader_user_id) # type: ignore[attr-defined]
            .order_by(self.model.created_at.desc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_files_by_visibility(
        self, db: AsyncSession, *, is_public: bool, skip: int = 0, limit: int = 100
    ) -> List[FileRecord]:
        """
        Retrieves file records based on their public visibility status.

        Args:
            db: The SQLAlchemy asynchronous database session.
            is_public: Boolean flag to filter by public (True) or private (False) files.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of FileRecord objects.
        """
        statement = (
            select(self.model)
            .where(self.model.is_public == is_public) # type: ignore[attr-defined]
            .order_by(self.model.created_at.desc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_by_filepath_or_url(self, db: AsyncSession, *, filepath_or_url: str) -> Optional[FileRecord]:
        """
        Retrieves a file record by its unique filepath_or_url.
        This assumes filepath_or_url is unique if used as a lookup key.

        Args:
            db: The SQLAlchemy asynchronous database session.
            filepath_or_url: The path or URL of the file.

        Returns:
            The FileRecord object if found, otherwise None.
        """
        statement = select(self.model).where(self.model.filepath_or_url == filepath_or_url) # type: ignore[attr-defined]
        result = await db.execute(statement)
        return result.scalar_one_or_none()
