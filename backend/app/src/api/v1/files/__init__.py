# backend/app/src/api/v1/files/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету ендпоінтів управління файлами API v1.

Цей пакет містить роутери для:
- Управління аватарами користувачів (`avatars.py`).
- Загальних операцій з файлами (`files.py`), таких як завантаження
  іконок груп, нагород, файлів до завдань тощо.
"""

from fastapi import APIRouter

from backend.app.src.api.v1.files.avatars import router as avatars_router
from backend.app.src.api.v1.files.files import router as general_files_router

# Агрегуючий роутер для всіх ендпоінтів, пов'язаних з файлами.
files_router = APIRouter()

# Ендпоінти для аватарів користувачів
# Будуть доступні за префіксом /files/avatars (визначеним у v1.router та тут)
files_router.include_router(avatars_router, prefix="/avatars", tags=["Files"])

# Ендпоінти для загальних операцій з файлами
# Будуть доступні за префіксом /files (визначеним у v1.router)
files_router.include_router(general_files_router, tags=["Files"])
# Якщо general_files_router має свої шляхи типу /upload, то кінцевий шлях буде /files/upload.
# Якщо шляхи в general_files_router вже включають /files, то тут префікс не потрібен.
# Поточна реалізація general_files_router.py передбачає, що префікс /files буде зовнішнім.

__all__ = (
    "files_router",
)
