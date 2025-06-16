# backend/app/src/api/v1/files/__init__.py
# -*- coding: utf-8 -*-
"""
Агрегований роутер для всіх ендпоінтів, пов'язаних з управлінням файлами.

Цей модуль імпортує та об'єднує окремі роутери для:
- Процесу завантаження файлів (`uploads.py`)
- Управління аватарами користувачів (`avatars.py`)
- Загальних операцій з записами файлів (метаданими) (`files.py`)

Загальний префікс для всіх цих шляхів (наприклад, `/files`) буде встановлено
при підключенні `files_router` до роутера версії API (`v1_router`).

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from fastapi import APIRouter

# Оновлені повні шляхи імпорту для під-роутерів
from backend.app.src.api.v1.files.uploads import router as uploads_router
from backend.app.src.api.v1.files.avatars import router as avatars_router
from backend.app.src.api.v1.files.files import router as general_files_router

from backend.app.src.config.logging import logger # Централізований логер

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних з файлами
files_router = APIRouter()

# Підключення роутера для завантаження файлів
files_router.include_router(uploads_router, prefix="/uploads", tags=["Файли - Завантаження"]) # i18n tag

# Підключення роутера для управління аватарами
files_router.include_router(avatars_router, prefix="/avatars", tags=["Файли - Аватари користувачів"]) # i18n tag

# Підключення роутера для загальних операцій з файлами (наприклад, отримання/видалення FileRecord)
# Цей роутер може мати шляхи типу /{file_id}, тому він підключається без додаткового префіксу тут.
# Загальний префікс /files буде застосовано при підключенні files_router до v1_router.
files_router.include_router(general_files_router, tags=["Файли - Управління записами"]) # i18n tag


# Експортуємо files_router для використання в головному v1_router
__all__ = [
    "files_router",
]

logger.info("Роутер для управління файлами (`files_router`) зібрано та готовий до підключення до API v1.")
