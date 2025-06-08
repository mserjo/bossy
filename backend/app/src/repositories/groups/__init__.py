# backend/app/src/repositories/groups/__init__.py

"""
This package contains repository classes for group-related entities.

Modules within this package will define repositories for groups, memberships,
invitations, group settings, etc.
"""

# Import and re-export repository classes here as they are created.
# This allows for cleaner imports from other parts of the application,
# e.g., `from app.src.repositories.groups import GroupRepository`.

from .group_repository import GroupRepository
from .membership_repository import GroupMembershipRepository
from .invitation_repository import GroupInvitationRepository
from .settings_repository import GroupSettingRepository


# Define __all__ to specify which names are exported when `from .groups import *` is used.
# This also helps linters and IDEs understand the public API of this package.
__all__ = [
    "GroupRepository",
    "GroupMembershipRepository",
    "GroupInvitationRepository",
    "GroupSettingRepository",
]

# Detailed comments:
# This __init__.py file initializes the 'groups' sub-package within the
# 'repositories' package. Its primary roles are:
#
# 1. Package Recognition:
#    It makes Python treat the 'repositories/groups' directory as a sub-package.
#
# 2. Namespace Management:
#    It serves as a central point for importing and re-exporting repository
#    classes defined in other modules within this sub-package. This simplifies
#    access for other application layers. For instance, instead of:
#    `from app.src.repositories.groups.group_repository import GroupRepository`
#    you can use:
#    `from app.src.repositories.groups import GroupRepository`
#    (once GroupRepository is defined and uncommented above).
#
# 3. Public API Definition (`__all__`):
#    The `__all__` list explicitly declares which symbols are part of the public
#    interface of this sub-package.
#
# This structure promotes a clean and organized data access layer for
# group-related components.
