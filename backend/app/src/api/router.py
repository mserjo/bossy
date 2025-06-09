# backend/app/src/api/router.py
# -*- coding: utf-8 -*-
"""
Головний агрегатор API роутерів для різних версій API.

Цей модуль визначає `api_router`, який є екземпляром `APIRouter` від FastAPI.
Він призначений для підключення всіх версійних роутерів (наприклад, v1, v2)
та будь-яких загальних API ендпоінтів, які не належать до конкретної версії.

`api_router` потім підключається до основного екземпляру FastAPI додатка в `main.py`.
"""

import logging
from fastapi import APIRouter, Depends # Додано Depends для прикладу

# Імпорт роутерів для конкретних версій API.
# Ці файли будуть створені пізніше, тому імпорти поки що можуть бути концептуальними.
# Наприклад, очікується, що буде створено backend/app/src/api/v1/router.py,
# який визначатиме свій власний APIRouter (наприклад, v1_router).

# from .v1.router import router as v1_router # Приклад імпорту роутера v1
# from .v2.router import router as v2_router # Приклад для майбутньої v2

# Можливо, імпорт middleware або залежностей, якщо вони застосовуються до всього api_router
# from .middleware import some_global_api_middleware # Приклад
# from .dependencies import get_current_active_user # Приклад глобальної залежності, що може бути застосована до всього роутера

logger = logging.getLogger(__name__)

# Створення головного роутера API
api_router = APIRouter(
    # prefix="/api", # Загальний префікс для всіх API шляхів, якщо потрібно.
                     # Часто префікс "/api" додається при підключенні цього роутера
                     # до основного додатку в main.py для більшої гнучкості,
                     # наприклад: app.include_router(api_router, prefix="/api")

    # Приклад глобальної залежності для всіх ендпоінтів цього роутера:
    # dependencies=[Depends(get_current_active_user)], # Розкоментуйте, якщо потрібна автентифікація для всіх шляхів під цим роутером

    # Приклад глобальних відповідей для всіх ендпоінтів цього роутера:
    responses={
        401: {"description": "Не авторизовано (Unauthorized)"},
        403: {"description": "Доступ заборонено (Forbidden)"},
        # 404: {"description": "Ресурс не знайдено (Not Found)"} # 404 зазвичай обробляється FastAPI автоматично
    }
)

# Підключення роутера для API версії 1
# Коли `api/v1/router.py` та `v1_router` в ньому будуть створені, розкоментуйте наступні рядки:
try:
    from .v1 import v1_router # Імпортуємо v1_router з api/v1/__init__.py
    api_router.include_router(v1_router, prefix="/v1", tags=["API v1"])
    logger.info("Роутер для API v1 успішно підключено до api_router.")
except ImportError as e:
    logger.warning(f"Не вдалося імпортувати v1_router з api.v1: {e}. API v1 не буде доступне.")
    # Можна залишити pass або додати обробку, якщо v1 є критичним
    pass
# logger.info("Концептуальне місце для підключення роутера API v1 (api.v1.router).") # Замінено реальним підключенням


# Підключення роутера для API версії 2 (приклад на майбутнє)
# try:
#     from .v2.router import router as v2_router
#     api_router.include_router(v2_router, prefix="/v2", tags=["API v2"])
#     logger.info("Роутер для API v2 успішно підключено до api_router.")
# except ImportError:
#     logger.info("Роутер для API v2 (api.v2.router) ще не реалізовано.")
#     pass
logger.info("Концептуальне місце для майбутнього підключення роутера API v2.")


# Приклад простого "health check" або "ping" ендпоінта на рівні агрегатора API,
# якщо він не належить до конкретної версії або потрібен для загальної перевірки.
@api_router.get(
    "/ping",
    summary="Перевірка доступності агрегатора API",
    tags=["API Health"],
    # response_description="Успішна відповідь від ping ендпоінта", # Опис відповіді
    # Зазвичай для таких простих ендпоінтів не потрібні складні схеми відповіді
)
async def ping_api():
    """
    Простий ендпоінт для перевірки, чи агрегатор API (`api_router`) працює.
    Повертає статус "API is alive!" та повідомлення "Pong!".
    Цей ендпоінт не вимагає автентифікації, якщо глобальні залежності не застосовані.
    """
    logger.debug("API ping ендпоінт викликано.")
    return {"status": "API aggregator is alive!", "message": "Pong!"}

# Можна додати інші загальні ендпоінти або налаштування тут.
# Наприклад, ендпоінт для отримання загальної конфігурації API, якщо це потрібно.

logger.info("Головний API роутер (`api_router`) налаштовано з базовим ping ендпоінтом.")

# Експорт api_router для використання в main.py.
# __all__ = ["api_router"] # Не є строго обов'язковим, оскільки імпорт зазвичай прямий:
                           # from app.src.api.router import api_router
                           # Але може бути корисним для документації або інструментів аналізу.
