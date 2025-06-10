# backend/app/src/schemas/auth/session.py

"""
Pydantic schemas for User Session information, if exposed via API.
"""

import logging
from typing import Optional
from datetime import datetime, timezone, timedelta # Added timezone, timedelta for __main__

from pydantic import Field

from backend.app.src.schemas.base import BaseSchema, BaseResponseSchema # For UserSessionResponse

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- UserSession Schemas ---

class UserSessionBase(BaseSchema):
    """
    Base schema for user session data. Contains fields that might be part of a response.
    Does not include sensitive parts of the session like the full session_id if it's a secret.
    """
    # id: int # This would come from BaseResponseSchema if used for response
    # user_id: int # Typically not exposed directly in a list of *my* sessions, but an admin might see it.
    ip_address: Optional[str] = Field(None, description="IP address from which the session originated.", example="203.0.113.45")
    user_agent: Optional[str] = Field(None, description="User agent string of the client for this session.", example="Chrome on Windows")
    last_activity_at: datetime = Field(..., description="Timestamp of the last recorded activity for this session (UTC).", example=datetime.now(timezone.utc))
    expires_at: datetime = Field(..., description="Timestamp when this session will/did expire (UTC).", example=datetime.now(timezone.utc) + timedelta(hours=1))
    # created_at: datetime # From BaseResponseSchema
    # updated_at: datetime # From BaseResponseSchema
    is_current_session: Optional[bool] = Field(None, description="Indicates if this is the session making the current request (populated by endpoint logic).", example=True)

class UserSessionResponse(BaseResponseSchema, UserSessionBase):
    """
    Schema for representing a user session in API responses (e.g., listing active sessions for a user).
    Includes 'id', 'created_at', 'updated_at' from BaseResponseSchema.
    """
    # Fields inherited from UserSessionBase and BaseResponseSchema (id, created_at, updated_at)
    # We might want to be more specific about which fields are included from UserSessionBase here.
    # For example, if user_id should be part of an admin view of sessions:
    # user_id: Optional[int] = Field(None, description="ID of the user this session belongs to (for admin views).")
    pass

# No Create or Update schemas are typically defined for UserSession from an API perspective,
# as sessions are usually managed implicitly by login/logout and token mechanisms or server-side.
# If an admin could manually invalidate a session, a SessionTerminateRequest might exist.

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- UserSession Schemas --- Demonstration")

    # UserSessionResponse Example
    session_response_data = {
        "id": 1001,
        "createdAt": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        "updatedAt": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        "ipAddress": "192.168.1.10", # camelCase for input if populate_by_name is True in BaseSchema
        "userAgent": "Firefox on Linux",
        "lastActivityAt": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        "expiresAt": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "isCurrentSession": True
    }
    try:
        session_resp_schema = UserSessionResponse(**session_response_data) # type: ignore[call-arg]
        logger.info(f"UserSessionResponse: {session_resp_schema.model_dump_json(by_alias=True, indent=2)}")
        logger.info(f"  IP Address (from alias 'ipAddress'): {session_resp_schema.ip_address}") # Access via Python name
        logger.info(f"  Is Current Session (from alias 'isCurrentSession'): {session_resp_schema.is_current_session}")
    except Exception as e:
        logger.error(f"Error creating UserSessionResponse: {e}")

    another_session_data = {
        "id": 1002,
        "created_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(), # Using pythonic name
        "updated_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), # Using pythonic name
        "ip_address": "2001:db8::1", # IPv6 example, pythonic name
        "user_agent": "Safari on macOS",
        "last_activity_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=6)).isoformat(),
        "is_current_session": False
    }
    try:
        # Demonstrating with pythonic names, which also works.
        # Pydantic's populate_by_name in BaseSchema allows either alias or field name if no conflict.
        another_session_schema = UserSessionResponse(**another_session_data)
        logger.info(f"Another UserSessionResponse (using pythonic names): {another_session_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating another UserSessionResponse: {e}")
