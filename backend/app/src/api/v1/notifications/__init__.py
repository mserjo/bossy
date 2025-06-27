# backend/app/src/api/v1/notifications/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету ендпоінтів сповіщень API v1.

Цей пакет містить роутери для:
- Управління сповіщеннями користувача та його налаштуваннями (`notifications.py`).
- Управління шаблонами сповіщень (адміністративні) (`templates.py`).
- Перегляду статусів доставки сповіщень (адміністративні) (`delivery.py`).
"""

from fastapi import APIRouter

from backend.app.src.api.v1.notifications.notifications import router as user_notifications_router
from backend.app.src.api.v1.notifications.templates import router as templates_router
from backend.app.src.api.v1.notifications.delivery import router as delivery_status_router

# Агрегуючий роутер для всіх ендпоінтів сповіщень.
notifications_router = APIRouter()

# Ендпоінти для користувача (мої сповіщення, мої налаштування)
# Будуть доступні за префіксом /notifications (визначеним у v1.router)
notifications_router.include_router(user_notifications_router, tags=["Notifications"])

# Адміністративні ендпоінти для шаблонів
notifications_router.include_router(templates_router, prefix="/templates", tags=["Notifications (Admin)"])

# Адміністративні ендпоінти для статусів доставки
notifications_router.include_router(delivery_status_router, prefix="/delivery-status", tags=["Notifications (Admin)"])


__all__ = (
    "notifications_router",
)
