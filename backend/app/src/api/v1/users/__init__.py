# backend/app/src/api/v1/users/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету ендпоінтів управління користувачами API v1 (адміністративні).

Цей пакет містить роутери для адміністративних операцій з користувачами,
такі як перегляд списку, створення, редагування, видалення, зміна ролей тощо.
"""

from fastapi import APIRouter
from backend.app.src.api.v1.users.users import router as admin_users_router

users_router = APIRouter()
users_router.include_router(admin_users_router, prefix="", tags=["Users (Admin)"]) # Теги вже є в users.py

__all__ = (
    "users_router",
)
