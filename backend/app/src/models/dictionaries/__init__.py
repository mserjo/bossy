# backend/app/src/models/dictionaries/__init__.py

"""
This package contains SQLAlchemy models for various dictionary or lookup tables.
These tables typically store predefined sets of values like statuses, types, roles, etc.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Dictionary models package initialized.")

# Example of re-exporting for easier access:
# from .base_dict import BaseDictionaryModel
# from .statuses import Status
# from .user_roles import UserRole
# ... and so on for other dictionary models

# __all__ = [
#     "BaseDictionaryModel",
#     "Status",
#     "UserRole",
#     # ... other model names
# ]
