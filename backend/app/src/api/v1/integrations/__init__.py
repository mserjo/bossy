# backend/app/src/api/v1/integrations/__init__.py
# -*- coding: utf-8 -*-
"""
Агрегований роутер для всіх ендпоінтів, пов'язаних з інтеграціями з зовнішніми сервісами.

Цей модуль імпортує та об'єднує окремі роутери для:
- Інтеграцій з календарними сервісами (наприклад, Google Calendar, Outlook Calendar).
- Інтеграцій з платформами месенджерів (наприклад, Telegram, Slack).

Загальний префікс для всіх цих шляхів (наприклад, `/integrations`) буде встановлено
при підключенні `integrations_router` до роутера версії API (`v1_router`).
"""
from fastapi import APIRouter

# Повні шляхи імпорту (відносно поточного пакету)
from .calendars import router as calendars_router
from .messengers import router as messengers_router

from backend.app.src.config.logging import logger # Централізований логер

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних з інтеграціями
integrations_router = APIRouter()

# Підключення роутера для інтеграцій з календарями
integrations_router.include_router(
    calendars_router,
    prefix="/calendars",
    tags=["Інтеграції - Календарі"] # i18n tag
)

# Підключення роутера для інтеграцій з месенджерами
integrations_router.include_router(
    messengers_router,
    prefix="/messengers",
    tags=["Інтеграції - Месенджери"] # i18n tag
)

# Експортуємо integrations_router для використання в головному v1_router
__all__ = [
    "integrations_router",
]

logger.info("Роутер для інтеграцій (`integrations_router`) зібрано та готовий до підключення до API v1.")
