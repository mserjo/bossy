# backend/app/src/core/constants.py

"""
This module defines global constants used throughout the application.
Constants help in maintaining consistency and make it easier to update
global values from a single source.
"""

# --- General Application Constants ---
PROJECT_NAME: str = "Kudos" # Could also be sourced from settings if it needs to be env-dependent
API_PREFIX: str = "/api" # General prefix for all API versions
API_V1_STR: str = "/api/v1" # Specific prefix for API version 1

# --- Pagination Constants ---
DEFAULT_PAGE_NUMBER: int = 1
DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100
MIN_PAGE_SIZE: int = 1

# --- Regular Expressions ---
# Example: Basic email regex (for non-Pydantic validation, Pydantic has its own EmailStr)
# EMAIL_REGEX: str = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
# Example: Username regex (alphanumeric, underscores, hyphens, 3-20 chars)
USERNAME_REGEX: str = r"^[a-zA-Z0-9_-]{3,20}$"
# Strong password regex: at least 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
PASSWORD_REGEX: str = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&_])[A-Za-z\d@$!%*?&_]{8,128}$"

# --- Default Values for Models ---
DEFAULT_USERNAME_PREFIX: str = "user_"
DEFAULT_GROUP_NAME: str = "My Group"
DEFAULT_TASK_POINTS: int = 10
DEFAULT_AVATAR_FILENAME: str = "default_avatar.png"

# --- File System Constants ---
# These might be better in settings if they vary by environment,
# but can be here if they are fixed structural constants.
# UPLOAD_DIRECTORY: str = "uploads"
# AVATARS_SUBDIRECTORY: str = "avatars"
# GROUP_ICONS_SUBDIRECTORY: str = "group_icons"
# REWARD_ICONS_SUBDIRECTORY: str = "reward_icons"

# --- Cache Related Constants ---
CACHE_DEFAULT_TTL_SECONDS: int = 300  # Default Time-To-Live for cache entries (5 minutes)
CACHE_KEY_PREFIX_USER: str = "user_"
CACHE_KEY_PREFIX_GROUP: str = "group_"
CACHE_KEY_PREFIX_TASK: str = "task_"

# --- Task/Event Related Constants ---
TASK_MAX_DESCRIPTION_LENGTH: int = 5000
EVENT_MAX_NAME_LENGTH: int = 255

# --- User Roles (if not using Enums from dicts.py or DB-driven roles extensively here) ---
# These are often better as Enums (see dicts.py) or from a UserRole model/table
# ROLE_SUPERUSER: str = "superuser"
# ROLE_ADMIN: str = "admin"
# ROLE_USER: str = "user"
# ROLE_BOT: str = "bot"

# --- System Usernames/IDs (if fixed and not only in settings) ---
# SYSTEM_USER_ODIN_NAME: str = "odin"
# SYSTEM_USER_SHADOW_NAME: str = "shadow"

# --- Other Constants ---
# Example: A constant for a specific feature flag name
FEATURE_NEW_DASHBOARD_ENABLED: str = "NEW_DASHBOARD_FEATURE_FLAG"


if __name__ == "__main__":
    print("--- Core Constants ---")
    print(f"PROJECT_NAME: {PROJECT_NAME}")
    print(f"API_V1_STR: {API_V1_STR}")
    print(f"DEFAULT_PAGE_SIZE: {DEFAULT_PAGE_SIZE}")
    print(f"PASSWORD_REGEX: {PASSWORD_REGEX}")
    print(f"CACHE_DEFAULT_TTL_SECONDS: {CACHE_DEFAULT_TTL_SECONDS}")
