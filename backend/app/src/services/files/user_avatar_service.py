# backend/app/src/services/files/user_avatar_service.py
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.files.avatar import UserAvatar # SQLAlchemy UserAvatar model
from app.src.models.files.file import FileRecord # To link to the actual file
from app.src.models.auth.user import User # For user context

from app.src.schemas.files.avatar import ( # Pydantic Schemas
    UserAvatarCreate, # Input when setting an avatar (just file_id) - Not directly used as param type, but conceptual
    UserAvatarUpdate, # For changing is_active
    UserAvatarResponse
)
from app.src.schemas.files.file import FileRecordResponse # For nested file details in response

# from app.src.services.files.file_record_service import FileRecordService # If needing to validate FileRecord further

# Initialize logger for this module
logger = logging.getLogger(__name__)

class UserAvatarService(BaseService):
    """
    Service for managing user avatars.
    Handles linking users to their avatar images (FileRecords) and managing
    which avatar is currently active.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("UserAvatarService initialized.")

    async def set_user_avatar(
        self,
        user_id: UUID,
        file_id: UUID,
        set_by_user_id: Optional[UUID] = None
    ) -> UserAvatarResponse:
        actual_set_by_user_id = set_by_user_id or user_id
        logger.debug(f"User ID '{actual_set_by_user_id}' attempting to set avatar for user ID '{user_id}' using file ID '{file_id}'.")

        user = await self.db_session.get(User, user_id)
        if not user: raise ValueError(f"User with ID '{user_id}' not found.")

        file_record = await self.db_session.get(FileRecord, file_id)
        if not file_record: raise ValueError(f"FileRecord with ID '{file_id}' not found.")

        if hasattr(file_record, 'mime_type') and not str(file_record.mime_type).startswith("image/"):
            logger.warning(f"File ID '{file_id}' (MIME: {file_record.mime_type}) is not an image. Cannot set as avatar.")
            raise ValueError(f"File '{file_record.file_name}' is not a valid image for an avatar.")

        # Deactivate existing active avatars for this user
        update_values = {"is_active": False, "updated_at": datetime.now(timezone.utc)}
        if hasattr(UserAvatar, 'updated_by_user_id') and actual_set_by_user_id:
            update_values["updated_by_user_id"] = actual_set_by_user_id

        stmt_deactivate = (
            UserAvatar.__table__.update()
            .where(UserAvatar.user_id == user_id, UserAvatar.is_active == True)
            .values(**update_values) # type: ignore
        )
        await self.db_session.execute(stmt_deactivate)

        stmt_existing_link = select(UserAvatar).where(
            UserAvatar.user_id == user_id,
            UserAvatar.file_id == file_id
        )
        existing_avatar_link = (await self.db_session.execute(stmt_existing_link)).scalar_one_or_none()

        new_avatar_link_db: UserAvatar
        if existing_avatar_link:
            logger.info(f"Reactivating existing avatar link between user ID '{user_id}' and file ID '{file_id}'.")
            existing_avatar_link.is_active = True
            if hasattr(existing_avatar_link, 'updated_at'):
                existing_avatar_link.updated_at = datetime.now(timezone.utc)
            if hasattr(existing_avatar_link, 'updated_by_user_id') and actual_set_by_user_id:
                existing_avatar_link.updated_by_user_id = actual_set_by_user_id
            new_avatar_link_db = existing_avatar_link
        else:
            logger.info(f"Creating new avatar link for user ID '{user_id}' with file ID '{file_id}'.")
            create_data = {
                "user_id": user_id,
                "file_id": file_id,
                "is_active": True
            }
            if hasattr(UserAvatar, 'created_by_user_id') and actual_set_by_user_id:
                create_data['created_by_user_id'] = actual_set_by_user_id
            if hasattr(UserAvatar, 'updated_by_user_id') and actual_set_by_user_id: # Also set updated_by on creation
                create_data['updated_by_user_id'] = actual_set_by_user_id

            new_avatar_link_db = UserAvatar(**create_data) # type: ignore
            self.db_session.add(new_avatar_link_db)

        try:
            await self.commit()
            refresh_attrs = ['user', 'file']
            if hasattr(new_avatar_link_db, 'user') and new_avatar_link_db.user and hasattr(User, 'user_type'):
                await self.db_session.refresh(new_avatar_link_db.user, attribute_names=['user_type'])
            if hasattr(new_avatar_link_db, 'file') and new_avatar_link_db.file and hasattr(FileRecord, 'uploader_user'):
                 await self.db_session.refresh(new_avatar_link_db.file, attribute_names=['uploader_user'])
            await self.db_session.refresh(new_avatar_link_db, attribute_names=refresh_attrs)

        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error setting avatar for user ID '{user_id}': {e}", exc_info=True)
            raise ValueError(f"Could not set avatar due to a data conflict: {e}")

        logger.info(f"Avatar (File ID: '{file_id}') successfully set as active for user ID '{user_id}'. Link ID: {new_avatar_link_db.id}")
        # return UserAvatarResponse.model_validate(new_avatar_link_db) # Pydantic v2
        return UserAvatarResponse.from_orm(new_avatar_link_db) # Pydantic v1

    async def get_active_user_avatar(self, user_id: UUID) -> Optional[UserAvatarResponse]:
        logger.debug(f"Attempting to retrieve active avatar for user ID: {user_id}")

        stmt = select(UserAvatar).options(
            selectinload(UserAvatar.user).load_only(User.id, User.username) if hasattr(UserAvatar, 'user') else None,
            selectinload(UserAvatar.file).options(
                selectinload(FileRecord.uploader_user).load_only(User.id, User.username) if hasattr(FileRecord, 'uploader_user') else None
            ) if hasattr(UserAvatar, 'file') else None
        ).where(
            UserAvatar.user_id == user_id,
            UserAvatar.is_active == True
        )
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))

        active_avatar_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if active_avatar_db:
            if hasattr(active_avatar_db, 'file') and not active_avatar_db.file:
                logger.error(f"Active avatar link ID '{active_avatar_db.id}' for user '{user_id}' has no associated file record. Data inconsistency.")
                return None
            logger.info(f"Active avatar found for user ID '{user_id}' (File ID: {active_avatar_db.file_id if hasattr(active_avatar_db, 'file_id') else 'N/A'}).")
            # return UserAvatarResponse.model_validate(active_avatar_db) # Pydantic v2
            return UserAvatarResponse.from_orm(active_avatar_db) # Pydantic v1

        logger.info(f"No active avatar found for user ID '{user_id}'.")
        return None

    async def list_user_avatars(self, user_id: UUID, skip: int = 0, limit: int = 10) -> List[UserAvatarResponse]:
        logger.debug(f"Listing all avatars for user ID: {user_id}, skip={skip}, limit={limit}")

        stmt = select(UserAvatar).options(
            selectinload(UserAvatar.user).load_only(User.id, User.username) if hasattr(UserAvatar, 'user') else None,
            selectinload(UserAvatar.file).options(
                selectinload(FileRecord.uploader_user).load_only(User.id, User.username) if hasattr(FileRecord, 'uploader_user') else None
            ) if hasattr(UserAvatar, 'file') else None
        ).where(UserAvatar.user_id == user_id) \
         .order_by(UserAvatar.is_active.desc(), UserAvatar.created_at.desc()) \
         .offset(skip).limit(limit)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))

        avatars_db = (await self.db_session.execute(stmt)).scalars().all()

        # response_list = [UserAvatarResponse.model_validate(ua) for ua in avatars_db] # Pydantic v2
        response_list = [UserAvatarResponse.from_orm(ua) for ua in avatars_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} avatar records for user ID '{user_id}'.")
        return response_list

    async def deactivate_user_avatar(self, user_avatar_id: UUID, current_user_id: UUID) -> bool:
        logger.debug(f"User ID '{current_user_id}' attempting to deactivate user_avatar link ID: {user_avatar_id}")

        user_avatar_db = await self.db_session.get(UserAvatar, user_avatar_id)
        if not user_avatar_db:
            logger.warning(f"UserAvatar link ID '{user_avatar_id}' not found.")
            return False

        if user_avatar_db.user_id != current_user_id:
            logger.error(f"User ID '{current_user_id}' not authorized to deactivate UserAvatar link ID '{user_avatar_id}'.")
            raise ValueError("Not authorized to deactivate this avatar link.")

        if not user_avatar_db.is_active:
            logger.info(f"UserAvatar link ID '{user_avatar_id}' is already inactive.")
            return True

        user_avatar_db.is_active = False
        if hasattr(user_avatar_db, 'updated_by_user_id'):
            user_avatar_db.updated_by_user_id = current_user_id # type: ignore
        if hasattr(user_avatar_db, 'updated_at'):
            user_avatar_db.updated_at = datetime.now(timezone.utc) # type: ignore

        self.db_session.add(user_avatar_db)
        await self.commit()
        logger.info(f"UserAvatar link ID '{user_avatar_id}' for user ID '{user_avatar_db.user_id}' deactivated.")
        return True

logger.info("UserAvatarService class defined.")
