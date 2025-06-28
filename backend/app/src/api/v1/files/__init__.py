# backend/app/src/api/v1/files/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'files' API v1.

Цей пакет містить ендпоінти для управління файлами в системі
через API v1. Сюди можуть входити операції:
- Завантаження файлів (аватари, іконки груп/нагород/бейджів, вкладення).
- Можливо, перегляд/видалення завантажених файлів.

Логіка може бути розділена на загальні операції (`files.py`)
та специфічні, наприклад, для аватарів (`avatars.py`).

Цей файл робить каталог 'files' пакетом Python та експортує
агрегований роутер `router` для файлових операцій.
"""

from fastapi import APIRouter

# TODO: Імпортувати окремі роутери з модулів цього пакету, коли вони будуть створені.
# from backend.app.src.api.v1.files.files import router as general_files_router
# from backend.app.src.api.v1.files.avatars import router as avatars_router

# Агрегуючий роутер для всіх ендпоінтів файлів API v1.
router = APIRouter(tags=["v1 :: Files"])

# TODO: Розкоментувати та підключити окремі роутери.
# Загальні операції з файлами (наприклад, /files/upload)
# router.include_router(general_files_router)

# Специфічні ендпоінти для аватарів (наприклад, /files/avatars або /users/me/avatar)
# router.include_router(avatars_router, prefix="/avatars")


# Експорт агрегованого роутера.
__all__ = [
    "router",
]

# TODO: Узгодити назву експортованого роутера ("router") з імпортом
# в `backend.app.src.api.v1.router.py` (очікує `files_v1_router`).
