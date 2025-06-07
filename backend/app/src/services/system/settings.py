# backend/app/src/services/system/settings.py
import logging
from typing import List, Optional, Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
# Assuming direct ORM interaction for now, repository would be an alternative
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload # If there are relationships to load

from app.src.services.base import BaseService
from app.src.models.system.settings import SystemSetting # Assuming this is the SQLAlchemy model
from app.src.schemas.system.settings import ( # Assuming these are the Pydantic schemas
    SystemSettingCreate,
    SystemSettingUpdate,
    SystemSettingResponse,
)
# from app.src.repositories.system.settings_repository import SystemSettingRepository # Placeholder

# Initialize logger for this module
logger = logging.getLogger(__name__)

class SystemSettingService(BaseService): # If using repo: BaseService[SystemSettingRepository]
    """
    Service for managing system-wide settings.
    Allows retrieving, creating, and updating settings that govern application behavior.
    """

    # If using repository pattern:
    # def __init__(self, db_session: AsyncSession, settings_repo: SystemSettingRepository):
    #     super().__init__(db_session, repo=settings_repo)
    #     logger.info("SystemSettingService initialized with SystemSettingRepository.")

    # If not using repository pattern (direct DB interaction via session):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("SystemSettingService initialized.")


    async def get_setting_by_key(self, key: str) -> Optional[SystemSettingResponse]:
        """
        Retrieves a specific system setting by its key.

        Args:
            key (str): The unique key of the system setting.

        Returns:
            Optional[SystemSettingResponse]: The system setting if found, otherwise None.
        """
        logger.debug(f"Attempting to retrieve system setting with key: {key}")
        # Using direct session interaction:
        stmt = select(SystemSetting).where(SystemSetting.key == key)
        result = await self.db_session.execute(stmt)
        setting_db = result.scalar_one_or_none()

        if setting_db:
            logger.info(f"System setting with key '{key}' found.")
            # return SystemSettingResponse.model_validate(setting_db) # Pydantic v2
            return SystemSettingResponse.from_orm(setting_db) # Pydantic v1
        else:
            logger.info(f"System setting with key '{key}' not found.")
            return None

    async def get_all_settings(self, skip: int = 0, limit: int = 100) -> List[SystemSettingResponse]:
        """
        Retrieves a list of all system settings, with pagination.

        Args:
            skip (int): Number of settings to skip.
            limit (int): Maximum number of settings to return.

        Returns:
            List[SystemSettingResponse]: A list of system settings.
        """
        logger.debug(f"Attempting to retrieve all system settings with skip={skip}, limit={limit}")
        stmt = select(SystemSetting).offset(skip).limit(limit).order_by(SystemSetting.key)
        result = await self.db_session.execute(stmt)
        settings_db = result.scalars().all()

        # response_list = [SystemSettingResponse.model_validate(s) for s in settings_db] # Pydantic v2
        response_list = [SystemSettingResponse.from_orm(s) for s in settings_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} system settings.")
        return response_list

    async def create_setting(self, setting_data: SystemSettingCreate) -> SystemSettingResponse:
        """
        Creates a new system setting.
        Ensures that a setting with the same key does not already exist.

        Args:
            setting_data (SystemSettingCreate): Data for the new system setting.

        Returns:
            SystemSettingResponse: The created system setting.

        Raises:
            ValueError: If a setting with the same key already exists.
        """
        logger.debug(f"Attempting to create new system setting with key: {setting_data.key}")
        existing_setting = await self.get_setting_by_key(setting_data.key)
        if existing_setting:
            logger.warning(f"System setting with key '{setting_data.key}' already exists. Creation aborted.")
            raise ValueError(f"System setting with key '{setting_data.key}' already exists.")

        # new_setting_db = SystemSetting(**setting_data.model_dump()) # Pydantic v2
        new_setting_db = SystemSetting(**setting_data.dict()) # Pydantic v1

        self.db_session.add(new_setting_db)
        await self.commit() # Commits session
        await self.db_session.refresh(new_setting_db) # Refresh to get DB-generated fields like id, created_at

        logger.info(f"System setting with key '{new_setting_db.key}' created successfully with ID: {new_setting_db.id}")
        # return SystemSettingResponse.model_validate(new_setting_db) # Pydantic v2
        return SystemSettingResponse.from_orm(new_setting_db) # Pydantic v1

    async def update_setting(self, setting_id: UUID, setting_update_data: SystemSettingUpdate) -> Optional[SystemSettingResponse]:
        """
        Updates an existing system setting by its ID.

        Args:
            setting_id (UUID): The ID of the system setting to update.
            setting_update_data (SystemSettingUpdate): Data to update the setting with.
                                                        Fields not present or None will be ignored.

        Returns:
            Optional[SystemSettingResponse]: The updated system setting, or None if not found.

        Raises:
            ValueError: If attempting to update the key to one that already exists for another setting.
        """
        logger.debug(f"Attempting to update system setting with ID: {setting_id}")

        stmt = select(SystemSetting).where(SystemSetting.id == setting_id)
        result = await self.db_session.execute(stmt)
        setting_db = result.scalar_one_or_none()

        if not setting_db:
            logger.warning(f"System setting with ID '{setting_id}' not found for update.")
            return None

        # update_data = setting_update_data.model_dump(exclude_unset=True) # Pydantic v2
        update_data = setting_update_data.dict(exclude_unset=True) # Pydantic v1

        if 'key' in update_data and update_data['key'] != setting_db.key:
            existing_key_setting = await self.get_setting_by_key(update_data['key'])
            if existing_key_setting and existing_key_setting.id != setting_id:
                logger.warning(f"Cannot update key for setting ID '{setting_id}' to '{update_data['key']}' as it's used by setting ID '{existing_key_setting.id}'.")
                raise ValueError(f"Another system setting with key '{update_data['key']}' already exists.")

        for field, value in update_data.items():
            setattr(setting_db, field, value)

        self.db_session.add(setting_db) # Add to session to mark as dirty
        await self.commit()
        await self.db_session.refresh(setting_db)

        logger.info(f"System setting with ID '{setting_id}' updated successfully.")
        # return SystemSettingResponse.model_validate(setting_db) # Pydantic v2
        return SystemSettingResponse.from_orm(setting_db) # Pydantic v1

    async def delete_setting(self, setting_id: UUID) -> bool:
        """
        Deletes a system setting by its ID.

        Args:
            setting_id (UUID): The ID of the system setting to delete.

        Returns:
            bool: True if deletion was successful, False if the setting was not found.
        """
        logger.debug(f"Attempting to delete system setting with ID: {setting_id}")
        stmt = select(SystemSetting).where(SystemSetting.id == setting_id)
        result = await self.db_session.execute(stmt)
        setting_db = result.scalar_one_or_none()

        if not setting_db:
            logger.warning(f"System setting with ID '{setting_id}' not found for deletion.")
            return False

        await self.db_session.delete(setting_db)
        await self.commit()
        logger.info(f"System setting with ID '{setting_id}' (key: {setting_db.key}) deleted successfully.")
        return True

    async def get_setting_value(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Convenience method to get the deserialized value of a setting by key.

        Args:
            key (str): The key of the setting.
            default (Optional[Any]): Default value to return if setting is not found.

        Returns:
            Optional[Any]: The deserialized value of the setting or the default.
        """
        setting = await self.get_setting_by_key(key)
        if setting:
            # The 'value' field in SystemSetting model should handle JSON deserialization if type is JSON
            # or it should be cast appropriately based on 'value_type'
            # For simplicity, assuming 'value' is directly usable or already deserialized by Pydantic model
            return setting.value
        logger.info(f"System setting key '{key}' not found, returning default value: {default}")
        return default

logger.info("SystemSettingService class defined.")
