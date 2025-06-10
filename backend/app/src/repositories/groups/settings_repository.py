# backend/app/src/repositories/groups/settings_repository.py

"""
Repository for GroupSetting entities.
Provides CRUD operations and specific methods for managing group-specific settings.
"""

import logging
from typing import Optional, List, Any, Dict, Union # Added List, Dict, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.src.models.groups.settings import GroupSetting, LocalValueTypeEnum # Using LocalValueTypeEnum from model
from backend.app.src.schemas.groups.settings import GroupSettingCreate, GroupSettingUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class GroupSettingRepository(BaseRepository[GroupSetting, GroupSettingCreate, GroupSettingUpdate]):
    """
    Repository for managing GroupSetting records.
    """

    def __init__(self):
        super().__init__(GroupSetting)

    async def get_by_group_and_key(self, db: AsyncSession, *, group_id: int, key: str) -> Optional[GroupSetting]:
        """
        Retrieves a specific setting for a group by its group_id and key.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            key: The unique key of the setting within the group.

        Returns:
            The GroupSetting object if found, otherwise None.
        """
        statement = select(self.model).where(
            self.model.group_id == group_id, # type: ignore[attr-defined]
            self.model.key == key # type: ignore[attr-defined]
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_all_for_group(self, db: AsyncSession, *, group_id: int, skip: int = 0, limit: int = 100) -> List[GroupSetting]:
        """
        Retrieves all settings for a specific group, with pagination.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of GroupSetting objects for the specified group.
        """
        statement = (
            select(self.model)
            .where(self.model.group_id == group_id) # type: ignore[attr-defined]
            .order_by(self.model.key) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: GroupSettingCreate, group_id: int) -> GroupSetting:
        """
        Creates a new group setting.
        The 'value' from the schema will be converted to its string representation
        for storage using the model's `set_typed_value` method.
        `group_id` is taken as an explicit parameter.

        Args:
            db: The SQLAlchemy asynchronous database session.
            obj_in: The Pydantic schema containing data for the new group setting.
            group_id: The ID of the group this setting belongs to.


        Returns:
            The newly created GroupSetting object.
        """
        db_obj = self.model(
            group_id=group_id, # Explicitly set group_id
            key=obj_in.key,
            value_type=obj_in.value_type,
            name=obj_in.name,
            description=obj_in.description,
            is_editable_by_group_admin=obj_in.is_editable_by_group_admin
        )

        try:
            db_obj.set_typed_value(obj_in.value)
        except (ValueError, TypeError) as e:
            logger.error(f"Error setting typed value for group setting '{obj_in.key}' for group_id '{group_id}': {e}")
            raise

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: GroupSetting, # The existing model instance from DB
        obj_in: Union[GroupSettingUpdate, Dict[str, Any]]
    ) -> GroupSetting:
        """
        Updates an existing group setting.
        If 'value' or 'value_type' is part of the update, it ensures the
        stored string 'value' is correctly updated using the model's logic.

        Args:
            db: The SQLAlchemy asynchronous database session.
            db_obj: The current GroupSetting object to update.
            obj_in: The Pydantic schema or dictionary containing update data.

        Returns:
            The updated GroupSetting object.
        """
        update_data: Dict[str, Any]
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if "value_type" in update_data:
            new_value_type_str = update_data["value_type"]
            try:
                new_value_type_enum = LocalValueTypeEnum(new_value_type_str) if isinstance(new_value_type_str, str) else new_value_type_str
                if isinstance(new_value_type_enum, LocalValueTypeEnum):
                    setattr(db_obj, "value_type", new_value_type_enum)
                else:
                    raise ValueError(f"Invalid value_type provided: {new_value_type_str}")
            except ValueError as e:
                logger.error(f"Invalid value_type '{new_value_type_str}' for group setting '{db_obj.key}': {e}") # type: ignore[attr-defined]
                raise

        if "value" in update_data:
            new_value = update_data["value"]
            try:
                db_obj.set_typed_value(new_value)
            except (ValueError, TypeError) as e:
                logger.error(f"Error setting typed value during update for group setting '{db_obj.key}': {e}") # type: ignore[attr-defined]
                raise

        for field, value_to_set in update_data.items():
            if field not in ["value", "value_type"] and hasattr(db_obj, field):
                setattr(db_obj, field, value_to_set)

        # db_obj.updated_at is handled by TimestampedMixin via BaseRepository's default update or by SQLAlchemy event listeners.
        # If BaseRepository.update is called, it will handle this.
        # If we are manually saving like this, we might need to set it.
        # The current BaseRepository.update does:
        #   obj_data = jsonable_encoder(db_obj)
        #   ...
        #   setattr(db_obj, field, update_data[field])
        #   db.add(db_obj); await db.commit(); await db.refresh(db_obj)
        # This should trigger TimestampedMixin's @event.listens_for(Session, "before_flush")
        # So, no explicit updated_at set needed here if relying on that.

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_typed_value_for_group_key(
        self, db: AsyncSession, *, group_id: int, key: str
    ) -> Optional[Any]:
        """
        Retrieves a specific group setting by group_id and key, and returns its
        value cast to the appropriate type.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            key: The unique key of the setting.

        Returns:
            The typed value of the setting if found, otherwise None.
        """
        setting = await self.get_by_group_and_key(db, group_id=group_id, key=key)
        if setting:
            try:
                return setting.get_typed_value()
            except Exception as e:
                logger.error(f"Error getting typed value for group_id '{group_id}', key '{key}': {e}. Raw value: '{setting.value}'")
                return setting.value
        return None
