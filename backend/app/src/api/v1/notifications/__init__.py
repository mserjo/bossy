# backend/app/src/api/v1/notifications/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'notifications' API v1.

Цей пакет містить ендпоінти для управління сповіщеннями в системі
через API v1. Сюди можуть входити операції:
- Перегляд сповіщень користувача та їх налаштувань (`notifications.py`).
- Адміністративне управління шаблонами сповіщень (`templates.py`).
- Перегляд статусів доставки сповіщень (`delivery.py`).

Цей файл робить каталог 'notifications' пакетом Python та експортує
агрегований роутер `router` для всіх ендпоінтів сповіщень.
"""

from fastapi import APIRouter

# TODO: Імпортувати окремі роутери з модулів цього пакету, коли вони будуть створені.
# from backend.app.src.api.v1.notifications.notifications import router as user_notifications_router
# from backend.app.src.api.v1.notifications.templates import router as notification_templates_router
# from backend.app.src.api.v1.notifications.delivery import router as notification_delivery_router

# Агрегуючий роутер для всіх ендпоінтів сповіщень API v1.
router = APIRouter(tags=["v1 :: Notifications"])

# TODO: Розкоментувати та підключити окремі роутери.
# Ендпоінти для користувацьких сповіщень
# (наприклад, /notifications/ або /users/me/notifications)
# router.include_router(user_notifications_router)

# Адміністративні ендпоінти для шаблонів сповіщень
# (наприклад, /notifications/templates)
# router.include_router(notification_templates_router, prefix="/templates", tags=["v1 :: Notifications (Admin)"])

# Адміністративні ендпоінти для статусів доставки сповіщень
# (наприклад, /notifications/delivery-status)
# router.include_router(notification_delivery_router, prefix="/delivery-status", tags=["v1 :: Notifications (Admin)"])


# Експорт агрегованого роутера.
__all__ = [
    "router",
]

# TODO: Узгодити назву експортованого роутера ("router") з імпортом
# в `backend.app.src.api.v1.router.py` (очікує `notifications_v1_router`).
