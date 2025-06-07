# backend/app/src/schemas/dictionaries/statuses.py

"""
Pydantic schemas for Status dictionary entries.
"""

import logging
from typing import Optional # For optional custom fields if any
from datetime import datetime, timezone # For example values in __main__ and BaseResponseSchema

from pydantic import Field
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryBase,
    DictionaryCreate as BaseDictionaryCreate, # Used if StatusCreate doesn't add/override fields from StatusBase specific to create
    DictionaryUpdate as BaseDictionaryUpdate, # Used if StatusUpdate doesn't add/override fields from StatusBase specific to update
    DictionaryResponse as BaseDictionaryResponse
)

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Status Schemas ---

# If Status model has specific fields not in BaseDictionaryModel,
# define them in StatusBaseSchema.
class StatusBase(DictionaryBase):
    """Base schema for Status, inherits all fields from DictionaryBase."""
    # Example of a custom field if Status model had one:
    # color_hex: Optional[str] = Field(None, max_length=7, pattern=r"^#[0-9a-fA-F]{6}$",
    #                                  description="Hex color code for UI representation (e.g., #FF0000)",
    #                                  example="#4CAF50")
    pass

class StatusCreate(StatusBase): # Inherit from StatusBase. DictionaryBase requirements (code, name) are met via StatusBase.
    """
    Schema for creating a new Status.
    Inherits fields from StatusBase. 'code' and 'name' are effectively required
    as they are non-optional in DictionaryBase (which StatusBase inherits).
    """
    # If StatusBase added new non-optional fields, they'd be required here too.
    # If 'color_hex' was added to StatusBase and should be optional during creation:
    # color_hex: Optional[str] = Field(None, max_length=7, pattern=r"^#[0-9a-fA-F]{6}$", example="#4CAF50")
    pass

class StatusUpdate(StatusBase): # Inherit from StatusBase, then make all fields optional in the body of this class
    """
    Schema for updating an existing Status.
    All fields from StatusBase are made optional here for partial updates.
    """
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="Unique code or short identifier.")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Human-readable name.")
    description: Optional[str] = Field(None) # Already optional in DictionaryBase/StatusBase
    state: Optional[str] = Field(None, max_length=50) # Already optional
    is_default: Optional[bool] = Field(None) # Already optional
    display_order: Optional[int] = Field(None) # Already optional
    notes: Optional[str] = Field(None) # Already optional
    # If 'color_hex' was added to StatusBase and is updatable:
    # color_hex: Optional[str] = Field(None, max_length=7, pattern=r"^#[0-9a-fA-F]{6}$", example="#FFC107")


class StatusResponse(BaseDictionaryResponse):
    """
    Schema for representing a Status in API responses.
    Inherits all fields from BaseDictionaryResponse (which includes id, timestamps, code, name etc.).
    Add any Status-specific response fields here if StatusBase had custom fields.
    """
    # If 'color_hex' was added to StatusBase and should be in the response:
    # color_hex: Optional[str] = Field(None, description="Hex color code for UI representation.", example="#4CAF50")
    pass


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Status Schemas (Dictionary) --- Demonstration")

    # StatusCreate Example
    status_create_data = {
        "code": "ACTIVE_TASK",
        "name": "Active Task",
        "description": "Task is currently active and in progress.",
        "state": "open",
        # "colorHex": "#2196F3" # Example if color_hex alias was used and field existed
    }
    try:
        status_create_schema = StatusCreate(**status_create_data)
        logger.info(f"StatusCreate valid: {status_create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating StatusCreate: {e}")

    # StatusUpdate Example
    status_update_data = {"description": "Task is active and assigned.", "state": "in_progress"}
    status_update_schema = StatusUpdate(**status_update_data)
    logger.info(f"StatusUpdate (partial): {status_update_schema.model_dump(exclude_unset=True, by_alias=True)}")
    logger.info(f"StatusUpdate (full, showing Nones for non-updated fields): {status_update_schema.model_dump(by_alias=True)}")


    # StatusResponse Example
    status_response_data = {
        "id": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "code": "COMPLETED",
        "name": "Completed",
        "description": "Task has been successfully completed.",
        "state": "closed",
        "isDefault": False,
        "displayOrder": 10,
        # "colorHex": "#4CAF50" # If field existed
    }
    try:
        status_response_schema = StatusResponse(**status_response_data) # type: ignore[call-arg]
        logger.info(f"StatusResponse: {status_response_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating StatusResponse: {e}")
