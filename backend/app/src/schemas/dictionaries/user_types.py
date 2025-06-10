# backend/app/src/schemas/dictionaries/user_types.py

"""
Pydantic schemas for UserType dictionary entries.
"""

import logging
from typing import Optional # For optional custom fields if any
from datetime import datetime, timezone # For example values in __main__ and BaseResponseSchema

from pydantic import Field
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryBase,
    # DictionaryCreate as BaseDictionaryCreate, # Not directly used if UserTypeCreate inherits UserTypeBase
    # DictionaryUpdate as BaseDictionaryUpdate, # Not directly used if UserTypeUpdate inherits UserTypeBase
    DictionaryResponse as BaseDictionaryResponse
)

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- UserType Schemas ---

class UserTypeBase(DictionaryBase):
    """Base schema for UserType, inherits all fields from DictionaryBase."""
    # Example of a custom field if UserType model had one:
    # can_login_via_ui: Optional[bool] = Field(None,
    #                                           description="Indicates if users of this type can typically log in via UI.",
    #                                           example=True)
    pass

class UserTypeCreate(UserTypeBase):
    """
    Schema for creating a new UserType.
    Inherits fields from UserTypeBase. 'code' and 'name' are effectively required.
    """
    pass

class UserTypeUpdate(UserTypeBase):
    """
    Schema for updating an existing UserType.
    All fields from UserTypeBase are made optional here for partial updates.
    """
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="Unique code or short identifier.")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Human-readable name.")
    description: Optional[str] = Field(None)
    state: Optional[str] = Field(None, max_length=50)
    is_default: Optional[bool] = Field(None)
    display_order: Optional[int] = Field(None)
    notes: Optional[str] = Field(None)
    # If 'can_login_via_ui' was in UserTypeBase:
    # can_login_via_ui: Optional[bool] = Field(None)


class UserTypeResponse(BaseDictionaryResponse):
    """
    Schema for representing a UserType in API responses.
    Inherits all fields from BaseDictionaryResponse.
    Add any UserType-specific response fields here if UserTypeBase had custom fields.
    """
    # If 'can_login_via_ui' was added to UserTypeBase and should be in the response:
    # can_login_via_ui: Optional[bool] = Field(None, description="Can users of this type log in via UI?", example=True)
    pass


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- UserType Schemas (Dictionary) --- Demonstration")

    # UserTypeCreate Example
    type_create_data = {
        "code": "HUMAN_USER",
        "name": "Human User",
        "description": "A standard human user account.",
        "state": "active",
        # "canLoginViaUi": True # Example if field was added and using alias
    }
    try:
        type_create_schema = UserTypeCreate(**type_create_data)
        logger.info(f"UserTypeCreate valid: {type_create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating UserTypeCreate: {e}")

    # UserTypeUpdate Example
    type_update_data = {"description": "A standard human user account with full system access."}
    type_update_schema = UserTypeUpdate(**type_update_data)
    logger.info(f"UserTypeUpdate (partial): {type_update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # UserTypeResponse Example
    type_response_data = {
        "id": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "code": "BOT_ACCOUNT",
        "name": "Bot Account",
        "description": "An automated service account.",
        "state": "active",
        "isDefault": False,
        "displayOrder": 5,
        # "canLoginViaUi": False # If field existed
    }
    try:
        type_response_schema = UserTypeResponse(**type_response_data) # type: ignore[call-arg]
        logger.info(f"UserTypeResponse: {type_response_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating UserTypeResponse: {e}")
