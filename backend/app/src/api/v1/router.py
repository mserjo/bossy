# backend/app/src/api/v1/router.py
# -*- coding: utf-8 -*-
"""
Головний агрегований маршрутизатор для API версії 1 (v1).

Цей модуль визначає `v1_router` (екземпляр `APIRouter`), який об'єднує
всі окремі маршрутизатори для різних функціональних блоків API v1.
Кожен функціональний блок (наприклад, автентифікація, користувачі, групи)
має свій власний під-маршрутизатор, який імпортується та підключається тут
з відповідним префіксом та тегами для документації OpenAPI.

`v1_router` потім підключається до кореневого маршрутизатора додатка.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

from fastapi import APIRouter

# --- Імпорт логера ---
# Використовуємо централізований логер додатка.
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# --- Імпорт під-маршрутизаторів для API v1 ---
# Кожен з цих імпортів має вказувати на змінну типу APIRouter,
# зазвичай названу `router` або `{module_name}_router` у відповідному файлі router.py.
# Наприклад, `system_router` з `backend.app.src.api.v1.system.router`.

from backend.app.src.api.v1.system.router import system_router
from backend.app.src.api.v1.auth.router import auth_router
from backend.app.src.api.v1.users.router import users_router
from backend.app.src.api.v1.dictionaries.router import dictionaries_router
from backend.app.src.api.v1.groups.router import groups_router
from backend.app.src.api.v1.tasks.router import tasks_router
from backend.app.src.api.v1.bonuses.router import bonuses_router
from backend.app.src.api.v1.gamification.router import gamification_router
from backend.app.src.api.v1.notifications.router import notifications_router # Виправлено з notifications_router на notifications_router
from backend.app.src.api.v1.files.router import files_router
from backend.app.src.api.v1.integrations.router import integrations_router

# Базова функція-заглушка для інтернаціоналізації рядків (якщо потрібна в коментарях)
def _(text: str) -> str:
    return text

# Створення головного маршрутизатора для API v1
v1_router = APIRouter() # Змінено v1_api_router на v1_router

# --- Підключення під-маршрутизаторів ---
# Кожен роутер підключається з унікальним префіксом, що відповідає його функціоналу.
# Теги використовуються для групування ендпоінтів в документації OpenAPI (Swagger).

ROUTERS_CONFIG = [
    {"router": system_router, "prefix": "/system", "tags": ["V1 Система"], "name": "system"},
    {"router": auth_router, "prefix": "/auth", "tags": ["V1 Автентифікація"], "name": "auth"},
    {"router": users_router, "prefix": "/users", "tags": ["V1 Користувачі"], "name": "users"},
    {"router": dictionaries_router, "prefix": "/dictionaries", "tags": ["V1 Довідники"], "name": "dictionaries"},
    {"router": groups_router, "prefix": "/groups", "tags": ["V1 Групи"], "name": "groups"},
    {"router": tasks_router, "prefix": "/tasks", "tags": ["V1 Завдання та Події"], "name": "tasks"},
    {"router": bonuses_router, "prefix": "/bonuses", "tags": ["V1 Бонуси та Винагороди"], "name": "bonuses"},
    {"router": gamification_router, "prefix": "/gamification", "tags": ["V1 Гейміфікація"], "name": "gamification"},
    {"router": notifications_router, "prefix": "/notifications", "tags": ["V1 Сповіщення"], "name": "notifications"},
    {"router": files_router, "prefix": "/files", "tags": ["V1 Файли"], "name": "files"},
    {"router": integrations_router, "prefix": "/integrations", "tags": ["V1 Інтеграції"], "name": "integrations"},
]

for config in ROUTERS_CONFIG:
    try:
        v1_router.include_router(config["router"], prefix=config["prefix"], tags=config["tags"])
        # i18n: Log message - Router connected successfully
        logger.info(_("Маршрутизатор v1.{name} успішно підключено з префіксом '{prefix}'.").format(name=config['name'], prefix=config['prefix']))
    except Exception as e:
        # i18n: Critical error message - Failed to connect router
        # Важливо логувати помилки на випадок, якщо якийсь роутер не вдалося підключити.
        logger.critical(
            _("КРИТИЧНО: Не вдалося підключити маршрутизатор v1.{name} з префіксом '{prefix}'. Помилка: {error}").format(
                name=config['name'], prefix=config['prefix'], error=e
            ),
            exc_info=True # Додаємо traceback до логу
        )

# --- Базовий ендпоінт для перевірки доступності API v1 ---
@v1_router.get(
    "/ping",
    summary="Перевірка доступності API v1",
    description="Простий ендпоінт для перевірки, чи головний маршрутизатор API v1 (`v1_router`) активний та відповідає.",
    tags=["V1 Перевірка стану"] # Оновлено тег
)
async def ping_v1_api():
    """
    Ендпоінт "ping" для API v1.
    Використовується для моніторингу доступності сервісу.
    """
    logger.debug("API v1: /ping ендпоінт викликано.")
    return {
        "status": "API v1 активний!", # Оновлено повідомлення
        "message": "Pong від API v1!"  # Оновлено повідомлення
    }

# i18n: Log message - V1 API router configured
logger.info(_("Головний маршрутизатор API v1 (`v1_router`) налаштовано та агреговано всі під-маршрутизатори."))

# Змінна, що експортується для підключення до основного FastAPI додатку
# (зазвичай в backend/app/main.py або backend/app/src/api/router.py)
# Наприклад: app.include_router(v1_router, prefix="/api/v1")
# __all__ = ["v1_api_router"] # Видалено, оскільки v1_api_router перейменовано і __all__ тут не критичний
