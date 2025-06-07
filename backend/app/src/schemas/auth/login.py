# backend/app/src/schemas/auth/login.py

"""
Pydantic schemas for user login and password management operations.
"""

import logging
from typing import Optional

from pydantic import Field, EmailStr, BaseModel, model_validator # BaseModel for simple request objects

from backend.app.src.schemas.base import BaseSchema # For consistency if any response uses BaseSchema features

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Login Schemas ---

class LoginRequest(BaseModel): # Does not necessarily need BaseSchema unless aliases or ORM mode are used
    """
    Schema for user login request.
    Corresponds to what OAuth2PasswordRequestForm typically expects (username, password),
    but defined as a Pydantic model for clarity and potential extensions (e.g., OTP code).
    'username' here can be an email or a dedicated username string.
    """
    username: str = Field(..., description="User's email or username for login.", example="user@example.com")
    password: str = Field(..., description="User's password.", example="s3crEtP@sswOrd")
    # otp_code: Optional[str] = Field(None, description="One-Time Password, if 2FA is enabled.") # Example extension

# TokenResponse is already defined in schemas.auth.token and would be the typical response for a successful login.

# --- Password Management Schemas ---

class PasswordResetRequest(BaseModel):
    """
    Schema for requesting a password reset.
    User provides their email to receive reset instructions.
    """
    email: EmailStr = Field(..., description="Email address of the user requesting password reset.", example="forgot.my.password@example.com")

class PasswordResetConfirm(BaseModel):
    """
    Schema for confirming a password reset using a token and new password.
    If this schema is used in an API that expects camelCase, it should inherit from BaseSchema
    or define field aliases manually. For this example, using Pythonic names.
    """
    reset_token: str = Field(..., description="The password reset token received by the user (e.g., via email).", alias="resetToken")
    new_password: str = Field(..., min_length=8, description="The new desired password.", alias="newPassword")
    new_password_confirm: str = Field(..., description="Confirmation of the new password.", alias="newPasswordConfirm")

    model_config = { # Pydantic V2 ConfigDict
        "populate_by_name": True # Allows using aliases in input data
    }

    @model_validator(mode='after')
    def check_new_passwords_match(self) -> 'PasswordResetConfirm':
        if self.new_password is not None and self.new_password_confirm is not None:
            if self.new_password != self.new_password_confirm:
                raise ValueError("New passwords do not match")
        return self

# MessageResponse from schemas.base can be used for simple confirmation messages after these operations.

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Login & Password Management Schemas --- Demonstration")

    # LoginRequest Example
    login_data = {"username": "test@example.com", "password": "password123"}
    try:
        login_schema = LoginRequest(**login_data)
        logger.info(f"LoginRequest valid: {login_schema.model_dump()}")
    except Exception as e:
        logger.error(f"Error creating LoginRequest: {e}")

    # PasswordResetRequest Example
    pw_reset_req_data = {"email": "user.who.forgot@example.com"}
    try:
        pw_reset_req_schema = PasswordResetRequest(**pw_reset_req_data)
        logger.info(f"PasswordResetRequest valid: {pw_reset_req_schema.model_dump()}")
    except Exception as e:
        logger.error(f"Error creating PasswordResetRequest: {e}")

    # PasswordResetConfirm Example
    pw_reset_confirm_data_camel = { # Input with camelCase aliases
        "resetToken": "a.valid.looking.reset.token.jwt",
        "newPassword": "NewStrongP@ss1!",
        "newPasswordConfirm": "NewStrongP@ss1!"
    }
    try:
        # PasswordResetConfirm now has model_config to handle camelCase aliases
        pw_reset_confirm_schema = PasswordResetConfirm(**pw_reset_confirm_data_camel)
        logger.info(f"PasswordResetConfirm valid (from camelCase): {pw_reset_confirm_schema.model_dump(exclude={'new_password', 'new_password_confirm'})}")
        logger.info(f"  Internal attribute (reset_token): {pw_reset_confirm_schema.reset_token}")

    except Exception as e:
        logger.error(f"Error creating PasswordResetConfirm: {e}")

    # PasswordResetConfirm mismatch example
    pw_reset_mismatch_data_camel = {
        "resetToken": "another.token",
        "newPassword": "PassA",
        "newPasswordConfirm": "PassB"
    }
    try:
        PasswordResetConfirm(**pw_reset_mismatch_data_camel)
    except ValueError as e:
        logger.info(f"PasswordResetConfirm caught expected password mismatch: {e}")
