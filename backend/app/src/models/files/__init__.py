# backend/app/src/models/files/__init__.py

"""
This package contains SQLAlchemy models related to file uploads, storage records,
and associations like user avatars.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("File models package initialized.")

# Example of re-exporting for easier access:
# from .file import FileRecord
# from .avatar import UserAvatar

# __all__ = [
#     "FileRecord",
#     "UserAvatar",
# ]
