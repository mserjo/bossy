# backend/app/src/api/external/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет для обробки зовнішніх API запитів, переважно вебхуків від сторонніх сервісів.

Цей модуль агрегує роутери, що відповідають за обробку вхідних запитів
від зовнішніх платформ, таких як календарні сервіси (Google Calendar, Outlook Calendar)
або месенджери (Telegram, Slack, Viber, Teams), коли вони надсилають події
(наприклад, оновлення події в календарі, нове повідомлення для бота).

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

from fastapi import APIRouter

# Повні шляхи імпорту
from backend.app.src.api.external.webhook import router as generic_webhook_router
from backend.app.src.api.external.calendar import router as calendar_webhooks_router
from backend.app.src.api.external.messenger import router as messenger_webhooks_router

from backend.app.src.config import logger # Стандартизований імпорт логера

# Створюємо агрегований роутер для всіх ендпоінтів, призначених для зовнішніх систем (вебхуків)
external_api_router = APIRouter()

# Підключення роутера для загальних вебхуків
# Ці вебхуки можуть бути для сервісів, що не класифікуються як календарі чи месенджери,
# або для початкової обробки перед маршрутизацією до більш специфічних обробників.
external_api_router.include_router(
    generic_webhook_router,
    prefix="/webhook", # Загальний префікс для універсальних вебхуків
    tags=["Зовнішні Вебхуки - Загальні"] # i18n
)

# Підключення роутера для вебхуків календарних сервісів
# Наприклад, для отримання сповіщень про зміни в подіях Google Calendar.
external_api_router.include_router(
    calendar_webhooks_router,
    prefix="/calendar", # Префікс для вебхуків від календарних сервісів
    tags=["Зовнішні Вебхуки - Календарі"] # i18n
)

# Підключення роутера для вебхуків месенджерів
# Наприклад, для отримання повідомлень, надісланих боту в Telegram або Slack.
external_api_router.include_router(
    messenger_webhooks_router,
    prefix="/messenger", # Префікс для вебхуків від месенджерів
    tags=["Зовнішні Вебхуки - Месенджери"] # i18n
)

# Експортуємо `external_api_router` для використання в головному API роутері (`backend/app/src/api/router.py`)
__all__ = [
    "external_api_router",
]

logger.info("Роутер для зовнішніх API (`external_api_router`) зібрано та готовий до підключення.")
