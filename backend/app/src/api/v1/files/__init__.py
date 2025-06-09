# backend/app/src/api/v1/files/__init__.py
from fastapi import APIRouter

# Імпортуємо роутери з файлів цього модуля
from .uploads import router as uploads_router
from .avatars import router as avatars_router
from .files import router as general_files_router # Роутер для загальних операцій з файлами (/{file_id})

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних з файлами
files_router = APIRouter()

# Підключення роутера для завантаження файлів
files_router.include_router(uploads_router, prefix="/uploads", tags=["File Uploads"])

# Підключення роутера для управління аватарами
files_router.include_router(avatars_router, prefix="/avatars", tags=["User Avatars"])

# Підключення роутера для загальних операцій з файлами (наприклад, отримання/видалення FileRecord)
# Цей роутер має шляхи типу /{file_id}, тому він підключається без додаткового префіксу тут.
# Загальний префікс /files буде застосовано при підключенні files_router до v1_router.
files_router.include_router(general_files_router, tags=["File Records Management"])


# Експортуємо files_router для використання в головному v1_router (app/src/api/v1/router.py)
__all__ = ["files_router"]
