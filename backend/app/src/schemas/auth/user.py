# backend/app/src/schemas/auth/user.py

"""
Pydantic schemas for User accounts, profiles, and related operations.
"""

import logging
from typing import Optional, List # For List type hint
from datetime import datetime, timezone # Added timezone for examples

from pydantic import Field, EmailStr, field_validator, model_validator

from backend.app.src.schemas.base import BaseSchema, BaseResponseSchema, BaseMainResponseSchema
# Assuming ValueTypeEnum or similar for user_type_id might come from models or a central dicts/enums schema if needed for validation
# from backend.app.src.models.auth.user import UserType # Or a Pydantic enum for UserType codes
from backend.app.src.models.dictionaries.user_types import UserType as UserTypeModel # Example, if using the model's enum or codes
# For user_type_id, it's often just an int/str in schema, validated against DB dictionary by service layer.

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- User Schemas ---

class UserBase(BaseSchema):
    """Base schema for user data, common to create and update operations."""
    email: Optional[EmailStr] = Field(None, description="User's email address (must be unique).", example="user@example.com")
    first_name: Optional[str] = Field(None, max_length=100, description="User's first name.", example="John")
    last_name: Optional[str] = Field(None, max_length=100, description="User's last name.", example="Doe")
    name: Optional[str] = Field(None, max_length=255, description="Display name of the user (can be full name or nickname).", example="JohnnyD")
    phone_number: Optional[str] = Field(None, max_length=30, description="User's phone number (optional, must be unique if provided).", example="+15551234567")
    # user_type_id: Optional[int] = Field(None, description="FK to user_types dictionary.", example=1) # Prefer user_type_code for DX
    # description, state, notes from BaseMainModel are usually admin-set or derived, not direct user input on base.

class UserCreate(UserBase):
    """Schema for new user creation by an admin or system process."""
    email: EmailStr = Field(..., description="User's email address (login identifier).", example="newuser@example.com")
    password: str = Field(..., min_length=8, description="User's password (will be hashed).", example="Str0ngP@sswOrd")
    # Admin might set these directly:
    is_active: Optional[bool] = Field(True, description="Is the user account active?")
    is_superuser: Optional[bool] = Field(False, description="Does the user have superuser privileges?")
    user_type_code: Optional[str] = Field(UserTypeModel.HUMAN.value if hasattr(UserTypeModel, 'HUMAN') else 'human', description="Code for user type (e.g., 'human', 'bot').", example="human")

class UserRegister(BaseSchema):
    """Schema for user self-registration."""
    email: EmailStr = Field(..., description="User's email address.", example="registering.user@example.com")
    password: str = Field(..., min_length=8, description="User's password.", example="MySecureP@ss1")
    password_confirm: str = Field(..., description="Password confirmation.", example="MySecureP@ss1")
    first_name: Optional[str] = Field(None, max_length=100, example="Jane")
    last_name: Optional[str] = Field(None, max_length=100, example="Doe")
    name: Optional[str] = Field(None, max_length=255, description="Optional display name.", example="JaneD")

    @model_validator(mode='after')
    def check_passwords_match(self) -> 'UserRegister':
        if self.password is not None and self.password_confirm is not None: # password_confirm will always be there due to ...
            if self.password != self.password_confirm:
                raise ValueError("Passwords do not match")
        return self

class UserUpdate(UserBase):
    """
    Schema for user profile updates by the user themselves.
    Typically, users can update their names, phone, maybe email (with verification).
    Password update is separate. Critical fields like is_active, is_superuser are not here.
    """
    # All fields are inherited as Optional from UserBase.
    # email: Optional[EmailStr] = Field(None, ...) # If email change is allowed, it usually triggers re-verification.
    pass

class UserAdminUpdate(UserBase):
    """
    Schema for updating user information by an administrator.
    Allows modification of more fields than a regular user update.
    """
    email: Optional[EmailStr] = Field(None, description="User's email address.") # Admin can change email
    is_active: Optional[bool] = Field(None, description="Activate or deactivate the user account.")
    is_superuser: Optional[bool] = Field(None, description="Grant or revoke superuser privileges.")
    user_type_code: Optional[str] = Field(None, description="Code for user type (e.g., 'human', 'bot').")
    state: Optional[str] = Field(None, max_length=50, description="Set user state (e.g., 'pending_verification', 'active', 'suspended').")
    notes: Optional[str] = Field(None, description="Admin notes for the user.")
    # Password should be reset via a separate mechanism, not directly set here by admin for security.

class UserPasswordUpdate(BaseSchema):
    """Schema for a user to update their own password."""
    current_password: str = Field(..., description="User's current password.")
    new_password: str = Field(..., min_length=8, description="New desired password.")
    new_password_confirm: str = Field(..., description="Confirmation of the new password.")

    @model_validator(mode='after')
    def check_new_passwords_match(self) -> 'UserPasswordUpdate':
        if self.new_password is not None and self.new_password_confirm is not None:
            if self.new_password != self.new_password_confirm:
                raise ValueError("New passwords do not match")
        return self

# --- User Response Schemas ---

