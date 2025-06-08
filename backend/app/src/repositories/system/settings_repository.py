# backend/app/src/repositories/system/settings_repository.py

"""
Repository for SystemSetting entities.
Provides CRUD operations and specific methods for managing system settings.
"""

import logging
from typing import Optional, Any, Dict, Union # Added Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Added select

from backend.app.src.models.system.settings import SystemSetting, ValueTypeEnum
from backend.app.src.schemas.system.settings import SystemSettingCreate, SystemSettingUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class SystemSettingRepository(BaseRepository[SystemSetting, SystemSettingCreate, SystemSettingUpdate]):
    """
    Repository for managing SystemSetting records.
    """

    def __init__(self):
        super().__init__(SystemSetting)

    async def get_by_key(self, db: AsyncSession, *, key: str) -> Optional[SystemSetting]:
        """
        Retrieves a system setting by its unique key.

        Args:
            db: The SQLAlchemy asynchronous database session.
            key: The unique key of the system setting.

        Returns:
            The SystemSetting object if found, otherwise None.
        """
        statement = select(self.model).where(self.model.key == key)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: SystemSettingCreate) -> SystemSetting:
        """
        Creates a new system setting.
        The 'value' from the schema (which can be of a specific type) will be
        converted to its string representation for storage using the model's
        `set_typed_value` method.

        Args:
            db: The SQLAlchemy asynchronous database session.
            obj_in: The Pydantic schema containing data for the new system setting.

        Returns:
            The newly created SystemSetting object.
        """
        db_obj = self.model(
            key=obj_in.key,
            value_type=obj_in.value_type,
            name=obj_in.name,
            description=obj_in.description,
            is_editable=obj_in.is_editable,
            group_name=obj_in.group_name
        )

        try:
            db_obj.set_typed_value(obj_in.value)
        except (ValueError, TypeError) as e:
            logger.error(f"Error setting typed value for setting '{obj_in.key}': {e}")
            raise

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: SystemSetting,
        obj_in: Union[SystemSettingUpdate, Dict[str, Any]]
    ) -> SystemSetting:
        """
        Updates an existing system setting.
        If 'value' or 'value_type' is part of the update, it ensures the
        stored string 'value' is correctly updated.

        Args:
            db: The SQLAlchemy asynchronous database session.
            db_obj: The current SystemSetting object to update.
            obj_in: The Pydantic schema or dictionary containing update data.

        Returns:
            The updated SystemSetting object.
        """
        update_data: Dict[str, Any]
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if "value_type" in update_data:
            new_value_type_str = update_data["value_type"]
            try:
                new_value_type_enum = ValueTypeEnum(new_value_type_str) if isinstance(new_value_type_str, str) else new_value_type_str
                if isinstance(new_value_type_enum, ValueTypeEnum):
                     setattr(db_obj, "value_type", new_value_type_enum)
                else:
                    raise ValueError(f"Invalid value_type provided: {new_value_type_str}")
            except ValueError as e:
                logger.error(f"Invalid value_type '{new_value_type_str}' for setting '{db_obj.key}': {e}")
                raise

        if "value" in update_data:
            new_value = update_data["value"]
            try:
                db_obj.set_typed_value(new_value)
            except (ValueError, TypeError) as e:
                logger.error(f"Error setting typed value during update for setting '{db_obj.key}': {e}")
                raise

        for field, value in update_data.items():
            if field not in ["value", "value_type"] and hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_typed_value_by_key(self, db: AsyncSession, *, key: str) -> Optional[Any]:
        """
        Retrieves a system setting by its key and returns its value cast to the
        appropriate type.

        Args:
            db: The SQLAlchemy asynchronous database session.
            key: The unique key of the system setting.

        Returns:
            The typed value of the setting if found, otherwise None.
        """
        setting = await self.get_by_key(db, key=key)
        if setting:
            try:
                return setting.get_typed_value()
            except Exception as e:
                logger.error(f"Error getting typed value for key '{key}' from DB object: {e}. Raw value: '{setting.value}'")
                return setting.value
        return None
