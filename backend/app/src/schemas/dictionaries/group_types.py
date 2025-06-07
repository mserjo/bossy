# backend/app/src/schemas/dictionaries/group_types.py

"""
Pydantic schemas for GroupType dictionary entries.
"""

import logging
from typing import Optional # For optional custom fields if any
from datetime import datetime, timezone # For example values in __main__ and BaseResponseSchema

from pydantic import Field
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryBase,
    # DictionaryCreate as BaseDictionaryCreate, # Not directly used if GroupTypeCreate inherits GroupTypeBase
    # DictionaryUpdate as BaseDictionaryUpdate, # Not directly used if GroupTypeUpdate inherits GroupTypeBase
    DictionaryResponse as BaseDictionaryResponse
)

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- GroupType Schemas ---

class GroupTypeBase(DictionaryBase):
    """Base schema for GroupType, inherits all fields from DictionaryBase."""
    # Example of custom fields if GroupType model had them:
    # default_max_members: Optional[int] = Field(None,
    #                                             description="Default maximum members for this group type.",
    #                                             example=50)
    # allows_subgroups: Optional[bool] = Field(None,
    #                                         description="Whether groups of this type can have subgroups.",
    #                                         example=False)
    pass

class GroupTypeCreate(GroupTypeBase):
    """
    Schema for creating a new GroupType.
    Inherits fields from GroupTypeBase. 'code' and 'name' are effectively required.
    """
    pass

class GroupTypeUpdate(GroupTypeBase):
    """
    Schema for updating an existing GroupType.
    All fields from GroupTypeBase are made optional here for partial updates.
    """
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="Unique code or short identifier.")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Human-readable name.")
    description: Optional[str] = Field(None)
    state: Optional[str] = Field(None, max_length=50)
    is_default: Optional[bool] = Field(None)
    display_order: Optional[int] = Field(None)
    notes: Optional[str] = Field(None)
    # If custom fields were in GroupTypeBase:
    # default_max_members: Optional[int] = Field(None)
    # allows_subgroups: Optional[bool] = Field(None)


class GroupTypeResponse(BaseDictionaryResponse):
    """
    Schema for representing a GroupType in API responses.
    Inherits all fields from BaseDictionaryResponse.
    Add any GroupType-specific response fields here if GroupTypeBase had custom fields.
    """
    # If custom fields were in GroupTypeBase and should be in response:
    # default_max_members: Optional[int] = Field(None, description="Default maximum members.")
    # allows_subgroups: Optional[bool] = Field(None, description="Can have subgroups?")
    pass


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- GroupType Schemas (Dictionary) --- Demonstration")

    # GroupTypeCreate Example
    type_create_data = {
        "code": "FAMILY_UNIT",
        "name": "Family Unit",
        "description": "A group type for families.",
        "state": "active",
        # "defaultMaxMembers": 10, # camelCase alias example if field existed
        # "allowsSubgroups": False
    }
    try:
        type_create_schema = GroupTypeCreate(**type_create_data)
        logger.info(f"GroupTypeCreate valid: {type_create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating GroupTypeCreate: {e}")

    # GroupTypeUpdate Example
    type_update_data = {"description": "A group type specifically for close-knit family units."}
    type_update_schema = GroupTypeUpdate(**type_update_data)
    logger.info(f"GroupTypeUpdate (partial): {type_update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # GroupTypeResponse Example
    type_response_data = {
        "id": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "code": "WORK_TEAM",
        "name": "Work Team",
        "description": "A group type for professional teams.",
        "state": "active",
        "isDefault": False,
        "displayOrder": 3,
        # "defaultMaxMembers": 25, # If field existed
        # "allowsSubgroups": True
    }
    try:
        type_response_schema = GroupTypeResponse(**type_response_data) # type: ignore[call-arg]
        logger.info(f"GroupTypeResponse: {type_response_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating GroupTypeResponse: {e}")
