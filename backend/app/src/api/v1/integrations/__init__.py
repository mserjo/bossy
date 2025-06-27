# backend/app/src/api/v1/integrations/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету ендпоінтів управління інтеграціями API v1.

Цей пакет містить роутери для налаштування інтеграцій з зовнішніми сервісами:
- Календарі (`calendars.py`).
- Месенджери (`messengers.py`).
- Таск-трекери (`trackers.py`).
"""

from fastapi import APIRouter

from backend.app.src.api.v1.integrations.calendars import router as calendars_router
from backend.app.src.api.v1.integrations.messengers import router as messengers_router
from backend.app.src.api.v1.integrations.trackers import router as trackers_router

# Агрегуючий роутер для всіх ендпоінтів інтеграцій.
integrations_router = APIRouter()

# Префікси для цих роутерів будуть визначені при підключенні integrations_router
# до головного v1_router. Наприклад, /api/v1/integrations/calendars, ...
# Або, якщо це персональні налаштування: /api/v1/users/me/integrations/calendars

integrations_router.include_router(calendars_router, prefix="/calendars", tags=["Integrations"])
integrations_router.include_router(messengers_router, prefix="/messengers", tags=["Integrations"])
integrations_router.include_router(trackers_router, prefix="/trackers", tags=["Integrations"])

__all__ = (
    "integrations_router",
)