class UserResponse(BaseMainResponseSchema, UserBase): # UserBase provides email, names, phone. BaseMainResponseSchema provides id, timestamps, name, desc, state, notes, deleted_at
    """
    Schema for representing a user in API responses (full view, typically for admin or self).
    Excludes hashed_password.
    """
    # Fields from UserBase (email, first_name, last_name, phone_number) are already Optional or correctly typed.
    # Fields from BaseMainResponseSchema (id, created_at, updated_at, deleted_at, name, description, state, notes)
    # We need to ensure `name` is consistent. UserBase.name is Optional, BaseMainResponseSchema.name is not.
    # Let's make UserResponse.name align with UserBase (Optional).
    name: Optional[str] = Field(None, max_length=255, description="Display name of the user.", example="JohnnyD")
    email: EmailStr = Field(..., description="User's email address.", example="user@example.com") # Email is not optional in response

    is_active: bool = Field(..., description="Is the user account active?")
    is_superuser: bool = Field(..., description="Does the user have superuser privileges?")
    user_type_code: Optional[str] = Field(None, description="Code for user type (e.g., 'human', 'bot').", example="human") # Populated from user.user_type.code
    last_login_at: Optional[datetime] = Field(None, description="Timestamp of the user's last successful login (UTC).")
    email_verified_at: Optional[datetime] = Field(None, description="Timestamp when email was verified (UTC).")
    phone_verified_at: Optional[datetime] = Field(None, description="Timestamp when phone was verified (UTC).")
    avatar_url: Optional[str] = Field(None, description="URL to the user's avatar image.") # To be populated by service/resolver

class UserPublicProfileResponse(BaseSchema):
    """
    Schema for a restricted public view of a user's profile.
    """
    id: int = Field(..., description="User's unique ID.", example=42)
    name: Optional[str] = Field(None, description="User's display name (or full name if preferred for public display).", example="Jane D.")
    avatar_url: Optional[str] = Field(None, description="URL to the user's avatar image.")
    # Optionally, include other fields like a short bio (description from UserBase) or join date (created_at from UserBase).
    # description: Optional[str] = Field(None, description="User's public bio.")
    # member_since: Optional[datetime] = Field(None, description="Date user joined.")


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- User Schemas --- Demonstration")

    # UserCreate
    user_create_data = {"email": "admin@example.com", "password": "SecurePass123!", "firstName": "Admin", "isSuperuser": True, "userTypeCode": "admin_user_type_code"}
    try:
        uc_schema = UserCreate(**user_create_data) # type: ignore[call-arg] # For Pydantic aliases
        logger.info(f"UserCreate valid: {uc_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"UserCreate error: {e}")

    # UserRegister
    user_reg_data = {"email": "new@example.com", "password": "RegP@ss1", "passwordConfirm": "RegP@ss1", "firstName": "Newbie"}
    try:
        ur_schema = UserRegister(**user_reg_data)
        logger.info(f"UserRegister valid: {ur_schema.model_dump(exclude={'password_confirm'}, by_alias=True)}")
    except Exception as e:
        logger.error(f"UserRegister error: {e}")

    user_reg_mismatch_data = {"email": "mismatch@example.com", "password": "Pass1", "passwordConfirm": "Pass2"}
    try:
        UserRegister(**user_reg_mismatch_data)
    except ValueError as e:
        logger.info(f"UserRegister caught expected password mismatch: {e}")

    # UserUpdate
    user_update_data = {"lastName": "Smith", "phoneNumber": "+15559876543"}
    uu_schema = UserUpdate(**user_update_data) # type: ignore[call-arg]
    logger.info(f"UserUpdate valid (partial): {uu_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # UserAdminUpdate
    user_admin_update_data = {"email": "updated.admin@example.com", "isActive": False, "state": "suspended"}
    uau_schema = UserAdminUpdate(**user_admin_update_data) # type: ignore[call-arg]
    logger.info(f"UserAdminUpdate valid (partial): {uau_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # UserPasswordUpdate
    user_pass_update_data = {"currentPassword": "OldPass!", "newPassword": "NewP@ss1", "newPasswordConfirm": "NewP@ss1"}
    try:
        upu_schema = UserPasswordUpdate(**user_pass_update_data) # type: ignore[call-arg]
        logger.info(f"UserPasswordUpdate valid: {upu_schema.model_dump(exclude={'current_password', 'new_password', 'new_password_confirm'}, by_alias=True)}")
    except Exception as e:
        logger.error(f"UserPasswordUpdate error: {e}")

    # UserResponse
    user_resp_data = {
        "id": 1, "createdAt": datetime.now(timezone.utc), "updatedAt": datetime.now(timezone.utc), "deletedAt": None,
        "email": "user@example.com", "name": "User FullName", "firstName": "User", "lastName": "FullName",
        "description": "User's bio.", "state": "active", "notes": "Some notes.",
        "isActive": True, "isSuperuser": False, "userTypeCode": "human",
        "lastLoginAt": datetime.now(timezone.utc), "emailVerifiedAt": datetime.now(timezone.utc),
        "phoneVerifiedAt": None, "avatarUrl": "https://example.com/avatar.png"
    }
    uresp_schema = UserResponse(**user_resp_data) # type: ignore[call-arg]
    logger.info(f"UserResponse: {uresp_schema.model_dump_json(by_alias=True, indent=2)}")

    # UserPublicProfileResponse
    user_public_data = {"id": 2, "name": "Anonymous User", "avatarUrl": "https://example.com/public_avatar.png"}
    upubresp_schema = UserPublicProfileResponse(**user_public_data) # type: ignore[call-arg]
    logger.info(f"UserPublicProfileResponse: {upubresp_schema.model_dump_json(by_alias=True, indent=2)}")
