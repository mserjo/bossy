# backend/app/src/schemas/groups/invitation.py

"""
Pydantic schemas for Group Invitations.
"""

import logging
from typing import Optional
from datetime import datetime, timezone, timedelta # Added timezone, timedelta for __main__

from pydantic import Field, EmailStr, field_validator, model_validator # Added model_validator

from backend.app.src.schemas.base import BaseSchema, BaseResponseSchema
from backend.app.src.models.groups.invitation import InvitationStatusEnum # Import Enum from model
# For nested inviter/group info in responses
# from backend.app.src.schemas.auth.user import UserPublicProfileResponse # Or a more minimal UserBasicInfo
# from backend.app.src.schemas.groups.group import GroupResponse # Or GroupBasicInfo

# Using locally defined Basic Info schemas for now, similar to membership.py
class UserBasicInfo(BaseSchema): # Inherit BaseSchema for consistent config (e.g. camelCase)
    id: int = Field(..., example=10)
    name: Optional[str] = Field(None, example="Alice")

class GroupBasicInfo(BaseSchema): # Inherit BaseSchema
    id: int = Field(..., example=1)
    name: str = Field(..., example="Book Club Readers")

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- GroupInvitation Schemas ---

class GroupInvitationBase(BaseSchema):
    """
    Base schema for group invitation data.
    `group_id` is typically a path parameter for API endpoints managing invitations of a specific group.
    `invited_by_user_id` is usually set by the system based on the current authenticated user.
    """
    email_invited: Optional[EmailStr] = Field(None, description="Email address of the invitee (if not an existing user or for direct email invite).", example="new.member@example.com")
    phone_invited: Optional[str] = Field(None, max_length=30, description="Phone number of the invitee (if not an existing user).", example="+15551230000")
    target_user_id: Optional[int] = Field(None, description="ID of an existing system user to invite directly.", example=102)
    # expires_at: Optional[datetime] = Field(None, description="Optional custom expiry for the invitation. Defaults to system setting (e.g., 7 days).") # Default is handled by model
    # status is usually managed by the system, not set directly on create by user.

    # Using model_validator for Pydantic v2 to check cross-field dependencies
    @model_validator(mode='before')
    @classmethod
    def check_invitee_details_provided(cls, data: Any) -> Any:
        if isinstance(data, dict): # Ensure data is a dict before using .get()
            # Check if at least one of the invitee identification fields is present
            if not (data.get('email_invited') or data.get('phone_invited') or data.get('target_user_id') or \
                    data.get('emailInvited') or data.get('phoneInvited') or data.get('targetUserId')): # Check aliases too
                raise ValueError("At least one of email_invited, phone_invited, or target_user_id must be provided.")
        # Could add checks for mutual exclusivity if desired (e.g., target_user_id XOR (email or phone))
        # but often this logic is better in the service layer.
        return data

class GroupInvitationCreate(GroupInvitationBase):
    """
    Schema for creating a new group invitation.
    Requires at least one invitee identifier (email, phone, or target_user_id), checked by GroupInvitationBase validator.
    `group_id` and `invited_by_user_id` are assumed from context/path/authenticated user.
    """
    pass

class GroupInvitationUpdate(BaseSchema):
    """
    Schema for updating an existing group invitation (e.g., revoking it).
    Typically, only status might be updatable by an admin or the inviter.
    """
    status: InvitationStatusEnum = Field(..., description="New status for the invitation (e.g., 'revoked').")
    # Example: Allow extending expiry, but this is less common for updates.
    # expires_at: Optional[datetime] = Field(None, description="New expiry date/time for the invitation.")

