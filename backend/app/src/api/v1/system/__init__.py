# backend/app/src/api/v1/system/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету системних ендпоінтів API v1.

Цей пакет містить роутери для управління системними функціями, такими як:
- Налаштування системи.
- Управління системними завданнями (cron).
- Моніторинг системи.
- Перевірка стану системи (health check).
- Ініціалізація початкових даних.

Кожен модуль у цьому пакеті (наприклад, `settings.py`, `health.py`) визначає
свій `APIRouter`, який потім агрегується тут для подальшого підключення
до головного роутера API v1 (`backend.app.src.api.v1.router`).
"""

from fastapi import APIRouter

from backend.app.src.api.v1.system.health import router as health_router
from backend.app.src.api.v1.system.init_data import router as init_data_router
from backend.app.src.api.v1.system.settings import router as settings_router
from backend.app.src.api.v1.system.cron_task import router as cron_task_router
from backend.app.src.api.v1.system.monitoring import router as monitoring_router

# Агрегуючий роутер для всіх системних ендпоінтів
system_router = APIRouter()

system_router.include_router(health_router, tags=["System"]) # Тег вже є в health_router
system_router.include_router(init_data_router, prefix="/init", tags=["System"]) # Тег вже є в init_data_router
system_router.include_router(settings_router, prefix="/config", tags=["System"]) # Тег вже є в settings_router
system_router.include_router(cron_task_router, prefix="/cron", tags=["System"]) # Тег вже є в cron_task_router
system_router.include_router(monitoring_router, prefix="/monitor", tags=["System"]) # Тег вже є в monitoring_router


__all__ = (
    "system_router",
)
