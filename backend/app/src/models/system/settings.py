# backend/app/src/models/system/settings.py

"""
SQLAlchemy model for storing system-wide settings or configurations.
"""

import logging
from typing import Optional, Any, Dict
import json # For handling JSON type values if needed
from enum import Enum as PythonEnum # For ValueTypeEnum definition

from sqlalchemy import Column, String, Text, Enum as SQLAlchemyEnum, JSON, Boolean # Added Boolean
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.src.models.base import BaseModel # Import your base model

# Configure logger for this module
logger = logging.getLogger(__name__)

class ValueTypeEnum(PythonEnum): # Changed to inherit from PythonEnum for clarity in definition
    """ Defines the possible data types for a system setting's value. """
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    # LIST_STR = "list_str" # Example for a list of strings, might need custom handling or JSON

class SystemSetting(BaseModel):
    """
    Represents a system setting stored in the database.
    This allows dynamic configuration of the application by administrators.

    Attributes:
        key (str): The unique key identifying the setting (e.g., 'maintenance_mode', 'default_user_role').
        value (Optional[str]): The value of the setting, stored as text.
                               Actual type casting should be based on `value_type`.
        value_type (ValueTypeEnum): The intended data type of the value (string, integer, boolean, etc.).
        name (Optional[str]): A human-readable name or title for the setting.
        description (Optional[str]): A detailed description of what the setting controls.
        is_editable (bool): Whether this setting can be modified by admins via an interface (defaults to True).
        group_name (Optional[str]): An optional grouping for settings in an admin UI (e.g., 'General', 'Email', 'Security').
    """
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True, comment="Unique key for the setting")
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Value of the setting, stored as text; cast based on value_type")

    # Using native SQLAlchemy Enum type for value_type
    value_type: Mapped[ValueTypeEnum] = mapped_column(
        SQLAlchemyEnum(ValueTypeEnum, name="valtypeenum", create_constraint=True, native_enum=False), # native_enum=False for string storage
        nullable=False,
        default=ValueTypeEnum.STRING,
        comment="The intended data type of the value (e.g., string, integer, boolean, json)"
    )

    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Human-readable name for the setting")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Detailed description of the setting's purpose")
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="Can this setting be edited by admins? False for system-managed settings.")
    group_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True, comment="Optional group name for organizing settings in UI")

    def __repr__(self) -> str:
        return f"<SystemSetting(id={self.id}, key='{self.key}', value_type='{self.value_type.value}')>"

    # Utility method to get the value cast to its intended type
    def get_typed_value(self) -> Any:
        """Returns the setting's value cast to its `value_type`."""
        if self.value is None:
            return None
        try:
            if self.value_type == ValueTypeEnum.STRING:
                return str(self.value)
            elif self.value_type == ValueTypeEnum.INTEGER:
                return int(self.value)
            elif self.value_type == ValueTypeEnum.FLOAT:
                return float(self.value)
            elif self.value_type == ValueTypeEnum.BOOLEAN:
                # Handle common boolean string representations
                if isinstance(self.value, bool): # Should not happen if stored as string 'true'/'false'
                    return self.value
                elif isinstance(self.value, str):
                    if self.value.lower() in ('true', '1', 'yes', 'on'):
                        return True
                    elif self.value.lower() in ('false', '0', 'no', 'off'):
                        return False
                    else:
                        logger.warning(f"Could not cast boolean string '{self.value}' for setting '{self.key}'. Returning raw string.")
                        return self.value # Or raise error
                else: # Should not happen if stored as string
                    return bool(self.value) # General fallback
            elif self.value_type == ValueTypeEnum.JSON:
                return json.loads(self.value)
            # elif self.value_type == ValueTypeEnum.LIST_STR:
            #     # Example: store as comma-separated or JSON string
            #     return [item.strip() for item in self.value.split(',')]
            else:
                logger.warning(f"Unknown value_type '{self.value_type}' for setting '{self.key}'. Returning raw string.")
                return self.value
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            logger.error(f"Error casting value for setting '{self.key}' (type: {self.value_type}): {e}. Raw value: '{self.value}'")
            return self.value # Return raw value or raise an error

    # Utility method to set the value, ensuring it's stored as a string
    def set_typed_value(self, new_value: Any) -> None:
        """Sets the setting's value, storing it as a string representation based on `value_type`."""
        if new_value is None:
            self.value = None
            return

        try:
            if self.value_type == ValueTypeEnum.STRING:
                self.value = str(new_value)
            elif self.value_type == ValueTypeEnum.INTEGER:
                # Ensure it's a valid integer before storing as string
                val = int(new_value)
                self.value = str(val)
            elif self.value_type == ValueTypeEnum.FLOAT:
                # Ensure it's a valid float before storing as string
                val = float(new_value)
                self.value = str(val)
            elif self.value_type == ValueTypeEnum.BOOLEAN:
                if isinstance(new_value, str):
                    self.value = 'true' if new_value.lower() in ('true', '1', 'yes', 'on') else 'false'
                else:
                    self.value = 'true' if bool(new_value) else 'false'
            elif self.value_type == ValueTypeEnum.JSON:
                self.value = json.dumps(new_value)
            # elif self.value_type == ValueTypeEnum.LIST_STR:
            #     if not isinstance(new_value, list) or not all(isinstance(i, str) for i in new_value):
            #         raise ValueError("Value must be a list of strings for LIST_STR type.")
            #     self.value = ",".join(new_value)
            else:
                logger.warning(f"Attempting to set value for unknown value_type '{self.value_type}' for setting '{self.key}'. Storing as raw string.")
                self.value = str(new_value)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            logger.error(f"Error preparing value for setting '{self.key}' (type: {self.value_type}, input: '{new_value}'): {e}. Value not set or remains unchanged.")
            # Optionally re-raise or handle more gracefully
            raise

