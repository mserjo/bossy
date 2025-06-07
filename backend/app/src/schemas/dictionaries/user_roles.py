# backend/app/src/schemas/dictionaries/user_roles.py

"""
Pydantic schemas for UserRole dictionary entries.
"""

import logging
from typing import Optional, List, Any # For optional custom fields like 'permissions'
from datetime import datetime, timezone # For example values in __main__ and BaseResponseSchema

from pydantic import Field
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryBase,
    # DictionaryCreate as BaseDictionaryCreate, # Not directly used if UserRoleCreate inherits UserRoleBase
    # DictionaryUpdate as BaseDictionaryUpdate, # Not directly used if UserRoleUpdate inherits UserRoleBase
    DictionaryResponse as BaseDictionaryResponse
)

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- UserRole Schemas ---

class UserRoleBase(DictionaryBase):
    """Base schema for UserRole, inherits all fields from DictionaryBase."""
    # Example of a custom field if UserRole model had 'permissions' as a JSON list:
    # permissions: Optional[List[str]] = Field(None,
    #                                          description="List of permission strings associated with this role.",
    #                                          example=["users:read", "users:write", "tasks:assign"])
    # is_system_role: Optional[bool] = Field(None,
    #                                         description="True if this is a core system role and cannot be deleted by users.",
    #                                         example=False)
    pass

class UserRoleCreate(UserRoleBase):
    """
    Schema for creating a new UserRole.
    Inherits fields from UserRoleBase. 'code' and 'name' are effectively required.
    """
    # If 'permissions' were in UserRoleBase and should be optional during creation:
    # permissions: Optional[List[str]] = Field(None, example=["tasks:view"])
    pass

class UserRoleUpdate(UserRoleBase):
    """
    Schema for updating an existing UserRole.
    All fields from UserRoleBase are made optional here for partial updates.
    """
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="Unique code or short identifier.")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Human-readable name.")
    description: Optional[str] = Field(None)
    state: Optional[str] = Field(None, max_length=50)
    is_default: Optional[bool] = Field(None)
    display_order: Optional[int] = Field(None)
    notes: Optional[str] = Field(None)
    # If 'permissions' were in UserRoleBase and updatable:
    # permissions: Optional[List[str]] = Field(None, example=["users:read_all"])
    # is_system_role: Optional[bool] = Field(None)


class UserRoleResponse(BaseDictionaryResponse):
    """
    Schema for representing a UserRole in API responses.
    Inherits all fields from BaseDictionaryResponse.
    Add any UserRole-specific response fields here if UserRoleBase had custom fields.
    """
    # If 'permissions' were in UserRoleBase and should be in the response:
    # permissions: Optional[List[str]] = Field(None, description="List of permission strings.", example=["users:read"])
    # is_system_role: Optional[bool] = Field(None, description="Is this a core system role?")
    pass


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- UserRole Schemas (Dictionary) --- Demonstration")

    # UserRoleCreate Example
    role_create_data = {
        "code": "GROUP_ADMIN",
        "name": "Group Administrator",
        "description": "Manages a specific group and its members.",
        "state": "active",
        # "permissions": ["group:edit", "group:invite_member"],
        # "isSystemRole": False
    }
    try:
        role_create_schema = UserRoleCreate(**role_create_data)
        logger.info(f"UserRoleCreate valid: {role_create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating UserRoleCreate: {e}")

    # UserRoleUpdate Example
    role_update_data = {"description": "Manages a specific group, its members, tasks, and rewards."}
    role_update_schema = UserRoleUpdate(**role_update_data)
    logger.info(f"UserRoleUpdate (partial): {role_update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # UserRoleResponse Example
    role_response_data = {
        "id": 2,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "code": "MEMBER",
        "name": "Member",
        "description": "Regular member of a group.",
        "state": "active",
        "isDefault": True,
        "displayOrder": 2,
        # "permissions": ["tasks:view_own", "tasks:complete_own"],
        # "isSystemRole": False
    }
    try:
        role_response_schema = UserRoleResponse(**role_response_data) # type: ignore[call-arg]
        logger.info(f"UserRoleResponse: {role_response_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating UserRoleResponse: {e}")
