# backend/app/src/api/external/__init__.py
# -*- coding: utf-8 -*-
from backend.app.src.core.i18n import _
"""
Пакет для обробки зовнішніх API запитів, переважно вебхуків від сторонніх сервісів.

Цей модуль агрегує роутери, що відповідають за обробку вхідних запитів
від зовнішніх платформ, таких як календарні сервіси (Google Calendar, Outlook Calendar)
або месенджери (Telegram, Slack, Viber, Teams), коли вони надсилають події
(наприклад, оновлення події в календарі, нове повідомлення для бота).

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

from fastapi import APIRouter

from backend.app.src.api.external.webhook import router as generic_webhook_router
from backend.app.src.api.external.calendar import router as calendar_webhooks_router
from backend.app.src.api.external.messenger import router as messenger_webhooks_router
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Створюємо агрегований роутер для всіх ендпоінтів, призначених для зовнішніх систем (вебхуків)
external_api_router = APIRouter()

# Підключення роутера для загальних вебхуків
# Ці вебхуки можуть бути для сервісів, що не класифікуються як календарі чи месенджери,
# або для початкової обробки перед маршрутизацією до більш специфічних обробників.
external_api_router.include_router(
    generic_webhook_router,
    prefix="/webhook",
    tags=[_("api_external_router.tags.webhooks_general")]
)

# Підключення роутера для вебхуків календарних сервісів
# Наприклад, для отримання сповіщень про зміни в подіях Google Calendar.
external_api_router.include_router(
    calendar_webhooks_router,
    prefix="/calendar",
    tags=[_("api_external_router.tags.webhooks_calendar")]
)

# Підключення роутера для вебхуків месенджерів
# Наприклад, для отримання повідомлень, надісланих боту в Telegram або Slack.
external_api_router.include_router(
    messenger_webhooks_router,
    prefix="/messenger",
    tags=[_("api_external_router.tags.webhooks_messenger")]
)

# Експортуємо `external_api_router` для використання в головному API роутері (`backend/app/src/api/router.py`)
__all__ = [
    "external_api_router",
]

logger.info(_("api_external_router.log.router_configured_and_ready"))
