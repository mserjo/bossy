# backend/app/src/repositories/dictionaries/__init__.py

"""
This package contains repository classes for dictionary (lookup) entities.

Each module within this package should define a repository class for a specific
dictionary model (e.g., StatusRepository, UserRoleRepository), typically
inheriting from a common BaseDictionaryRepository.
"""

# Import and re-export repository classes here as they are created.
# This allows for cleaner imports from other parts of the application,
# e.g., `from app.src.repositories.dictionaries import StatusRepository`.

from .base_dict_repository import BaseDictionaryRepository
from .status_repository import StatusRepository
from .user_role_repository import UserRoleRepository
from .user_type_repository import UserTypeRepository
from .group_type_repository import GroupTypeRepository
from .task_type_repository import TaskTypeRepository
from .bonus_type_repository import BonusTypeRepository
from .calendar_provider_repository import CalendarProviderRepository
from .messenger_platform_repository import MessengerPlatformRepository


# Define __all__ to specify which names are exported when `from .dictionaries import *` is used.
# This also helps linters and IDEs understand the public API of this package.
__all__ = [
    "BaseDictionaryRepository",
    "StatusRepository",
    "UserRoleRepository",
    "UserTypeRepository",
    "GroupTypeRepository",
    "TaskTypeRepository",
    "BonusTypeRepository",
    "CalendarProviderRepository",
    "MessengerPlatformRepository",
]

# Detailed comments:
# This __init__.py file initializes the 'dictionaries' sub-package within the
# 'repositories' package. Its primary roles are:
#
# 1. Package Recognition:
#    It makes Python treat the 'repositories/dictionaries' directory as a sub-package,
#    enabling structured imports and organization of dictionary-specific repositories.
#
# 2. Namespace Management:
#    It serves as a central point for importing and re-exporting the repository
#    classes defined in other modules within this sub-package. This simplifies
#    access for other application layers. For instance, instead of:
#    `from app.src.repositories.dictionaries.status_repository import StatusRepository`
#    you can use:
#    `from app.src.repositories.dictionaries import StatusRepository`
#    (once StatusRepository is defined and uncommented above).
#
# 3. Public API Definition (`__all__`):
#    The `__all__` list explicitly declares which symbols are part of the public
#    interface of this sub-package. This is good practice for package maintainability
#    and clarity. When new repositories are added to this sub-package (like
#    StatusRepository), they should be imported here and their names added to
#    the `__all__` list.
#
# This approach ensures that the dictionary repositories are well-organized and
# easily accessible throughout the application while maintaining a clear structure.
