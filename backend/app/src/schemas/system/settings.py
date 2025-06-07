# backend/app/src/schemas/system/settings.py

"""
Pydantic schemas for System Settings.
"""

import logging
from typing import Optional, Any, Dict
from datetime import datetime, timezone # Added timezone for __main__
import json # For model_validator example

from pydantic import Field, field_validator, model_validator # Removed duplicate validator import

from backend.app.src.schemas.base import BaseSchema, BaseResponseSchema
from backend.app.src.models.system.settings import ValueTypeEnum # Import the Enum from the model

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- SystemSetting Schemas ---

class SystemSettingBase(BaseSchema):
    """Base schema for system settings, containing all common fields."""
    key: str = Field(..., min_length=3, max_length=255,
                     description="Unique key identifying the setting (e.g., 'maintenance_mode', 'default_user_role').",
                     example="maintenance_mode")
    value: Optional[Any] = Field(None, description="The value of the setting. Type depends on 'value_type'. For creation/update, provide the actual type. For response, this might be the string representation from DB.", example="true")
    value_type: ValueTypeEnum = Field(..., description="The intended data type of the value.", example=ValueTypeEnum.BOOLEAN)
    name: Optional[str] = Field(None, max_length=255, description="Human-readable name or title for the setting.", example="Maintenance Mode")
    description: Optional[str] = Field(None, description="Detailed description of what the setting controls.", example="Enable to put the site into maintenance mode.")
    is_editable: bool = Field(True, description="Whether this setting can be modified by admins via an interface.", example=True)
    group_name: Optional[str] = Field(None, max_length=100, description="Optional grouping for settings in an admin UI (e.g., 'General', 'Email').", example="General")

    @model_validator(mode='before')
    @classmethod
    def validate_value_against_type(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        value = data.get('value')
        value_type_str = data.get('value_type') # This will be the string value of the enum member

        if value is None:
            return data

        try:
            # Convert string representation of enum to actual enum member for comparison
            value_type_enum = ValueTypeEnum(value_type_str) if value_type_str else None
        except ValueError:
            # Let Pydantic's field validation for `value_type` handle invalid enum strings.
            return data

        if value_type_enum:
            try:
                if value_type_enum == ValueTypeEnum.INTEGER:
                    int(value)
                elif value_type_enum == ValueTypeEnum.FLOAT:
                    float(value)
                elif value_type_enum == ValueTypeEnum.BOOLEAN:
                    if not isinstance(value, (bool, int, str)) or (isinstance(value, str) and value.lower() not in ['true', 'false', '1', '0', 'yes', 'no', 'on', 'off']):
                         if isinstance(value, int) and value not in [0,1]: # only 0 and 1 for int->bool
                            raise ValueError("Integer value for BOOLEAN must be 0 or 1.")
                         elif isinstance(value, str): # if string, it must be a recognized boolean string
                            pass # Pydantic will handle common boolean strings
                         elif not isinstance(value, bool): # if not bool, int, or valid string
                            raise ValueError("Boolean value must be a bool, int (0/1), or recognized string.")
                elif value_type_enum == ValueTypeEnum.JSON:
                    if isinstance(value, str): # If it's a string, try to parse it as JSON
                        json.loads(value)
                    elif not isinstance(value, (dict, list)): # If not a string, it should be dict or list
                        raise ValueError("JSON value must be a valid JSON string, dict, or list.")
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                # This is a pre-validation. Pydantic will do its own more specific validation per field.
                # This validator is more about ensuring the 'value' is plausible for the 'value_type' before Pydantic's stricter checks.
                # To make this error more specific to a field, you'd use field_validator, but that's harder with inter-field dependencies in Pydantic v2 < v2.7.
                # For now, we'll log it and let Pydantic proceed. Or, you could raise a generic ValueError to fail fast.
                logger.debug(f"Preliminary validation warning for key '{data.get('key', 'N/A')}': Value '{value}' might not be compatible with value_type '{value_type_enum.value if value_type_enum else 'N/A'}': {e}")
        return data

class SystemSettingCreate(SystemSettingBase):
    """Schema for creating a new system setting."""
    key: str = Field(..., min_length=3, max_length=255, description="Unique key for the setting.", example="new_feature_enabled")
    value_type: ValueTypeEnum = Field(..., description="The data type of the value.", example=ValueTypeEnum.BOOLEAN)

class SystemSettingUpdate(SystemSettingBase):
    """Schema for updating an existing system setting. All fields are optional."""
    key: Optional[str] = Field(None, min_length=3, max_length=255, description="Unique key for the setting.")
    value: Optional[Any] = Field(None, description="The value of the setting. Type depends on 'value_type'.")
    value_type: Optional[ValueTypeEnum] = Field(None, description="The data type of the value.")
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None)
    is_editable: Optional[bool] = Field(None)
    group_name: Optional[str] = Field(None, max_length=100)

