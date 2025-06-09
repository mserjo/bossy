# backend/app/src/core/constants.py

"""
Цей модуль визначає глобальні константи, що використовуються в усій програмі.
Константи допомагають підтримувати узгодженість та полегшують оновлення
глобальних значень з єдиного джерела.
"""

# --- Загальні константи програми ---
PROJECT_NAME: str = "Kudos" # Також може бути отримано з налаштувань, якщо потребує залежності від середовища
API_PREFIX: str = "/api" # Загальний префікс для всіх версій API
API_V1_STR: str = "/api/v1" # Специфічний префікс для API версії 1

# --- Константи пагінації ---
DEFAULT_PAGE_NUMBER: int = 1
DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100
MIN_PAGE_SIZE: int = 1

# --- Регулярні вирази ---
# Приклад: Базовий regex для email (для валідації не через Pydantic, Pydantic має власний EmailStr)
# EMAIL_REGEX: str = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
# Приклад: Regex для імені користувача (буквено-цифрові символи, підкреслення, дефіси, 3-20 символів)
USERNAME_REGEX: str = r"^[a-zA-Z0-9_-]{3,20}$"
# Regex для надійного пароля: щонайменше 8 символів, 1 велика літера, 1 маленька літера, 1 цифра, 1 спеціальний символ
PASSWORD_REGEX: str = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&_])[A-Za-z\d@$!%*?&_]{8,128}$"

# --- Значення за замовчуванням для моделей ---
DEFAULT_USERNAME_PREFIX: str = "user_"
DEFAULT_GROUP_NAME: str = "Моя група"
DEFAULT_TASK_POINTS: int = 10
DEFAULT_AVATAR_FILENAME: str = "default_avatar.png"

# --- Константи файлової системи ---
# Їх краще розміщувати в налаштуваннях, якщо вони змінюються залежно від середовища,
# але можуть бути тут, якщо це фіксовані структурні константи.
# UPLOAD_DIRECTORY: str = "uploads"
# AVATARS_SUBDIRECTORY: str = "avatars"
# GROUP_ICONS_SUBDIRECTORY: str = "group_icons"
# REWARD_ICONS_SUBDIRECTORY: str = "reward_icons"

# --- Константи, пов'язані з кешем ---
CACHE_DEFAULT_TTL_SECONDS: int = 300  # Час життя за замовчуванням для записів у кеші (5 хвилин)
CACHE_KEY_PREFIX_USER: str = "user_"
CACHE_KEY_PREFIX_GROUP: str = "group_"
CACHE_KEY_PREFIX_TASK: str = "task_"

# --- Константи, пов'язані із завданнями/подіями ---
TASK_MAX_DESCRIPTION_LENGTH: int = 5000
EVENT_MAX_NAME_LENGTH: int = 255

# --- Ролі користувачів (якщо не використовуються Enum з dicts.py або ролі з БД тут активно) ---
# Їх часто краще визначати як Enum (див. dicts.py) або з моделі/таблиці UserRole
# ROLE_SUPERUSER: str = "superuser"
# ROLE_ADMIN: str = "admin"
# ROLE_USER: str = "user"
# ROLE_BOT: str = "bot"

# --- Імена/ID системних користувачів (якщо фіксовані, а не лише в налаштуваннях) ---
# SYSTEM_USER_ODIN_NAME: str = "odin"
# SYSTEM_USER_SHADOW_NAME: str = "shadow"

# --- Інші константи ---
# Приклад: константа для назви конкретного прапорця функції
FEATURE_NEW_DASHBOARD_ENABLED: str = "NEW_DASHBOARD_FEATURE_FLAG"


if __name__ == "__main__":
    print("--- Основні константи ---")
    print(f"PROJECT_NAME: {PROJECT_NAME}")
    print(f"API_V1_STR: {API_V1_STR}")
    print(f"DEFAULT_PAGE_SIZE: {DEFAULT_PAGE_SIZE}")
    print(f"PASSWORD_REGEX: {PASSWORD_REGEX}")
    print(f"CACHE_DEFAULT_TTL_SECONDS: {CACHE_DEFAULT_TTL_SECONDS}")
