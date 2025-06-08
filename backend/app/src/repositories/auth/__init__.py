# backend/app/src/repositories/auth/__init__.py

"""
This package contains repository classes for authentication and authorization-related entities.

Modules within this package will define repositories for users, tokens, sessions, etc.
"""

# Import and re-export repository classes here as they are created.
# This allows for cleaner imports from other parts of the application,
# e.g., `from app.src.repositories.auth import UserRepository`.

from .user_repository import UserRepository
from .refresh_token_repository import RefreshTokenRepository
from .session_repository import UserSessionRepository


# Define __all__ to specify which names are exported when `from .auth import *` is used.
# This also helps linters and IDEs understand the public API of this package.
__all__ = [
    "UserRepository",
    "RefreshTokenRepository",
    "UserSessionRepository",
]

# Detailed comments:
# This __init__.py file initializes the 'auth' sub-package within the
# 'repositories' package. Its primary roles are:
#
# 1. Package Recognition:
#    It makes Python treat the 'repositories/auth' directory as a sub-package.
#
# 2. Namespace Management:
#    It serves as a central point for importing and re-exporting repository
#    classes defined in other modules within this sub-package (e.g.,
#    `user_repository.py`). This simplifies access for other application layers.
#    For instance, instead of:
#    `from app.src.repositories.auth.user_repository import UserRepository`
#    you can use:
#    `from app.src.repositories.auth import UserRepository`
#    (once UserRepository is defined and uncommented above).
#
# 3. Public API Definition (`__all__`):
#    The `__all__` list explicitly declares which symbols are part of the public
#    interface of this sub-package.
#
# This structure promotes a clean and organized data access layer for
# authentication and authorization components.
