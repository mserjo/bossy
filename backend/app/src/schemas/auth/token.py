# backend/app/src/schemas/auth/token.py

"""
Pydantic schemas for JWT (JSON Web Tokens) and token responses.
"""

import logging
from typing import Optional, List # Added List for TokenPayload.roles
from datetime import datetime, timedelta, timezone # Added timezone for examples

from pydantic import Field, BaseModel, ConfigDict # BaseModel for TokenPayload if it doesn't need BaseSchema config like alias gen

from backend.app.src.schemas.base import BaseSchema # For TokenResponse

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Token Schemas ---

class TokenPayload(BaseModel):
    """
    Schema for the data encoded within a JWT.
    This represents the standard claims plus any custom claims.
    It's used when decoding a token to validate its structure.
    """
    sub: Optional[str] = Field(None, description="Subject of the token (usually user ID or email)", example="user@example.com or 123")
    user_id: Optional[int] = Field(None, description="Explicit user ID if 'sub' is not the user ID itself.", example=123)
    # Standard JWT claims (optional)
    exp: Optional[int] = Field(None, description="Expiration time (Unix timestamp)", example=1678886400)
    iat: Optional[int] = Field(None, description="Issued at time (Unix timestamp)", example=1678882800)
    nbf: Optional[int] = Field(None, description="Not before time (Unix timestamp)", example=1678882800)
    jti: Optional[str] = Field(None, description="JWT ID, for unique identification of the token", example="abcdef123456")
    # Custom claims
    token_type: Optional[str] = Field(None, alias="type", description="Type of token (e.g., 'access', 'refresh')", example="access")
    roles: Optional[List[str]] = Field(None, description="List of user roles associated with the token", example=["user", "editor"])
    # Add other custom claims as needed (e.g., permissions, session_id)

    model_config = ConfigDict( # Updated to Pydantic V2 ConfigDict
        populate_by_name=True, # Allows using 'type' as field name but 'token_type' as Python attribute
        extra="ignore" # Ignore extra fields in payload not defined here
    )

class TokenResponse(BaseSchema):
    """
    Schema for returning access and refresh tokens to the client upon successful authentication.
    """
    access_token: str = Field(..., description="JWT access token for authenticating API requests.", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token for obtaining new access tokens.", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field("bearer", description="Type of token (always 'bearer' for OAuth2).", example="bearer")
    # Optional: expires_in (seconds until access_token expiry) or access_token_expires_at (datetime)
    # access_token_expires_at: Optional[datetime] = Field(None, description="Exact expiry datetime of the access token")
    # refresh_token_expires_at: Optional[datetime] = Field(None, description="Exact expiry datetime of the refresh token")

class RefreshTokenRequest(BaseModel): # Simple model, doesn't need BaseSchema config typically
    """
    Schema for the request body when refreshing an access token.
    """
    refresh_token: str = Field(..., description="The refresh token issued during login.")


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Token Schemas --- Demonstration")

    # TokenPayload Example
    payload_data = {
        "sub": "user123@example.com",
        "user_id": 123, # Pydantic V2 will map this to user_id if populate_by_name is True and no alias on field. If alias is on field, use alias.
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "jti": "a_unique_jwt_id",
        "type": "access", # This will map to token_type due to alias and populate_by_name
        "roles": ["user", "premium_member"]
    }
    try:
        token_payload_schema = TokenPayload(**payload_data)
        logger.info(f"TokenPayload valid: {token_payload_schema.model_dump(by_alias=True)}") # by_alias=True will show 'type'
        logger.info(f"  TokenPayload internal: {token_payload_schema.model_dump()}") # by_alias=False will show 'token_type'
        logger.info(f"  Token subject (sub): {token_payload_schema.sub}")
        logger.info(f"  Token user_id: {token_payload_schema.user_id}") # Access with Python name
        logger.info(f"  Token type (token_type): {token_payload_schema.token_type}") # Access with Python name
        if token_payload_schema.exp:
            logger.info(f"  Token expires at (datetime): {datetime.fromtimestamp(token_payload_schema.exp, timezone.utc).isoformat()}")
    except Exception as e:
        logger.error(f"Error creating TokenPayload: {e}")

    # TokenResponse Example
    token_response_data = {
        "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTYxNjQwNjQwMH0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTYxNzAxODAwMH0.somethinglongeranddifferent",
        "tokenType": "bearer"
    }
    try:
        token_response_schema = TokenResponse(**token_response_data) # type: ignore[call-arg]
        logger.info(f"TokenResponse: {token_response_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating TokenResponse: {e}")

    # RefreshTokenRequest Example
    refresh_request_data = {
        "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTYxNzAxODAwMH0.somethinglongeranddifferent"
    }
    try:
        refresh_request_schema = RefreshTokenRequest(**refresh_request_data) # type: ignore[call-arg]
        logger.info(f"RefreshTokenRequest: {refresh_request_schema.model_dump_json(by_alias=True, indent=2)}") # by_alias relevant if BaseSchema was used
    except Exception as e:
        logger.error(f"Error creating RefreshTokenRequest: {e}")
