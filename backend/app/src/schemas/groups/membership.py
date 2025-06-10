# backend/app/src/schemas/groups/membership.py

"""
Pydantic schemas for Group Memberships.
"""

import logging
from typing import Optional
from datetime import datetime, timezone, timedelta # Added timezone, timedelta for __main__

from pydantic import Field

from backend.app.src.schemas.base import BaseSchema, BaseResponseSchema
# For nested user/group/role info in responses, import their respective minimal response schemas
# from backend.app.src.schemas.auth.user import UserPublicProfileResponse # Or a more minimal UserBasicInfo
# from backend.app.src.schemas.groups.group import GroupResponse # Usually too verbose, create GroupBasicInfo
# from backend.app.src.schemas.dictionaries.user_roles import UserRoleResponse # Or UserRoleBasicInfo

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Minimal Sub-schemas for nested responses (examples) ---
# These should ideally be defined in their respective modules or a common 'shared_schemas.py'
# For now, defining them here for clarity of GroupMembershipResponse structure.

class UserBasicInfo(BaseSchema):
    """Minimal user info for membership responses."""
    id: int = Field(..., example=101)
    name: Optional[str] = Field(None, example="Alice Wonderland")
    # avatar_url: Optional[str] = None # Example: Field(None, example="https://example.com/avatar.png")

class GroupBasicInfo(BaseSchema):
    """Minimal group info for membership responses."""
    id: int = Field(..., example=1)
    name: str = Field(..., example="Project Alpha Team")

class RoleBasicInfo(BaseSchema):
    """Minimal role info for membership responses."""
    id: int = Field(..., example=2)
    code: str = Field(..., example="ADMIN")
    name: str = Field(..., example="Administrator")

# --- GroupMembership Schemas ---

class GroupMembershipBase(BaseSchema):
    """
    Base schema for group membership data.
    `group_id` is typically a path parameter for API endpoints managing memberships of a specific group.
    `user_id` might be in the path for specific user's membership, or in the body for adding new members.
    """
    # user_id: int = Field(..., description="ID of the user for this membership.") # Usually in Create or path
    role_id: int = Field(..., description="ID of the user's role within this group (from dict_user_roles).", example=2)
    is_active: Optional[bool] = Field(True, description="Whether this membership is currently active.", example=True)
    notes: Optional[str] = Field(None, description="Optional notes specific to this membership.", example="Founding member")
    # join_date is usually set by the server on creation.

class GroupMembershipCreate(BaseSchema): # Not inheriting GroupMembershipBase to explicitly define fields for create
    """
    Schema for adding a user to a group (creating a membership).
    `group_id` is assumed to be part of the API path (e.g., /groups/{group_id}/members).
    """
    user_id: int = Field(..., description="ID of the user to add to the group.", example=101)
    role_id: int = Field(..., description="ID of the role to assign to the user in this group.", example=3) # e.g., 'member' role ID
    notes: Optional[str] = Field(None, description="Optional notes for this new membership.")

class GroupMembershipUpdate(BaseSchema): # Not inheriting GroupMembershipBase to explicitly define fields for update
    """
    Schema for updating an existing group membership.
    `group_id` and `user_id` are typically path parameters.
    Only role, active status, and notes are usually updatable.
    """
    role_id: Optional[int] = Field(None, description="New role ID for the user in this group.")
    is_active: Optional[bool] = Field(None, description="Update active status of the membership (e.g., for suspension/reactivation).")
    notes: Optional[str] = Field(None, description="Updated notes for this membership.")

class GroupMembershipResponse(BaseResponseSchema):
    """
    Schema for representing a group membership in API responses.
    Includes 'id' (surrogate PK of the membership record), 'created_at', 'updated_at'.
    """
    # user_id: int # Direct FK, but often we want the nested User object
    # group_id: int # Direct FK, often we want the nested Group object
    # role_id: int # Direct FK, often we want the nested Role object

    user: UserBasicInfo = Field(..., description="Information about the member.")
    group: GroupBasicInfo = Field(..., description="Information about the group.")
    role: RoleBasicInfo = Field(..., description="User's role within the group.")

    join_date: datetime = Field(..., description="Timestamp when the user joined the group (UTC).")
    is_active: bool = Field(..., description="Is this membership currently active?")
    notes: Optional[str] = Field(None, description="Notes specific to this membership.")


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- GroupMembership Schemas --- Demonstration")

    # GroupMembershipCreate Example
    # Assume group_id is from path, e.g., POST /groups/1/members
    membership_create_data = {
        "userId": 101, # camelCase for user_id
        "roleId": 3,   # camelCase for role_id
        "notes": "Invited by team lead."
    }
    try:
        create_schema = GroupMembershipCreate(**membership_create_data) # type: ignore[call-arg]
        logger.info(f"GroupMembershipCreate valid: {create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating GroupMembershipCreate: {e}")

    # GroupMembershipUpdate Example
    # Assume group_id and user_id are from path, e.g., PUT /groups/1/members/101
    membership_update_data = {"roleId": 2, "isActive": False} # Promote to role_id 2 (e.g. admin), and deactivate
    update_schema = GroupMembershipUpdate(**membership_update_data) # type: ignore[call-arg]
    logger.info(f"GroupMembershipUpdate (partial): {update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # GroupMembershipResponse Example
    user_info_data = {"id": 101, "name": "Alice Wonderland"}
    group_info_data = {"id": 1, "name": "Project Alpha Team"}
    role_info_data = {"id": 2, "code": "ADMIN", "name": "Administrator"}

    response_data = {
        "id": 50, # ID of the GroupMembership record itself
        "createdAt": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "user": user_info_data,
        "group": group_info_data,
        "role": role_info_data,
        "joinDate": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(), # camelCase for join_date
        "isActive": True,
        "notes": "Key contributor"
    }
    try:
        response_schema = GroupMembershipResponse(**response_data) # type: ignore[call-arg]
        logger.info(f"GroupMembershipResponse: {response_schema.model_dump_json(by_alias=True, indent=2)}")
        if response_schema.user:
            logger.info(f"  Member Name (from nested schema): {response_schema.user.name}")
        if response_schema.role:
            logger.info(f"  Member Role Name (from nested schema): {response_schema.role.name}")
    except Exception as e:
        logger.error(f"Error creating GroupMembershipResponse: {e}")