if __name__ == "__main__":
    # This block is for demonstration and basic testing of the SystemSetting model structure.
    # It does not interact with a database directly here.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- SystemSetting Model --- Demonstration")

    # Create dummy instances (not added to a session or DB)
    # To get __table__ and columns, the model needs to be part of Base.metadata
    # and potentially Base.metadata.create_all() needs to be called on an engine.
    # For now, we'll test the set/get typed value logic.

    # Setting up a dummy SystemSetting instance for testing typed value methods
    # This doesn't use SQLAlchemy's ORM event lifecycle, just tests the methods.
    class DummySystemSetting(SystemSetting): # Inherit to avoid __abstract__ issues if BaseModel is abstract
         __abstract__ = False # Allow instantiation for testing
         # Minimal override if needed, or just use SystemSetting if Base is properly defined and non-abstract for this test
         pass

    # If BaseModel is abstract and has __tablename__ generation that relies on cls.__name__
    # We might need to ensure it's not abstract for this direct instantiation test or provide a dummy Base.
    # For this test, we assume SystemSetting can be instantiated if its Base is non-abstract or __tablename__ is explicit.
    # If SystemSetting.BaseModel is abstract, we might need a concrete class or mock.

    # Test Boolean
    setting_maintenance = SystemSetting(key="maintenance_mode", name="Maintenance Mode", value_type=ValueTypeEnum.BOOLEAN)
    setting_maintenance.set_typed_value(True)
    logger.info(f"Setting: {setting_maintenance.key}, Raw: '{setting_maintenance.value}', Typed: {setting_maintenance.get_typed_value()} ({type(setting_maintenance.get_typed_value())})")
    setting_maintenance.set_typed_value("off")
    logger.info(f"Setting: {setting_maintenance.key}, Raw: '{setting_maintenance.value}', Typed: {setting_maintenance.get_typed_value()} ({type(setting_maintenance.get_typed_value())})")

    # Test Integer
    setting_max_users = SystemSetting(key="max_users", name="Max Users", value_type=ValueTypeEnum.INTEGER)
    setting_max_users.set_typed_value(100)
    logger.info(f"Setting: {setting_max_users.key}, Raw: '{setting_max_users.value}', Typed: {setting_max_users.get_typed_value()} ({type(setting_max_users.get_typed_value())})")
    try:
        setting_max_users.set_typed_value("abc")
    except ValueError as e:
        logger.error(f"Caught expected error for {setting_max_users.key} with 'abc': {e}")

    # Test Float
    setting_threshold = SystemSetting(key="alert_threshold", name="Alert Threshold", value_type=ValueTypeEnum.FLOAT)
    setting_threshold.set_typed_value(99.9)
    logger.info(f"Setting: {setting_threshold.key}, Raw: '{setting_threshold.value}', Typed: {setting_threshold.get_typed_value()} ({type(setting_threshold.get_typed_value())})")

    # Test JSON
    setting_json_data = SystemSetting(key="feature_flags", name="Feature Flags", value_type=ValueTypeEnum.JSON)
    json_val = {"new_dashboard": True, "beta_feature": False}
    setting_json_data.set_typed_value(json_val)
    logger.info(f"Setting: {setting_json_data.key}, Raw: '{setting_json_data.value}', Typed: {setting_json_data.get_typed_value()} ({type(setting_json_data.get_typed_value())})")

    # Test String (default)
    setting_admin_email = SystemSetting(key="admin_email", name="Admin Email", value_type=ValueTypeEnum.STRING) # Or default
    setting_admin_email.set_typed_value("admin@example.com")
    logger.info(f"Setting: {setting_admin_email.key}, Raw: '{setting_admin_email.value}', Typed: {setting_admin_email.get_typed_value()} ({type(setting_admin_email.get_typed_value())})")

    # Example of inspecting columns if Base and metadata were fully set up:
    # logger.info(f"SystemSetting attributes (conceptual table columns): {[c.name for c in SystemSetting.__table__.columns if not c.name.startswith('_')]}")
    # This line would error if run directly without SQLAlchemy engine and metadata setup.
    # It's here for illustrative purposes of what could be inspected.
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine.")
