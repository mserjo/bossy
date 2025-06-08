# backend/app/src/repositories/files/__init__.py

"""
This package contains repository classes for file-related entities.

Modules within this package will define repositories for managing file metadata,
user avatars, and potentially other file associations.
"""

# Import and re-export repository classes here as they are created.
# This allows for cleaner imports from other parts of the application,
# e.g., `from app.src.repositories.files import FileRecordRepository`.

from .file_record_repository import FileRecordRepository
from .user_avatar_repository import UserAvatarRepository


# Define __all__ to specify which names are exported when `from .files import *` is used.
# This also helps linters and IDEs understand the public API of this package.
__all__ = [
    "FileRecordRepository",
    "UserAvatarRepository",
]

# Detailed comments:
# This __init__.py file initializes the 'files' sub-package within the
# 'repositories' package. Its primary roles are:
#
# 1. Package Recognition:
#    It makes Python treat the 'repositories/files' directory as a sub-package.
#
# 2. Namespace Management:
#    It serves as a central point for importing and re-exporting repository
#    classes defined in other modules within this sub-package. This simplifies
#    access for other application layers.
#
# 3. Public API Definition (`__all__`):
#    The `__all__` list explicitly declares which symbols are part of the public
#    interface of this sub-package.
#
# This structure promotes a clean and organized data access layer for
# file management components.
