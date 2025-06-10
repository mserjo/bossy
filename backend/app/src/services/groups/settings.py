# backend/app/src/services/groups/settings.py
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload # If settings have related objects to load
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.groups.settings import GroupSetting # SQLAlchemy GroupSetting model
from app.src.models.groups.group import Group # To link setting to a group
from app.src.schemas.groups.settings import ( # Pydantic GroupSetting schemas
    GroupSettingCreate,
    GroupSettingUpdate,
    GroupSettingResponse
)
# from app.src.repositories.groups.group_setting_repository import GroupSettingRepository # Placeholder

# Initialize logger for this module
logger = logging.getLogger(__name__)

class GroupSettingService(BaseService): # If using repo: BaseService[GroupSettingRepository]
    """
    Service for managing settings specific to individual groups.
    Each group can have its own set of configurations like currency name,
    debt limits, task review policies, etc.
    """

    # If using repository pattern:
    # def __init__(self, db_session: AsyncSession, group_setting_repo: GroupSettingRepository):
    #     super().__init__(db_session, repo=group_setting_repo)
    #     logger.info("GroupSettingService initialized with GroupSettingRepository.")

    # If not using repository pattern (direct DB interaction via session):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("GroupSettingService initialized.")

    async def get_settings_for_group(self, group_id: UUID) -> Optional[GroupSettingResponse]:
        """
        Retrieves the settings for a specific group.
        A group typically has one settings record.
        """
        logger.debug(f"Attempting to retrieve settings for group ID: {group_id}")

        stmt = select(GroupSetting).where(GroupSetting.group_id == group_id)
        # If GroupSetting has relationships to eager load, add them here with .options(selectinload(...))

        result = await self.db_session.execute(stmt)
        settings_db = result.scalar_one_or_none()

        if settings_db:
            logger.info(f"Settings for group ID '{group_id}' found.")
            # return GroupSettingResponse.model_validate(settings_db) # Pydantic v2
            return GroupSettingResponse.from_orm(settings_db) # Pydantic v1
        else:
            logger.info(f"No settings record found for group ID '{group_id}'. May need to be created.")
            # Depending on application logic, you might create default settings here if none exist,
            # or expect them to be explicitly created. For now, just returning None.
            return None

    async def create_or_update_group_settings(
        self,
        group_id: UUID,
        settings_data: GroupSettingUpdate, # Using GroupSettingUpdate as it allows partial fields
        current_user_id: Optional[UUID] = None # Optional: for audit trails
    ) -> GroupSettingResponse:
        """
        Creates group settings if they don't exist, or updates them if they do.
        This is an upsert-like operation specifically for a group's settings record.

        Args:
            group_id (UUID): The ID of the group whose settings are being configured.
            settings_data (GroupSettingUpdate): Data for the settings.
            current_user_id (Optional[UUID]): ID of the user performing the operation (for audit/tracking).

        Returns:
            GroupSettingResponse: The created or updated group settings.

        Raises:
            ValueError: If the specified group does not exist.
        """
        logger.debug(f"Attempting to create or update settings for group ID: {group_id} by user ID: {current_user_id or 'System'}")

        # Ensure the group exists
        group_db = await self.db_session.get(Group, group_id)
        if not group_db:
            logger.error(f"Group with ID '{group_id}' not found. Cannot create/update settings.")
            raise ValueError(f"Group with ID '{group_id}' not found.")

        # Try to fetch existing settings
        stmt_select = select(GroupSetting).where(GroupSetting.group_id == group_id)
        settings_db = (await self.db_session.execute(stmt_select)).scalar_one_or_none()

        # update_data_dict = settings_data.model_dump(exclude_unset=True) # Pydantic v2
        update_data_dict = settings_data.dict(exclude_unset=True) # Pydantic v1

        if settings_db: # Update existing settings
            logger.info(f"Found existing settings for group ID '{group_id}'. Updating.")
            for field, value in update_data_dict.items():
                if hasattr(settings_db, field):
                    setattr(settings_db, field, value)
                else:
                    logger.warning(f"Field '{field}' not found on GroupSetting model during update for group ID '{group_id}'.")
            if hasattr(settings_db, 'updated_by_user_id') and current_user_id:
                settings_db.updated_by_user_id = current_user_id
        else: # Create new settings record
            logger.info(f"No existing settings for group ID '{group_id}'. Creating new settings record.")

            create_data = update_data_dict.copy() # Start with fields from update schema
            create_data['group_id'] = group_id # Ensure group_id is set

            if hasattr(GroupSetting, 'created_by_user_id') and current_user_id: # Check model attribute
                 create_data['created_by_user_id'] = current_user_id
            if hasattr(GroupSetting, 'updated_by_user_id') and current_user_id: # Check model attribute
                 create_data['updated_by_user_id'] = current_user_id

            settings_db = GroupSetting(**create_data)
            self.db_session.add(settings_db)

        try:
            await self.commit()
            await self.db_session.refresh(settings_db)
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error saving settings for group ID '{group_id}': {e}", exc_info=True)
            raise ValueError(f"Could not save settings for group ID '{group_id}' due to data conflict.")

        logger.info(f"Settings for group ID '{group_id}' saved successfully.")
        # return GroupSettingResponse.model_validate(settings_db) # Pydantic v2
        return GroupSettingResponse.from_orm(settings_db) # Pydantic v1

    async def update_group_currency(self, group_id: UUID, currency_name: str, current_user_id: Optional[UUID] = None) -> Optional[GroupSettingResponse]:
        """Updates only the currency name for a group's settings."""
        logger.debug(f"Updating currency for group ID {group_id} to '{currency_name}' by user {current_user_id or 'System'}.")
        update_payload = GroupSettingUpdate(currency_name=currency_name)
        return await self.create_or_update_group_settings(group_id, update_payload, current_user_id)

    async def get_group_setting_value(self, group_id: UUID, setting_key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Convenience method to get a specific setting value for a group.

        Args:
            group_id (UUID): The ID of the group.
            setting_key (str): The specific setting field name (e.g., 'currency_name', 'max_debt_amount').
            default (Optional[Any]): Default value if setting or key not found.

        Returns:
            Optional[Any]: The value of the setting or the default.
        """
        logger.debug(f"Getting setting value for key '{setting_key}' in group ID '{group_id}'.")
        group_settings_response = await self.get_settings_for_group(group_id)
        if group_settings_response: # This is a Pydantic model (GroupSettingResponse)
            if hasattr(group_settings_response, setting_key):
                value = getattr(group_settings_response, setting_key)
                logger.info(f"Found value '{value}' for setting key '{setting_key}' in group ID '{group_id}'.")
                return value
            else:
                logger.warning(f"Setting key '{setting_key}' not found in settings for group ID '{group_id}'. Returning default.")
        else:
            logger.info(f"No settings record found for group ID '{group_id}'. Returning default for key '{setting_key}'.")
        return default

logger.info("GroupSettingService class defined.")
