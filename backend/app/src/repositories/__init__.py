# backend/app/src/repositories/__init__.py
from .base import BaseRepository

# Import system repositories
from .system.settings_repository import SystemSettingRepository
from .system.monitoring_repository import SystemLogRepository, PerformanceMetricRepository
from .system.health_repository import ServiceHealthRepository

# Import dictionary repositories
from .dictionaries.base_dict_repository import BaseDictionaryRepository
from .dictionaries.status_repository import StatusRepository
from .dictionaries.user_role_repository import UserRoleRepository
from .dictionaries.user_type_repository import UserTypeRepository
from .dictionaries.group_type_repository import GroupTypeRepository
from .dictionaries.task_type_repository import TaskTypeRepository
from .dictionaries.bonus_type_repository import BonusTypeRepository
from .dictionaries.calendar_provider_repository import CalendarProviderRepository
from .dictionaries.messenger_platform_repository import MessengerPlatformRepository

# Import auth repositories
from .auth import UserRepository, RefreshTokenRepository, UserSessionRepository

# Import group repositories
from .groups import GroupRepository, GroupMembershipRepository, GroupInvitationRepository, GroupSettingRepository

# Import task repositories
from .tasks import TaskRepository, EventRepository, TaskAssignmentRepository, TaskCompletionRepository

# Import bonus repositories
from .bonuses import BonusRuleRepository, UserAccountRepository, AccountTransactionRepository, RewardRepository

# Import gamification repositories
from .gamification import LevelRepository, UserLevelRepository, BadgeRepository

# Import notification repositories
from .notifications import NotificationTemplateRepository, NotificationRepository, NotificationDeliveryAttemptRepository

# Import file repositories
from .files import FileRecordRepository, UserAvatarRepository

# This line exports the BaseRepository class when the package is imported,
# making it available as `from app.src.repositories import BaseRepository`.

# When you create specific repositories, you will import and export them here
# to make them easily accessible from the repositories package.
# For example:
# from .user_repository import UserRepository # Will be in auth folder
# from .item_repository import ItemRepository # Example, if not categorized

# __all__ defines the public API of this package.
# When a client uses `from app.src.repositories import *`, only names listed
# in `__all__` will be imported.
__all__ = [
    "BaseRepository",
    # System Repositories
    "SystemSettingRepository",
    "SystemLogRepository",
    "PerformanceMetricRepository",
    "ServiceHealthRepository",
    # Dictionary Repositories
    "BaseDictionaryRepository",
    "StatusRepository",
    "UserRoleRepository",
    "UserTypeRepository",
    "GroupTypeRepository",
    "TaskTypeRepository",
    "BonusTypeRepository",
    "CalendarProviderRepository",
    "MessengerPlatformRepository",
    # Auth Repositories
    "UserRepository", # This was already added in the previous incorrect diff, so it's fine.
    "RefreshTokenRepository",
    "UserSessionRepository",
    # Group Repositories
    "GroupRepository",
    "GroupMembershipRepository",
    "GroupInvitationRepository",
    "GroupSettingRepository",
    # Task Repositories
    "TaskRepository",
    "EventRepository",
    "TaskAssignmentRepository",
    "TaskCompletionRepository",
    # Bonus Repositories
    "BonusRuleRepository",
    "UserAccountRepository",
    "AccountTransactionRepository",
    "RewardRepository",
    # Gamification Repositories
    "LevelRepository",
    "UserLevelRepository",
    "BadgeRepository",
    # Notification Repositories
    "NotificationTemplateRepository",
    "NotificationRepository",
    "NotificationDeliveryAttemptRepository",
    # File Repositories
    "FileRecordRepository",
    "UserAvatarRepository",
    # Add other main repository class names here as they are created
]

# Detailed comments:
# This __init__.py file serves as the main entry point for the 'repositories' package.
#
# Key Functions:
# 1. Package Initialization:
#    Allows Python to treat the 'repositories' directory as a package, enabling
#    organized imports of repository modules.
#
# 2. Centralized Access to Repositories:
#    It imports and re-exports repository classes from its sub-packages (like
#    `system` and `dictionaries`) and also any repositories defined directly
#    under `repositories` (like `BaseRepository`). This provides a single,
#    consistent point of access for other parts of the application. For example,
#    services can import any repository using:
#    `from app.src.repositories import SystemSettingRepository`
#    `from app.src.repositories import StatusRepository`
#     `from app.src.repositories import UserRepository`
#
# 3. Public API Control (`__all__`):
#    The `__all__` list explicitly defines which symbols are part of this package's
#    public interface. This is crucial for:
#    - Clarity: Makes it clear which repositories are intended for external use.
#    - Namespace Management: Prevents accidental import of internal variables or
#      modules when `from app.src.repositories import *` is used (though wildcard
#      imports are generally discouraged in production code).
#    - Tooling: Helps linters, IDEs, and documentation generators understand the
#      package structure and public API.
#
# How to Extend:
# - Base Repositories: If new base repository types are created (e.g., `BaseServiceAccessRepository`),
#   define them in a `.py` file in this directory and add them here.
# - Specific Entity Repositories (e.g., User, Task, Group):
#   - Categorize them into sub-packages if logical (e.g., `auth`, `tasks`, `groups`).
#   - Create an `__init__.py` in each sub-package to export its repositories.
#   - Import the specific repositories from their sub-packages into this top-level
#     `__init__.py` file and add their names to the `__all__` list.
#   - Example (for UserRepository in `repositories/auth/user_repository.py`):
#     ```python
#     # In repositories/auth/__init__.py:
#     from .user_repository import UserRepository
#     __all__ = ["UserRepository"]
#
#     # In this file (repositories/__init__.py):
#     from .auth import UserRepository # Assuming auth/__init__.py exports it
#     # ...
#     __all__.append("UserRepository") # Or directly include as done above
#     ```
#
# This centralized approach promotes a clean, maintainable, and easily navigable
# data access layer.
