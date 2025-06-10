# backend/app/src/schemas/groups/settings.py

"""
Pydantic schemas for Group Settings.
"""

import logging
from typing import Optional, Any, Dict
from datetime import datetime, timezone # Added timezone for __main__
import json # For model_validator example

from pydantic import Field, model_validator

from backend.app.src.schemas.base import BaseSchema, BaseResponseSchema
# Assuming ValueTypeEnum is defined in system.settings or a central core.types/enums module
# For this example, we'll re-import it from system.settings model path.
# In a real app, ensure this enum is defined in a common accessible place (e.g., core.dicts or core.enums)
# to avoid potential circular dependencies if schemas.system.settings needed to import something from schemas.groups.
from backend.app.src.models.system.settings import ValueTypeEnum as SystemValueTypeEnum # Using the one from system settings model

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- GroupSetting Schemas ---

class GroupSettingBase(BaseSchema):
    """Base schema for group settings, common for create and update."""
    key: str = Field(..., min_length=3, max_length=255,
                     description="Unique key identifying the setting within the group (e.g., 'max_members', 'task_approval_required').",
                     example="task_approval_required")
    value: Optional[Any] = Field(None, description="The value of the setting. Type depends on 'value_type'.", example="true")
    value_type: SystemValueTypeEnum = Field(..., description="The intended data type of the value.", example=SystemValueTypeEnum.BOOLEAN)
    name: Optional[str] = Field(None, max_length=255, description="Human-readable name for the setting (for UI).", example="Task Approval Required")
    description: Optional[str] = Field(None, description="Description of what this setting controls (for UI).", example="If true, task completions require admin approval.")
    is_editable_by_group_admin: bool = Field(True, description="Can group admins modify this setting?", example=True)
    # group_id is typically a path parameter in API calls, not part of request body for these operations.

    @model_validator(mode='before')
    @classmethod
    def validate_value_against_type(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        value = data.get('value')
        value_type_str = data.get('value_type') # This will be the string value of the enum member
        if value is None: return data

        try:
            value_type_enum = SystemValueTypeEnum(value_type_str) if value_type_str else None
        except ValueError:
            return data

        if value_type_enum:
            try:
                if value_type_enum == SystemValueTypeEnum.INTEGER: int(value)
                elif value_type_enum == SystemValueTypeEnum.FLOAT: float(value)
                elif value_type_enum == SystemValueTypeEnum.BOOLEAN:
                    if not isinstance(value, (bool, int, str)) or (isinstance(value, str) and value.lower() not in ['true', 'false', '1', '0', 'yes', 'no', 'on', 'off']):
                        if isinstance(value, int) and value not in [0,1]: raise ValueError("Int for BOOLEAN must be 0 or 1.")
                        elif isinstance(value, str): pass
                        elif not isinstance(value, bool): raise ValueError("Bool value must be bool, int (0/1), or recognized str.")
                elif value_type_enum == SystemValueTypeEnum.JSON:
                    if isinstance(value, str): json.loads(value)
                    elif not isinstance(value, (dict, list)): raise ValueError("JSON value must be valid JSON str, dict, or list.")
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                logger.debug(f"Preliminary validation warning for group setting key '{data.get('key', 'N/A')}': Value '{value}' might not be compatible with value_type '{value_type_enum.value if value_type_enum else 'N/A'}': {e}")
        return data

class GroupSettingCreate(GroupSettingBase):
    """Schema for creating a new group setting for a specific group."""
    # Key and value_type are mandatory from GroupSettingBase
    value: Any = Field(..., description="The value for the setting.") # Make value mandatory for creation

class GroupSettingUpdate(BaseSchema): # Changed to BaseSchema to define all fields as optional explicitly
    """
    Schema for updating an existing group setting.
    All fields are optional for partial updates. Key is not updatable.
    """
    # key: Optional[str] = Field(None, description="Key is generally not updatable.", exclude=True) # Key is usually not part of update payload, identified in path
    value: Optional[Any] = Field(None, description="The new value for the setting.")
    value_type: Optional[SystemValueTypeEnum] = Field(None, description="The data type of the value (changing this might require value revalidation).")
    name: Optional[str] = Field(None, max_length=255, description="Human-readable name for the setting.")
    description: Optional[str] = Field(None, description="Description of what this setting controls.")
    is_editable_by_group_admin: Optional[bool] = Field(None, description="Can group admins modify this setting?")


class GroupSettingResponse(BaseResponseSchema, GroupSettingBase):
    """
    Schema for representing a group setting in API responses.
    Includes 'id', 'created_at', 'updated_at' from BaseResponseSchema.
    Also includes group_id.
    """
    group_id: int = Field(..., description="ID of the group this setting belongs to.", example=1)
    value: Optional[str] = Field(None, description="The value of the setting as stored (string representation).", example="true")
    # Similar to SystemSettingResponse, a 'typed_value: Any' could be added here, populated by API logic.

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- GroupSetting Schemas --- Demonstration")

    # GroupSettingCreate Example
    setting_create_data = {
        "key": "allow_member_invite",
        "value": False,
        "valueType": SystemValueTypeEnum.BOOLEAN, # Pass Enum member
        "name": "Allow Member Invitations",
        "description": "If true, regular members can invite others to the group.",
        "isEditableByGroupAdmin": True
    }
    try:
        create_schema = GroupSettingCreate(**setting_create_data) # type: ignore[call-arg]
        logger.info(f"GroupSettingCreate valid: {create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating GroupSettingCreate: {e}")

    # GroupSettingUpdate Example
    setting_update_data = {"value": True, "description": "Regular members are now allowed to invite others."}
    update_schema = GroupSettingUpdate(**setting_update_data)
    logger.info(f"GroupSettingUpdate (partial): {update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # GroupSettingResponse Example
    response_data = {
        "id": 10,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "groupId": 1, # camelCase for group_id
        "key": "daily_task_limit",
        "value": "10", # Stored as string
        "valueType": SystemValueTypeEnum.INTEGER, # Pass Enum member
        "name": "Daily Task Creation Limit",
        "isEditableByGroupAdmin": True
    }
    try:
        response_schema = GroupSettingResponse(**response_data) # type: ignore[call-arg]
        logger.info(f"GroupSettingResponse: {response_schema.model_dump_json(by_alias=True, indent=2)}")
        logger.info(f"  Response value_type: {response_schema.value_type.value}")
    except Exception as e:
        logger.error(f"Error creating GroupSettingResponse: {e}")
