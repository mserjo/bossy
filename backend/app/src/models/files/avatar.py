# backend/app/src/models/files/avatar.py

"""
SQLAlchemy model for User Avatars, linking a User to their avatar FileRecord.
This acts as a one-to-one (or one-to-current-one) mapping.
"""

import logging
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone # Added timezone for __main__

from sqlalchemy import ForeignKey, Boolean, Integer # Added Integer for FKs
from sqlalchemy.orm import Mapped, mapped_column, relationship
# from sqlalchemy.sql import func # Not strictly needed here

from backend.app.src.models.base import BaseModel # Avatars are simpler entities

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.files.file import FileRecord

class UserAvatar(BaseModel):
    """
    Represents the association of a User with their avatar FileRecord.
    Typically, a user has one active avatar.

    Attributes:
        user_id (int): Foreign key to the user. This is also the primary key, ensuring one avatar record per user.
        file_record_id (int): Foreign key to the FileRecord that is the user's avatar.
        is_active (bool): If multiple avatars were ever allowed historically, this could mark the current one.
                        For a strict one-to-one, this might be redundant but can be useful for future flexibility.
        # `id` from BaseModel is NOT used as the primary key for this table. `user_id` is.
        # `created_at`, `updated_at` are inherited from BaseModel.
    """
    __tablename__ = "user_avatars"

    # user_id is the primary key to enforce one avatar record per user.
    # BaseModel's 'id' is effectively shadowed by this explicit PK.
    # If you wanted to use BaseModel's 'id' as the PK, then user_id would be a unique FK.
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True, index=True, comment="FK to the user. This is the PK for a one-to-one mapping.")
    file_record_id: Mapped[int] = mapped_column(Integer, ForeignKey("file_records.id"), unique=True, nullable=False, index=True, comment="FK to the FileRecord that is the avatar. Unique ensures a file is only one user's current active avatar.")

    # is_active might be useful if users could upload multiple avatars but only one is current.
    # For a simple one-to-one, this field might be less critical if changing avatar means replacing the record or file_record_id.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="Is this the currently active avatar for the user?")

    # --- Relationships ---
    # This establishes a one-to-one relationship from User to UserAvatar,
    # and via UserAvatar, to a specific FileRecord.
    user: Mapped["User"] = relationship(back_populates="avatar") # Assumes User.avatar is defined with uselist=False and back_populates="user"
    file_record: Mapped["FileRecord"] = relationship(back_populates="user_avatar_association") # Assumes FileRecord.user_avatar_association is defined with back_populates="file_record"

    def __repr__(self) -> str:
        # Since user_id is PK, BaseModel's id is not used here as the primary identifier.
        return f"<UserAvatar(user_id={self.user_id}, file_record_id={self.file_record_id}, active={self.is_active})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- UserAvatar Model --- Demonstration")

    # Example UserAvatar instance
    # Assume User id=1 and FileRecord id=1 exist
    avatar_link = UserAvatar(
        user_id=1,
        file_record_id=1,
        is_active=True
    )
    # This model uses user_id as PK, so BaseModel's 'id' is not the main identifier.
    # For demonstration, we'll show how created_at/updated_at from BaseModel would still exist.
    # The 'id' field from BaseModel would also exist but would not be the PK.
    # If we want to avoid the separate 'id' column from BaseModel entirely for this table,
    # UserAvatar would need to not inherit 'id' (e.g. inherit from a Base without 'id', or define all columns here).
    # For now, assume BaseModel's 'id' is present but not the PK.

    # Manually setting created_at/updated_at for demo as they come from BaseModel
    avatar_link.created_at = datetime.now(timezone.utc)
    avatar_link.updated_at = datetime.now(timezone.utc)
    # If BaseModel's 'id' column is still present (not shadowed by user_id as PK, which depends on SQLAlchemy version/behavior for inherited PKs):
    # avatar_link.id = 101 # Example of the surrogate key from BaseModel if it were still active and distinct from user_id as PK.

    logger.info(f"Example UserAvatar: {avatar_link!r}")
    logger.info(f"  User ID (PK): {avatar_link.user_id}")
    logger.info(f"  File Record ID: {avatar_link.file_record_id}")
    logger.info(f"  Is Active: {avatar_link.is_active}")
    logger.info(f"  Record Created At (from BaseModel): {avatar_link.created_at.isoformat() if avatar_link.created_at else 'N/A'}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"UserAvatar attributes (conceptual table columns): {[c.name for c in UserAvatar.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
