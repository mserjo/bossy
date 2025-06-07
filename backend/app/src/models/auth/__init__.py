# backend/app/src/models/auth/__init__.py

"""
This package contains SQLAlchemy models related to authentication, authorization,
user accounts, sessions, and tokens.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Authentication models package initialized.")

# Example of re-exporting for easier access from other modules:
# from .user import User
# from .token import RefreshToken
# from .session import UserSession

# __all__ = [
#     "User",
#     "RefreshToken",
#     "UserSession",
# ]
