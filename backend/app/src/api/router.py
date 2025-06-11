# backend/app/src/api/router.py
# -*- coding: utf-8 -*-
"""
Головний агрегатор API роутерів для різних версій API.

Цей модуль визначає `api_router`, який є екземпляром `APIRouter` від FastAPI.
Він призначений для підключення всіх версійних роутерів (наприклад, v1, v2)
та будь-яких загальних API ендпоінтів, які не належать до конкретної версії.

`api_router` потім підключається до основного екземпляру FastAPI додатка в `main.py`.
"""

# import logging # Замінено на централізований логер
from fastapi import APIRouter # Depends не використовується тут напряму, лише в коментарях

# Повні шляхи імпорту
from backend.app.src.api.v1 import v1_router # Імпортуємо v1_router з api/v1/__init__.py (або api.v1.router)
from backend.app.src.api.external import external_api_router # Імпортуємо external_api_router з api/external/__init__.py (або api.external.router)
from backend.app.src.config.logging import logger # Централізований логер
# from .dependencies import get_current_active_user # Приклад глобальної залежності


# Створення головного роутера API
api_router = APIRouter(
    # Приклад глобальної залежності для всіх ендпоінтів цього роутера:
    # dependencies=[Depends(get_current_active_user)],

    # Загальні відповіді для всіх ендпоінтів цього роутера:
    responses={
        401: {"description": "Не авторизовано (токен не надано, невалідний або прострочений)"}, # i18n
        403: {"description": "Доступ заборонено (недостатньо прав для виконання операції)"}, # i18n
        # 404 Not Found зазвичай обробляється FastAPI автоматично для неіснуючих шляхів.
        # 500 Internal Server Error обробляється кастомним обробником винятків.
    }
)

# Підключення роутера для API версії 1
try:
    api_router.include_router(v1_router, prefix="/v1", tags=["API v1"])
    logger.info("Роутер для API v1 успішно підключено до api_router.")
except Exception as e: # Більш загальний Exception для випадків, коли v1_router може бути None через помилку імпорту
    logger.warning(f"Не вдалося підключити v1_router з api.v1: {e}. API v1 може бути недоступне.")


# Підключення роутера для зовнішніх API (вебхуків)
try:
    api_router.include_router(external_api_router, prefix="/external", tags=["Зовнішні API (Вебхуки)"]) # i18n tag
    logger.info("Роутер для зовнішніх API (вебхуків) успішно підключено до api_router.")
except Exception as e:
    logger.warning(f"Не вдалося підключити external_api_router з api.external: {e}. Зовнішні API (вебхуки) можуть бути недоступні.")


# Приклад підключення роутера для API версії 2 (на майбутнє)
# try:
#     from .v2.router import router as v2_router # Припускаючи, що v2_router визначено в api/v2/router.py
#     api_router.include_router(v2_router, prefix="/v2", tags=["API v2"])
#     logger.info("Роутер для API v2 успішно підключено до api_router.")
# except ImportError:
#     logger.info("Роутер для API v2 (api.v2.router) ще не реалізовано.")


@api_router.get(
    "/ping",
    summary="Перевірка доступності агрегатора API", # i18n
    tags=["Стан API"], # i18n
    response_description="Успішна відповідь від ping ендпоінта" # i18n
)
async def ping_api():
    """
    Простий ендпоінт для перевірки, чи агрегатор API (`api_router`) працює.
    Повертає статус "Агрегатор API активний!" та повідомлення "Pong!".
    Цей ендпоінт не вимагає автентифікації, якщо глобальні залежності не застосовані.
    """
    logger.debug("API ping ендпоінт викликано.")
    # i18n
    return {"status": "Агрегатор API активний!", "message": "Pong!"}


logger.info("Головний API роутер (`api_router`) налаштовано з базовим ping ендпоінтом та підключеними версійними роутерами.")

# __all__ не є обов'язковим для APIRouter, оскільки він зазвичай імпортується напряму.
# Якщо потрібно експортувати щось ще з цього модуля, можна додати до __all__.
# __all__ = ["api_router"]
