# backend/app/src/api/external/__init__.py
from fastapi import APIRouter

# Імпортуємо роутери з файлів цього модуля
from .webhook import router as generic_webhook_router
from .calendar import router as calendar_webhooks_router
from .messenger import router as messenger_webhooks_router

# Створюємо агрегований роутер для всіх ендпоінтів, призначених для зовнішніх систем (вебхуків)
external_api_router = APIRouter()

# Підключення роутера для загальних вебхуків
external_api_router.include_router(generic_webhook_router, prefix="/webhook", tags=["External Webhooks - Generic"])

# Підключення роутера для вебхуків календарних сервісів
external_api_router.include_router(calendar_webhooks_router, prefix="/calendar", tags=["External Webhooks - Calendars"])

# Підключення роутера для вебхуків месенджерів
external_api_router.include_router(messenger_webhooks_router, prefix="/messenger", tags=["External Webhooks - Messengers"])


# Експортуємо external_api_router для використання в головному API роутері
__all__ = ["external_api_router"]
