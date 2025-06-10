# backend/app/src/models/groups/settings.py

"""
SQLAlchemy model for storing group-specific settings.
"""

import logging
from typing import Optional, Any, Dict, TYPE_CHECKING # Added TYPE_CHECKING
import json # For JSON value handling
from enum import Enum as PythonEnum # For LocalValueTypeEnum
from datetime import datetime, timezone # For __main__

from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, Enum as SQLAlchemyEnum, Integer, Boolean # Added Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseModel # GroupSettings are simpler, may not need all BaseMainModel fields

# Configure logger for this module
logger = logging.getLogger(__name__)

# Re-define ValueTypeEnum here if it's not easily/safely importable from system.settings
# Or ensure it's in a core.types module accessible by both.
# For this exercise, we define a local one. In a real app, centralize it.
class LocalValueTypeEnum(PythonEnum): # Inherits from PythonEnum
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"

if TYPE_CHECKING:
    from backend.app.src.models.groups.group import Group

class GroupSetting(BaseModel):
    """
    Represents a specific setting for a group.
    Allows for fine-grained, dynamic configuration of group behaviors.

    Attributes:
        group_id (int): Foreign key to the group this setting belongs to.
        key (str): The unique key identifying the setting within the group (e.g., 'max_members', 'task_approval_required').
        value (Optional[str]): The value of the setting, stored as text. Actual type casting based on `value_type`.
        value_type (LocalValueTypeEnum): The intended data type of the value.
        name (Optional[str]): A human-readable name for the setting (for UI).
        description (Optional[str]): A description of what this setting controls (for UI).
        is_editable_by_group_admin (bool): Can group admins modify this setting? (defaults to True).
    """
    __tablename__ = "group_settings"

    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"), nullable=False, index=True, comment="The group this setting applies to")
    key: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="Unique key for the setting within this group")
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Value of the setting (stored as text, cast by value_type)")

    value_type: Mapped[LocalValueTypeEnum] = mapped_column(
        SQLAlchemyEnum(LocalValueTypeEnum, name="groupvaltypeenum", create_constraint=True, native_enum=False), # native_enum=False for string storage
        nullable=False,
        default=LocalValueTypeEnum.STRING,
        comment="Intended data type of the value (string, integer, boolean, json)"
    )

    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Human-readable name for the group setting (UI)")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Description of the group setting's purpose (UI)")
    is_editable_by_group_admin: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="Can group admins change this setting? System-enforced settings might be False.")

    # --- Relationship ---
    group: Mapped["Group"] = relationship(back_populates="settings")

    # --- Table Arguments ---
    __table_args__ = (
        UniqueConstraint('group_id', 'key', name='uq_group_setting_group_id_key'),
    )

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<GroupSetting(id={id_val}, group_id={self.group_id}, key='{self.key}', value_type='{self.value_type.value if self.value_type else 'N/A'}')>"

    def get_typed_value(self) -> Any:
        if self.value is None: return None
        try:
            if self.value_type == LocalValueTypeEnum.STRING: return str(self.value)
            elif self.value_type == LocalValueTypeEnum.INTEGER: return int(self.value)
            elif self.value_type == LocalValueTypeEnum.FLOAT: return float(self.value)
            elif self.value_type == LocalValueTypeEnum.BOOLEAN:
                if isinstance(self.value, str): return self.value.lower() in ('true', '1', 'yes', 'on')
                return bool(self.value) # Should not happen if stored as 'true'/'false' string
            elif self.value_type == LocalValueTypeEnum.JSON: return json.loads(self.value)
            else: return self.value # Should not happen with enum validation
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            logger.error(f"Error casting value for group setting '{self.key}' (group {self.group_id}, type: {self.value_type}): {e}")
            return self.value

    def set_typed_value(self, new_value: Any) -> None:
        if new_value is None: self.value = None; return
        try:
            if self.value_type == LocalValueTypeEnum.STRING: self.value = str(new_value)
            elif self.value_type == LocalValueTypeEnum.INTEGER: self.value = str(int(new_value))
            elif self.value_type == LocalValueTypeEnum.FLOAT: self.value = str(float(new_value))
            elif self.value_type == LocalValueTypeEnum.BOOLEAN:
                self.value = 'true' if bool(new_value) else 'false'
            elif self.value_type == LocalValueTypeEnum.JSON: self.value = json.dumps(new_value)
            else: self.value = str(new_value) # Should not happen
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            logger.error(f"Error serializing value for group setting '{self.key}' (group {self.group_id}, type: {self.value_type}): {e}")
            raise

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- GroupSetting Model --- Demonstration")

    setting_max_members = GroupSetting(
        group_id=1, # Assuming group with id=1 exists
        key="max_active_members",
        name="Maximum Active Members",
        description="Maximum number of active members allowed in this group.",
        value_type=LocalValueTypeEnum.INTEGER,
        is_editable_by_group_admin=True
    )
    setting_max_members.set_typed_value(50)
    setting_max_members.id = 1 # Simulate ORM ID
    setting_max_members.created_at = datetime.now(timezone.utc)
    setting_max_members.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example GroupSetting: {setting_max_members!r}")
    logger.info(f"  Key: {setting_max_members.key}, Typed Value: {setting_max_members.get_typed_value()}, Type: {type(setting_max_members.get_typed_value())}")
    logger.info(f"  Created At: {setting_max_members.created_at.isoformat()}")


    setting_task_approval = GroupSetting(
        group_id=1,
        key="task_completion_requires_approval",
        name="Task Approval Required",
        value_type=LocalValueTypeEnum.BOOLEAN
    )
    setting_task_approval.set_typed_value("TRUE") # Test string boolean
    setting_task_approval.id = 2
    setting_task_approval.created_at = datetime.now(timezone.utc)
    setting_task_approval.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example GroupSetting: {setting_task_approval!r}")
    logger.info(f"  Key: {setting_task_approval.key}, Typed Value: {setting_task_approval.get_typed_value()}, Type: {type(setting_task_approval.get_typed_value())}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"GroupSetting attributes (conceptual table columns): {[c.name for c in GroupSetting.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