class GroupInvitationResponse(BaseResponseSchema):
    """
    Schema for representing a group invitation in API responses.
    Includes 'id', 'created_at', 'updated_at' from BaseResponseSchema.
    """
    group: GroupBasicInfo = Field(..., description="Basic information about the group for which the invitation was made.")
    invited_by: Optional[UserBasicInfo] = Field(None, description="Basic information about the user who sent the invitation.")

    email_invited: Optional[EmailStr] = Field(None)
    phone_invited: Optional[str] = Field(None)
    target_user: Optional[UserBasicInfo] = Field(None, description="Basic information about the targeted existing user (if any).")

    invitation_code: str = Field(..., description="Unique code for this invitation.")
    status: InvitationStatusEnum = Field(..., description="Current status of the invitation.")
    expires_at: datetime = Field(..., description="Timestamp when the invitation expires (UTC).")
    accepted_at: Optional[datetime] = Field(None, description="Timestamp when the invitation was accepted (UTC).")
    revoked_at: Optional[datetime] = Field(None, description="Timestamp when the invitation was revoked (UTC).")

class GroupInvitationAccept(BaseSchema):
    """
    Schema for accepting a group invitation.
    The `invitation_code` is typically part of the URL path for an accept endpoint.
    This schema is for any additional payload if needed, or can be empty if not.
    """
    # user_id: Optional[int] = Field(None, description="ID of the user accepting, if not implicit from auth. Usually implicit.")
    # No specific fields needed if only code in path is used.
    # Could include a custom message or similar if the feature existed.
    pass


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- GroupInvitation Schemas --- Demonstration")

    # GroupInvitationCreate Example
    inv_create_email_data = {"emailInvited": "invitee@example.com"}
    try:
        create_email_schema = GroupInvitationCreate(**inv_create_email_data) # type: ignore[call-arg]
        logger.info(f"GroupInvitationCreate (email) valid: {create_email_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating GroupInvitationCreate (email): {e}")

    inv_create_user_data = {"targetUserId": 201}
    try:
        create_user_schema = GroupInvitationCreate(**inv_create_user_data) # type: ignore[call-arg]
        logger.info(f"GroupInvitationCreate (user_id) valid: {create_user_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating GroupInvitationCreate (user_id): {e}")

    inv_create_fail_data = {"notes": "This should fail"} # No invitee identifier
    try:
        GroupInvitationCreate(**inv_create_fail_data) # type: ignore[call-arg]
    except ValueError as e:
        logger.info(f"GroupInvitationCreate caught expected validation error: {e}")


    # GroupInvitationUpdate Example
    inv_update_data = {"status": InvitationStatusEnum.REVOKED}
    update_schema = GroupInvitationUpdate(**inv_update_data)
    logger.info(f"GroupInvitationUpdate (partial): {update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # GroupInvitationResponse Example
    group_info_data = {"id": 1, "name": "Book Club Readers"}
    inviter_info_data = {"id": 10, "name": "Alice"}
    target_user_info_data = {"id": 25, "name": "Bob (Invited User)"}
    response_data = {
        "id": 123,
        "createdAt": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
        "updatedAt": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "group": group_info_data,
        "invitedBy": inviter_info_data, # camelCase for invited_by
        "targetUser": target_user_info_data, # camelCase for target_user
        "invitationCode": "ABC123XYZ",
        "status": InvitationStatusEnum.PENDING,
        "expiresAt": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
        "acceptedAt": None,
        "revokedAt": None,
    }
    try:
        response_schema = GroupInvitationResponse(**response_data) # type: ignore[call-arg]
        logger.info(f"GroupInvitationResponse: {response_schema.model_dump_json(by_alias=True, indent=2)}")
        if response_schema.group:
             logger.info(f"  Invited to Group: {response_schema.group.name}")
        if response_schema.invited_by:
             logger.info(f"  Invited By: {response_schema.invited_by.name}") # Access with Python name
    except Exception as e:
        logger.error(f"Error creating GroupInvitationResponse: {e}")

    # GroupInvitationAccept Example (empty schema for now)
    accept_schema = GroupInvitationAccept()
    logger.info(f"GroupInvitationAccept (empty): {accept_schema.model_dump()}")
