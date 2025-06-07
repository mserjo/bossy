# backend/app/src/schemas/auth/__init__.py

"""
This package contains Pydantic schemas related to user authentication,
authorization, user profiles, tokens, and session management.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Authentication schemas package initialized.")

# Example of re-exporting for easier access:
# from .user import UserResponse, UserCreate, UserUpdate
# from .token import TokenResponse, TokenPayload
# from .login import LoginRequest

# __all__ = [
#     "UserResponse",
#     "UserCreate",
#     "UserUpdate",
#     "TokenResponse",
#     "TokenPayload",
#     "LoginRequest",
#     # ... other auth schemas
# ]