class SystemSettingResponse(BaseResponseSchema, SystemSettingBase):
    """
    Schema for representing a system setting in API responses.
    Includes 'id', 'created_at', 'updated_at' from BaseResponseSchema.
    The 'value' field here will represent the string value as stored in the database.
    """
    value: Optional[str] = Field(None, description="The value of the setting as stored (usually string representation).", example="true")
    # typed_value: Optional[Any] = Field(None, description="The value cast to its actual type. Populated at runtime by API if needed.", exclude=True) # Exclude from schema, populate in endpoint

    # Example of a computed field if you want typed_value directly in the response schema (less common for direct DB model mapping)
    # from pydantic import computed_field
    # @computed_field
    # @property
    # def typed_value(self) -> Optional[Any]:
    #     if self.value is None: return None
    #     try:
    #         if self.value_type == ValueTypeEnum.STRING: return str(self.value)
    #         # ... (similar logic as model's get_typed_value)
    #         else: return self.value
    #     except: return self.value


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- SystemSetting Schemas --- Demonstration")

    # Create
    setting_create_data = {
        "key": "maintenance_mode",
        "value": True,
        "valueType": ValueTypeEnum.BOOLEAN, # Pass Enum member directly
        "name": "Site Maintenance Mode",
        "description": "Puts the site into read-only maintenance mode."
    }
    try:
        created_setting = SystemSettingCreate(**setting_create_data)
        logger.info(f"SystemSettingCreate valid: {created_setting.model_dump(by_alias=True)}")
        logger.info(f"  Value type: {type(created_setting.value)}, Value: {created_setting.value}")
    except Exception as e:
        logger.error(f"Error creating SystemSettingCreate: {e}")

    setting_create_json_data = {
        "key": "feature_flags",
        "value": {"new_dashboard": True, "beta_users": [1,2,3]},
        "valueType": ValueTypeEnum.JSON,
        "name": "Feature Flags"
    }
    try:
        created_json_setting = SystemSettingCreate(**setting_create_json_data)
        logger.info(f"SystemSettingCreate (JSON) valid: {created_json_setting.model_dump(by_alias=True)}")
        logger.info(f"  Value type: {type(created_json_setting.value)}, Value: {created_json_setting.value}")
    except Exception as e:
        logger.error(f"Error creating SystemSettingCreate (JSON): {e}")

    # Example of a value that might be problematic if not handled carefully by service/model layer
    # The schema validator here is basic and might pass this for string type.
    setting_problematic_value = {
        "key": "some_string_setting",
        "value": {"complex": "object"}, # Passing a dict for a STRING type
        "valueType": ValueTypeEnum.STRING,
        "name": "Some String Setting"
    }
    try:
        problem_setting = SystemSettingCreate(**setting_problematic_value)
        logger.info(f"SystemSettingCreate with problematic value (for STRING type): {problem_setting.model_dump(by_alias=True)}")
        # Service/model layer should ensure this dict is properly serialized to string if this is the intent.
    except Exception as e:
        logger.error(f"Error with problematic value: {e}")


    # Update (all fields optional)
    setting_update_data = {"value": "false", "description": "Site is fully operational."}
    updated_setting = SystemSettingUpdate(**setting_update_data)
    logger.info(f"SystemSettingUpdate: {updated_setting.model_dump(exclude_unset=True, by_alias=True)}")

    # Response
    response_data = {
        "id": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "key": "maintenance_mode",
        "value": "true",
        "valueType": ValueTypeEnum.BOOLEAN, # Pass Enum member
        "name": "Site Maintenance Mode",
        "isEditable": False
    }
    response_setting = SystemSettingResponse(**response_data)
    logger.info(f"SystemSettingResponse: {response_setting.model_dump_json(by_alias=True, indent=2)}")
    logger.info(f"  Response value_type: {response_setting.value_type.value}")

    # Example of response where value might be a JSON string
    response_json_data = {
        "id": 2, "createdAt": datetime.now(timezone.utc).isoformat(), "updatedAt": datetime.now(timezone.utc).isoformat(),
        "key": "feature_flags", "value": json.dumps({"new_dashboard": True}), "valueType": ValueTypeEnum.JSON
    }
    response_json_setting = SystemSettingResponse(**response_json_data)
    logger.info(f"SystemSettingResponse (JSON value): {response_json_setting.model_dump_json(by_alias=True, indent=2)}")
