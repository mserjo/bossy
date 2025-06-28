# backend/app/src/api/v1/integrations/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'integrations' API v1.

Цей пакет містить ендпоінти для управління інтеграціями з зовнішніми
сервісами через API v1. Наприклад:
- Налаштування синхронізації з календарями (`calendars.py`).
- Налаштування сповіщень через месенджери (`messengers.py`).
- Налаштування інтеграції з таск-трекерами (`trackers.py`).

Цей файл робить каталог 'integrations' пакетом Python та експортує
агрегований роутер `router` для всіх ендпоінтів інтеграцій.
"""

from fastapi import APIRouter

# TODO: Імпортувати окремі роутери з модулів цього пакету, коли вони будуть створені.
# from backend.app.src.api.v1.integrations.calendars import router as calendars_integration_router
# from backend.app.src.api.v1.integrations.messengers import router as messengers_integration_router
# from backend.app.src.api.v1.integrations.trackers import router as trackers_integration_router

# Агрегуючий роутер для всіх ендпоінтів інтеграцій API v1.
router = APIRouter(tags=["v1 :: Integrations"])

# TODO: Розкоментувати та підключити окремі роутери.
# Префікси тут будуть відносні до шляху, з яким цей `router` підключається
# (наприклад, `/integrations` або `/users/me/integrations`).

# router.include_router(calendars_integration_router, prefix="/calendars")
# router.include_router(messengers_integration_router, prefix="/messengers")
# router.include_router(trackers_integration_router, prefix="/trackers")


# Експорт агрегованого роутера.
__all__ = [
    "router",
]

# TODO: Узгодити назву експортованого роутера ("router") з імпортом
# в `backend.app.src.api.v1.router.py` (очікує `integrations_v1_router`).
# TODO: Визначити, чи ці налаштування є глобальними, на рівні групи чи користувача,
# та відповідно адаптувати шляхи та префікси.
