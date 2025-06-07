# backend/app/src/models/files/file.py

"""
SQLAlchemy model for File Records, storing metadata about uploaded files.
"""

import logging
from typing import Optional, TYPE_CHECKING, List # Added List for UserAvatar back_populates
from datetime import datetime, timezone # Added timezone for __main__
from enum import Enum as PythonEnum # For native Python Enum if used in SQLAlchemyEnum

from sqlalchemy import String, Integer, Boolean, ForeignKey, BigInteger, Enum as SQLAlchemyEnum, Text # Added BigInteger for size, Integer for FK, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
# from sqlalchemy.sql import func # Not strictly needed here as created_at from BaseModel has server_default

from backend.app.src.models.base import BaseModel

# Configure logger for this module
logger = logging.getLogger(__name__)

class FileStorageTypeEnum(PythonEnum): # Changed to inherit from PythonEnum
    """ Defines where the file is physically stored. Using native Python Enum for SQLAlchemyEnum. """
    LOCAL = "local"         # Stored on the local filesystem of the server.
    S3 = "s3"             # Stored in an AWS S3 bucket or compatible service.
    # AZURE_BLOB = "azure_blob" # Example for Azure Blob Storage
    # GOOGLE_CLOUD_STORAGE = "google_cloud_storage" # Example for GCS
    OTHER = "other"         # Other storage mechanism.

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.files.avatar import UserAvatar # For relationship

class FileRecord(BaseModel):
    """
    Represents a record of an uploaded file, storing its metadata.
    The actual file is stored elsewhere (e.g., local filesystem, S3).

    Attributes:
        uploader_user_id (Optional[int]): Foreign key to the user who uploaded the file.
                                       Null if uploaded by an anonymous user or system process.
        original_filename (str): The original name of the file as uploaded by the user.
        stored_filename (str): The name used to store the file on the server/storage (e.g., a UUID-based name to avoid collisions).
        filepath_or_url (str): The absolute local path or the full URL to access the file.
        mime_type (str): The MIME type of the file (e.g., 'image/jpeg', 'application/pdf').
        size_bytes (int): The size of the file in bytes.
        storage_type (FileStorageTypeEnum): Indicates where the file is stored (e.g., local, S3).
        is_public (bool): Whether the file is publicly accessible or requires authentication/authorization.
        # `id`, `created_at` (upload_timestamp), `updated_at` from BaseModel.
        # `created_at` can serve as the upload_timestamp.
    """
    __tablename__ = "file_records"

    uploader_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="FK to the user who uploaded the file (if any)")

    original_filename: Mapped[str] = mapped_column(String(512), nullable=False, comment="Original name of the file as uploaded")
    stored_filename: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True, comment="Filename used for storage (e.g., UUID-based to prevent collisions)")

    filepath_or_url: Mapped[str] = mapped_column(Text, nullable=False, comment="Local path or full URL to the file") # Changed to Text for potentially very long URLs/paths

    mime_type: Mapped[str] = mapped_column(String(255), nullable=False, comment="MIME type of the file (e.g., 'image/jpeg')")
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="Size of the file in bytes") # BigInteger for potentially large files

    storage_type: Mapped[FileStorageTypeEnum] = mapped_column(
        SQLAlchemyEnum(FileStorageTypeEnum, name="filestoragetypeenum", native_enum=False, create_constraint=True),
        nullable=False,
        default=FileStorageTypeEnum.LOCAL,
        comment="Indicates where the file is physically stored (e.g., local, s3)"
    )

    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="Is this file publicly accessible without specific auth checks?")
    # hash_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, comment="SHA256 hash of the file content for integrity/deduplication")

    # --- Relationships ---
    uploader: Mapped[Optional["User"]] = relationship(foreign_keys=[uploader_user_id]) # One-way or add back_populates to User

    # This defines the one-to-one relationship from FileRecord to UserAvatar
    # UserAvatar will have a file_record_id that points back here.
    user_avatar_association: Mapped[Optional["UserAvatar"]] = relationship(back_populates="file_record")


    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<FileRecord(id={id_val}, name='{self.original_filename}', stored_as='{self.stored_filename}', type='{self.mime_type}')>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- FileRecord Model --- Demonstration")

    # Example FileRecord instance
    # Assume User id=1 exists
    file_rec1 = FileRecord(
        uploader_user_id=1,
        original_filename="profile_picture.jpg",
        stored_filename="f47ac10b-58cc-4372-a567-0e02b2c3d479.jpg",
        filepath_or_url="/uploads/avatars/f47ac10b-58cc-4372-a567-0e02b2c3d479.jpg",
        mime_type="image/jpeg",
        size_bytes=1024 * 120, # 120KB
        storage_type=FileStorageTypeEnum.LOCAL,
        is_public=False
    )
    file_rec1.id = 1 # Simulate ORM-set ID
    file_rec1.created_at = datetime.now(timezone.utc)
    file_rec1.updated_at = datetime.now(timezone.utc)

    logger.info(f"Example FileRecord: {file_rec1!r}")
    logger.info(f"  Original Name: {file_rec1.original_filename}")
    logger.info(f"  Storage Type: {file_rec1.storage_type.value if isinstance(file_rec1.storage_type, PythonEnum) else file_rec1.storage_type}") # Check against PythonEnum
    logger.info(f"  Size: {file_rec1.size_bytes / 1024:.2f} KB")
    logger.info(f"  Is Public: {file_rec1.is_public}")
    logger.info(f"  Created At: {file_rec1.created_at.isoformat() if file_rec1.created_at else 'N/A'}")


    s3_file_rec = FileRecord(
        original_filename="annual_report.pdf",
        stored_filename="report_archive/2023_annual_report_final.pdf",
        filepath_or_url="s3://my-kudos-bucket/report_archive/2023_annual_report_final.pdf",
        mime_type="application/pdf",
        size_bytes=1024 * 1024 * 5, # 5MB
        storage_type=FileStorageTypeEnum.S3,
        is_public=False
    )
    s3_file_rec.id = 2
    logger.info(f"Example S3 FileRecord: {s3_file_rec!r}")
    logger.info(f"  File Path/URL: {s3_file_rec.filepath_or_url}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"FileRecord attributes (conceptual table columns): {[c.name for c in FileRecord.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
