# backend/app/src/core/dependencies.py

"""
This module defines common FastAPI dependencies, particularly for authentication
and authorization, such as retrieving the current user from a token.
"""

from typing import Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import BaseModel, ValidationError # Added BaseModel for TokenPayload
from datetime import datetime, timezone, timedelta # Added for __main__ example

from backend.app.src.config.settings import settings
from backend.app.src.config.security import decode_token
from backend.app.src.config.database import get_db, AsyncSession
# It's common to import user models and service/repository for fetching user data
# For now, we'll use a placeholder. These should be replaced with actual imports
# from backend.app.src.models.auth import User as UserModel # Placeholder
# from backend.app.src.services.auth.user import UserService # Placeholder
# from backend.app.src.schemas.auth.token import TokenPayload # Placeholder for token payload schema

# This is a placeholder for the actual User model. Replace with your User model import.
class UserModel:
    id: int
    email: str
    is_active: bool
    is_superuser: bool
    # Add other relevant fields like roles, group memberships etc.
    def __init__(self, id: int, email: str, is_active: bool = True, is_superuser: bool = False):
        self.id = id
        self.email = email
        self.is_active = is_active
        self.is_superuser = is_superuser

# This is a placeholder for the actual TokenPayload schema. Replace with your Pydantic schema.
class TokenPayload(BaseModel): # Inheriting from BaseModel
    sub: Optional[str] = None # 'sub' usually stores the user identifier (e.g., email or user_id)
    user_id: Optional[int] = None # Or use user_id directly if that's your 'sub'
    type: Optional[str] = None # To distinguish between access and refresh tokens

# OAuth2PasswordBearer is a FastAPI utility class that handles extracting the token
# from the Authorization header (Bearer token).
# The `tokenUrl` should point to your login endpoint where tokens are issued.
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login" # Example login endpoint
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> UserModel: # Should return your actual User model type
    """
    FastAPI dependency to get the current user from a JWT token.

    Args:
        db (AsyncSession): Database session dependency.
        token (str): The JWT token extracted from the Authorization header.

    Returns:
        UserModel: The authenticated user object from the database.

    Raises:
        HTTPException (401): If the token is invalid, expired, or the user is not found.
        HTTPException (400): If the token payload is malformed.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    malformed_payload_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Malformed token payload"
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    try:
        token_data = TokenPayload(**payload)
    except ValidationError:
        raise malformed_payload_exception

    if token_data.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, expected 'access' token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_identifier = token_data.sub or (str(token_data.user_id) if token_data.user_id else None)
    if user_identifier is None:
        raise malformed_payload_exception

    # --- Fetch user from database ---
    # This part needs to be adapted to your actual user service/repository logic.
    # user_service = UserService(db) # Example instantiation
    # current_user = await user_service.get_user_by_email(email=user_identifier) # If 'sub' is email
    # Or: current_user = await user_service.get_user_by_id(id=int(user_identifier)) # If 'sub' is user_id

    # Placeholder user fetching logic:
    # In a real app, you would query the database using the user_identifier from the token.
    # For demonstration, we'll create a dummy user if the identifier matches a pattern.
    # Replace this with actual database lookup.
    if user_identifier == "testuser@example.com" or user_identifier == "123":
        # This is a dummy user. Replace with actual DB lookup.
        # Ensure the UserModel structure matches your actual User model.
        current_user = UserModel(id=123, email="testuser@example.com", is_active=True)
    elif user_identifier == settings.FIRST_SUPERUSER_EMAIL:
        current_user = UserModel(id=1, email=settings.FIRST_SUPERUSER_EMAIL, is_active=True, is_superuser=True)
    else:
        current_user = None # User not found
    # --- End of placeholder user fetching logic ---

    if current_user is None:
        raise credentials_exception # User not found in DB

    return current_user

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    FastAPI dependency to get the current active user.
    Builds on `get_current_user` and checks if the user is active.

    Args:
        current_user (UserModel): The user object obtained from `get_current_user`.

    Returns:
        UserModel: The authenticated and active user object.

    Raises:
        HTTPException (403): If the user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user

async def get_current_superuser(
    current_active_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """
    FastAPI dependency to get the current active superuser.
    Builds on `get_current_active_user` and checks if the user is a superuser.

    Args:
        current_active_user (UserModel): The user object from `get_current_active_user`.

    Returns:
        UserModel: The authenticated, active, and superuser object.

    Raises:
        HTTPException (403): If the user is not a superuser.
    """
    if not hasattr(current_active_user, 'is_superuser') or not current_active_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user does not have superuser privileges."
        )
    return current_active_user

# Placeholder for Group Admin dependency - this will need more context
# from backend.app.src.models.groups import GroupMembershipModel # Placeholder
# from backend.app.src.core.dicts import GroupRole # Placeholder

# async def get_current_group_admin(
#     current_active_user: UserModel = Depends(get_current_active_user),
#     group_id: int = Path(..., title="The ID of the group"), # Assuming group_id is a path parameter
#     db: AsyncSession = Depends(get_db)
# ) -> UserModel:
#     """
#     FastAPI dependency to check if the current user is an admin of a specific group.
#     This is a more complex dependency and needs your actual GroupMembership model and logic.
#     """
#     # Example logic (needs your actual models and repository/service):
#     # membership = await GroupMembershipRepository(db).get_by_user_and_group(
#     # user_id=current_active_user.id, group_id=group_id
#     # )
#     # if not membership or membership.role != GroupRole.ADMIN:
#     #     raise HTTPException(
#     # status_code=status.HTTP_403_FORBIDDEN,
#     # detail="User is not an admin of this group."
#     #     )
#     # return current_active_user
#     # For now, let's make it pass if the user is a superuser for testing purposes
#     if hasattr(current_active_user, 'is_superuser') and current_active_user.is_superuser:
#         return current_active_user
#     raise HTTPException(status_code=403, detail="Not a group admin (placeholder logic)")


if __name__ == "__main__":
    # This module defines dependencies for FastAPI and is not typically run directly.
    # Testing these dependencies usually involves integration tests with a FastAPI test client.
    print("--- Core Dependencies (for FastAPI) ---")
    print("OAuth2PasswordBearer instance created for token URL:")
    print(f"  reusable_oauth2.scheme.tokenUrl = {reusable_oauth2.scheme.tokenUrl}")

    print("\nDefined dependencies:")
    print("- get_current_user: Decodes token, fetches user from DB (placeholder).")
    print("- get_current_active_user: Ensures user from get_current_user is active.")
    print("- get_current_superuser: Ensures user from get_current_active_user is a superuser.")
    # print("- get_current_group_admin: Placeholder for group admin check.")

    print("\nNote: To test these, you'd typically use FastAPI's TestClient and mock database/token interactions.")

    # Example of how TokenPayload might be used (though it's usually internal to get_current_user)
    try:
        payload_data = {"sub": "user@example.com", "user_id": 1, "type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
        token_payload_instance = TokenPayload(**payload_data)
        print(f"\nExample TokenPayload instance: {token_payload_instance.model_dump_json(indent=2)}")
    except ValidationError as e:
        print(f"\nError creating TokenPayload instance: {e}")

    # The actual UserModel would come from your models.auth.user module
    # This is just to show the placeholder class structure
    print(f"\nPlaceholder UserModel structure: id, email, is_active, is_superuser")
    dummy_user = UserModel(id=1, email="dummy@example.com", is_active=True, is_superuser=False)
    print(f"  Dummy user: id={dummy_user.id}, email='{dummy_user.email}', active={dummy_user.is_active}")
