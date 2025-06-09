# backend/app/src/api/v1/integrations/__init__.py
from fastapi import APIRouter

# Імпортуємо роутери з файлів цього модуля
from .calendars import router as calendars_router
from .messengers import router as messengers_router

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних з інтеграціями
integrations_router = APIRouter()

# Підключення роутера для інтеграцій з календарями
integrations_router.include_router(calendars_router, prefix="/calendars", tags=["Integrations - Calendars"])

# Підключення роутера для інтеграцій з месенджерами
integrations_router.include_router(messengers_router, prefix="/messengers", tags=["Integrations - Messengers"])


# Експортуємо integrations_router для використання в головному v1_router (app/src/api/v1/router.py)
__all__ = ["integrations_router"]
