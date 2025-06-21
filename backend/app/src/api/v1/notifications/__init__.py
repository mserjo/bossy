# backend/app/src/api/v1/notifications/__init__.py
# -*- coding: utf-8 -*-
"""
Агрегований роутер для всіх ендпоінтів, пов'язаних із системою сповіщень.

Цей модуль імпортує та об'єднує окремі роутери для:
- Управління сповіщеннями користувачів (перегляд, позначення як прочитані) (`notifications.py`)
- CRUD операцій над шаблонами сповіщень (адміністрування) (`templates.py`)
- Перегляду статусів доставки сповіщень (адміністрування) (`delivery.py`)

Загальний префікс для всіх цих шляхів (наприклад, `/notifications`) буде встановлено
при підключенні `notifications_router` до роутера версії API (`v1_router`).

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from fastapi import APIRouter

# Оновлені повні шляхи імпорту для під-роутерів
from backend.app.src.api.v1.notifications.notifications import router as user_notifications_router
from backend.app.src.api.v1.notifications.templates import router as notification_templates_router
from backend.app.src.api.v1.notifications.delivery import router as notification_delivery_router

from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних із системою сповіщень
notifications_router = APIRouter()

# Підключення роутера для сповіщень користувача
# Шляхи (напр. / та /{notification_id}) будуть відносні до префіксу notifications_router
notifications_router.include_router(user_notifications_router, tags=["Сповіщення - Користувацькі"]) # i18n tag

# Підключення роутера для шаблонів сповіщень (керування адміном)
notifications_router.include_router(
    notification_templates_router,
    prefix="/templates",
    tags=["Сповіщення - Шаблони (Адмін)"] # i18n tag
)

# Підключення роутера для статусів доставки сповіщень (перегляд адміном)
notifications_router.include_router(
    notification_delivery_router,
    prefix="/delivery-attempts", # Змінено префікс для ясності, що це про спроби доставки
    tags=["Сповіщення - Спроби доставки (Адмін)"] # i18n tag
)


# Експортуємо notifications_router для використання в головному v1_router
__all__ = [
    "notifications_router",
]

logger.info("Роутер для системи сповіщень (`notifications_router`) зібрано та готовий до підключення до API v1.")
