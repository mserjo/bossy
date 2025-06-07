# backend/app/src/schemas/groups/group.py

"""
Pydantic schemas for Groups.
"""

import logging
from typing import Optional, List # For list of members in detailed response, if added
from datetime import datetime, timezone # For BaseResponseSchema inheritance and examples

from pydantic import Field, HttpUrl

from backend.app.src.schemas.base import BaseSchema, BaseMainResponseSchema
# For OwnerBasicInfo and GroupTypeBasicInfo, we'd ideally have specific minimal schemas
# from ..auth.user import UserPublicProfileResponse # Example for richer owner info
# from ..dictionaries.group_types import GroupTypeResponse # Example for richer group_type info

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Sub-schemas for nested responses (examples) ---
class OwnerBasicInfo(BaseSchema):
    """Minimal info about a group owner for embedding in GroupResponse."""
    id: int
    name: Optional[str] = None # Or full_name, username etc.
    # avatar_url: Optional[HttpUrl] = None

class GroupTypeBasicInfo(BaseSchema):
    """Minimal info about a group type for embedding in GroupResponse."""
    id: int
    code: str
    name: str

# --- Group Schemas ---

class GroupBase(BaseSchema):
    """Base schema for group data, common to create and update operations."""
    name: str = Field(..., min_length=2, max_length=255, description="Name of the group.", example="The Avengers HQ")
    description: Optional[str] = Field(None, description="Optional detailed description of the group.", example="A place for Earth's Mightiest Heroes to hang out.")
    group_type_id: int = Field(..., description="ID of the group type (from dict_group_types).", example=1)
    icon_url: Optional[HttpUrl] = Field(None, description="Optional URL to an icon for the group.", example="https://example.com/icons/avengers.png")
    currency_name: Optional[str] = Field("points", max_length=50, description="Custom name for the group's currency/points.", example="Kudos Points")
    state: Optional[str] = Field("active", max_length=50, description="State of the group (e.g., 'active', 'archived').", example="active")
    # owner_id is usually set by the system based on the currently authenticated user during creation.
    # It might be updatable by an admin via a specific endpoint/service method.

class GroupCreate(GroupBase):
    """
    Schema for creating a new group.
    `owner_id` will be set by the backend service based on the current authenticated user.
    """
    # All fields from GroupBase are used. Name and group_type_id are mandatory.
    pass

class GroupUpdate(GroupBase):
    """
    Schema for updating an existing group.
    All fields are optional for partial updates.
    `group_type_id` and `owner_id` are typically not updatable or have specific service logic.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=255, description="Name of the group.")
    description: Optional[str] = Field(None, description="Optional detailed description of the group.")
    group_type_id: Optional[int] = Field(None, description="ID of the group type. Changing this might have significant implications.")
    icon_url: Optional[HttpUrl] = Field(None, description="Optional URL to an icon for the group.")
    currency_name: Optional[str] = Field(None, max_length=50, description="Custom name for the group's currency/points.")
    state: Optional[str] = Field(None, max_length=50, description="State of the group.")
    # owner_id: Optional[int] = Field(None, description="Transfer ownership. Requires special privileges.")

class GroupResponse(BaseMainResponseSchema):
    """
    Schema for representing a group in API responses.
    Inherits id, created_at, updated_at, deleted_at, name, description, state, notes from BaseMainResponseSchema.
    """
    # Override fields from BaseMainResponseSchema if their constraints/examples differ for Group
    # name is already defined in BaseMainResponseSchema and is mandatory.
    # description, state, notes are also from BaseMainResponseSchema and are Optional.

    # Group-specific fields from Group model
    # owner_id: int = Field(..., description="ID of the group owner.") # Not usually exposed directly if owner object is present
    # group_type_id: int = Field(..., description="ID of the group type.") # Not usually exposed directly if group_type object is present
    icon_url: Optional[HttpUrl] = Field(None, description="URL to an icon for the group.")
    currency_name: Optional[str] = Field(None, description="Custom name for the group's currency/points.")

    # Enriched (nested) information - examples
    owner: Optional[OwnerBasicInfo] = Field(None, description="Basic information about the group owner.")
    group_type: Optional[GroupTypeBasicInfo] = Field(None, description="Basic information about the group type.")

    # These fields are from BaseMainResponseSchema (which includes BaseResponseSchema -> IDSchemaMixin, TimestampSchemaMixin) and SoftDeleteSchemaMixin
    # id: int
    # created_at: datetime
    # updated_at: datetime
    # deleted_at: Optional[datetime]

# For a more detailed response, e.g., including a list of members (paginated ideally)
# from ..auth.user import UserPublicProfileResponse # Example for richer member info
# class GroupMemberInfo(UserPublicProfileResponse):
#     role_in_group: str = Field(..., description="User's role in this group")

# class GroupDetailedResponse(GroupResponse):
#     members: Optional[List[GroupMemberInfo]] = Field(None, description="List of group members (subset for detail view)")
#     # tasks_summary: Optional[Any] = Field(None, description="Summary of tasks in the group")


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Group Schemas --- Demonstration")

    # GroupCreate Example
    group_create_data = {
        "name": "Kudos Champions Team",
        "description": "A team dedicated to promoting kudos and recognition.",
        "groupTypeId": 1, # camelCase for group_type_id
        "iconUrl": "https://example.com/icon.png",
        "currencyName": "Kudos"
    }
    try:
        group_create_schema = GroupCreate(**group_create_data) # type: ignore[call-arg]
        logger.info(f"GroupCreate valid: {group_create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating GroupCreate: {e}")

    # GroupUpdate Example
    group_update_data = {"description": "An awesome team for peer recognition and motivation!", "currencyName": "Super Kudos"}
    group_update_schema = GroupUpdate(**group_update_data) # type: ignore[call-arg]
    logger.info(f"GroupUpdate (partial): {group_update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # GroupResponse Example
    owner_info_data = {"id": 101, "name": "Tony Stark"}
    group_type_info_data = {"id": 1, "code": "PROJECT_TEAM", "name": "Project Team"}
    group_response_data = {
        "id": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "deletedAt": None,
        "name": "Kudos Champions Team",
        "description": "An awesome team for peer recognition and motivation!",
        "state": "active",
        "notes": "Initial setup phase.",
        "iconUrl": "https://example.com/icon.png",
        "currencyName": "Super Kudos",
        "owner": owner_info_data,
        "groupType": group_type_info_data
    }
    try:
        group_response_schema = GroupResponse(**group_response_data) # type: ignore[call-arg]
        logger.info(f"GroupResponse: {group_response_schema.model_dump_json(by_alias=True, indent=2)}")
        if group_response_schema.owner:
            logger.info(f"  Owner Name (from nested schema): {group_response_schema.owner.name}")
    except Exception as e:
        logger.error(f"Error creating GroupResponse: {e}")
