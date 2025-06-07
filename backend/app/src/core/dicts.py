# backend/app/src/core/dicts.py

"""
This module defines system-level enumerations (Enums) that represent fixed sets of choices
used within the application's business logic. These are distinct from dictionary models
that might be stored in the database and managed dynamically.
"""

from enum import Enum

class SortOrder(str, Enum):
    """Defines the sort order for query results."""
    ASC = "asc"         # Ascending order
    DESC = "desc"       # Descending order

class UserState(str, Enum):
    """Represents the possible states of a user account."""
    PENDING_VERIFICATION = "pending_verification" # User registered, email/phone not yet verified
    ACTIVE = "active"                     # User account is active and can be used
    INACTIVE = "inactive"                   # User account has been deactivated by an admin or user
    SUSPENDED = "suspended"                 # User account has been temporarily suspended by an admin
    BANNED = "banned"                     # User account has been permanently banned
    DELETED = "deleted"                   # User account is marked for deletion (soft delete)

class GroupRole(str, Enum):
    """Defines roles within a group."""
    ADMIN = "admin"       # Administrator of the group
    MEMBER = "member"     # Regular member of the group
    # GUEST = "guest"     # Optional: A guest role with limited permissions

class TaskStatus(str, Enum):
    """
    Represents the lifecycle status of a task.
    These are general statuses; specific applications might extend or specialize them.
    """
    OPEN = "open"                          # Task is available to be worked on
    IN_PROGRESS = "in_progress"            # Task is currently being worked on by a user
    PENDING_REVIEW = "pending_review"      # Task completion is submitted and awaits admin approval
    COMPLETED = "completed"                # Task has been successfully completed and verified
    REJECTED = "rejected"                  # Task completion was reviewed and rejected
    CANCELLED = "cancelled"                # Task has been cancelled before completion
    ON_HOLD = "on_hold"                    # Task is temporarily paused
    EXPIRED = "expired"                    # Task was not completed within its due date

class EventFrequency(str, Enum):
    """Defines how often a recurring task or event occurs."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    # CUSTOM = "custom" # For more complex recurrence patterns, usually needs more fields

class NotificationType(str, Enum):
    """Defines different types of notifications within the system."""
    GENERAL_INFO = "general_info"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED_USER = "task_completed_by_user" # User marked task as complete
    TASK_VERIFIED_ADMIN = "task_verified_by_admin" # Admin approved/rejected completion
    TASK_REMINDER = "task_reminder"
    BONUS_AWARDED = "bonus_awarded"
    REWARD_REDEEMED = "reward_redeemed"
    GROUP_INVITATION = "group_invitation"
    NEW_MEMBER_JOINED_GROUP = "new_member_joined_group"
    ACCOUNT_BALANCE_UPDATE = "account_balance_update"
    SYSTEM_ANNOUNCEMENT = "system_announcement"

class FileType(str, Enum):
    """Categorizes uploaded files."""
    AVATAR = "avatar"
    GROUP_ICON = "group_icon"
    REWARD_ICON = "reward_icon"
    BADGE_ICON = "badge_icon"
    TASK_ATTACHMENT = "task_attachment"
    GENERAL_DOCUMENT = "general_document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    OTHER = "other"

class TimePeriod(str, Enum):
    """Represents common time periods for reporting or filtering."""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    CURRENT_MONTH = "current_month"
    PREVIOUS_MONTH = "previous_month"
    CURRENT_YEAR = "current_year"
    ALL_TIME = "all_time"

# Add more Enums as needed for your application's core logic.
# Examples:
# class TransactionType(str, Enum):
#     CREDIT = "credit"
#     DEBIT = "debit"
#     REFUND = "refund"

# class LogLevel(str, Enum):
#     DEBUG = "debug"
#     INFO = "info"
#     WARNING = "warning"
#     ERROR = "error"
#     CRITICAL = "critical"

if __name__ == "__main__":
    print("--- Core Enums (Dictionaries) ---")

    print("\nUser States:")
    for state in UserState:
        print(f"- {state.name}: {state.value}")

    print("\nGroup Roles:")
    for role in GroupRole:
        print(f"- {role.name}: {role.value}")

    print("\nTask Statuses:")
    for status in TaskStatus:
        print(f"- {status.name}: {status.value}")

    print("\nSort Orders:")
    for order in SortOrder:
        print(f"- {order.name}: {order.value}")

    print("\nNotification Types:")
    for n_type in NotificationType:
        print(f"- {n_type.name}: {n_type.value}")

    print(f"\nAccessing a specific enum value: UserState.ACTIVE is '{UserState.ACTIVE.value}'")
