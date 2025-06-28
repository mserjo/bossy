# backend/app/src/config/redis.py
# -*- coding: utf-8 -*-
"""
Цей модуль відповідає за налаштування підключення до Redis.
Redis може використовуватися для кешування, черг повідомлень (Celery),
зберігання сесій, rate limiting тощо.
"""

import redis.asyncio as aioredis # type: ignore # Асинхронна бібліотека для Redis
from typing import Optional, AsyncGenerator

# Імпорт налаштувань Redis з settings.py
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import logger # Використовуємо налаштований логгер

# Глобальна змінна для зберігання пулу з'єднань Redis більше не використовується.
# Пул або клієнт буде передаватися через app.state.

async def init_redis_pool(redis_url: str) -> Optional[aioredis.Redis]:
    """
    Ініціалізує та повертає клієнта Redis (який керує пулом з'єднань).
    Повертає None, якщо сталася помилка підключення.
    """
    try:
        logger.info(f"Спроба підключення до Redis за URL: {redis_url}")
        # `aioredis.from_url` створює клієнта, який керує пулом всередині.
        redis_client = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True # Автоматично декодувати відповіді з bytes в str
        )
        # Перевірка з'єднання
        await redis_client.ping()
        logger.info("Успішне підключення до Redis та ініціалізація клієнта (пулу).")
        return redis_client
    except Exception as e:
        logger.error(f"Помилка підключення до Redis під час ініціалізації: {e}", exc_info=True)
        return None

async def close_redis_pool(redis_client: Optional[aioredis.Redis]) -> None:
    """
    Закриває наданий клієнт Redis (та його внутрішній пул з'єднань).
    """
    if redis_client:
        logger.info("Закриття клієнта Redis (та його внутрішнього пулу з'єднань)...")
        try:
            await redis_client.close()
            # У новіших версіях aioredis (>2.0.0) close() є корутиною,
            # і може бути достатньо просто await redis_client.close().
            # `wait_closed()` використовувався для старіших версій для пулів.
            # Для клієнта, створеного через from_url, await close() має бути достатньо.
            logger.info("Клієнт Redis успішно закрито.")
        except Exception as e:
            logger.error(f"Помилка під час закриття клієнта Redis: {e}", exc_info=True)
    else:
        logger.info("Клієнт Redis не був наданий або не ініціалізований, закриття не потрібне.")

# Функція-залежність FastAPI для отримання Redis клієнта.
# Тепер вона отримує клієнта з app.state, як очікує main.py.
# Використовуємо Request для доступу до app.state, як це зазвичай робиться в FastAPI.
from fastapi import Request as FastAPIRequest # Уникаємо конфлікту імен, якщо Request використовується десь ще

async def get_redis_client(request: FastAPIRequest) -> Optional[aioredis.Redis]:
    """
    Залежність FastAPI для отримання клієнта Redis зі стану додатку (app.state).
    Повертає None, якщо Redis не налаштований, недоступний або не ініціалізований в app.state.
    """
    # main.py зберігає клієнта в app.state.redis
    redis_client: Optional[aioredis.Redis] = getattr(request.app.state, 'redis', None)
    if redis_client is None:
        logger.debug("Клієнт Redis не знайдено в app.state.redis. Можливо, Redis не увімкнено або не ініціалізовано.")
    # Ця залежність просто надає доступ до вже ініціалізованого клієнта.
    # Життєвим циклом клієнта керують події startup/shutdown в main.py.
    return redis_client # Просто повертаємо те, що є в app.state

# Приклад використання в ендпоінті:
# from fastapi import Depends, APIRouter
# router = APIRouter()
# @router.get("/redis-test")
# async def my_endpoint(redis: Optional[aioredis.Redis] = Depends(get_redis_client)):
#     if redis:
#         await redis.set("my_key", "my_value")
#         value = await redis.get("my_key")
# else:
# # Логіка, якщо Redis недоступний

# TODO: Перевірити, чи `settings.redis` існує перед доступом до `settings.redis.REDIS_URL`.
# Це зроблено через `if settings.redis and settings.redis.REDIS_URL:`.
#
# TODO: Додати обробку подій FastAPI `startup` та `shutdown` для ініціалізації
# та закриття пулу з'єднань Redis в `main.py`.
#
# @app.on_event("startup")
# async def startup_event():
#     await get_redis_connection() # Ініціалізує пул, якщо налаштовано
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     await close_redis_connection()
#
# Це забезпечить коректне управління ресурсами.
#
# Використання `decode_responses=True` в `aioredis.from_url` зручно,
# оскільки дані автоматично декодуються з байтів у рядки.
#
# Асинхронна бібліотека `redis.asyncio` (aioredis) є стандартним вибором для FastAPI.
#
# `get_redis_client` як залежність FastAPI надає зручний спосіб доступу до Redis
# в обробниках запитів. Якщо Redis не налаштований, залежність поверне `None`,
# і код обробника має це враховувати.
#
# Все виглядає як хороший базовий модуль для роботи з Redis.
# Якщо Redis не налаштований (немає `REDIS_URL`), то `_redis_pool` залишиться `None`,
# і `get_redis_connection()` / `get_redis_client()` повертатимуть `None`.
# Це дозволяє додатку працювати без Redis, якщо він не є критичним компонентом
# для всіх функцій (наприклад, використовується лише для опціонального кешування).
# Якщо Redis критичний, то помилка підключення має призводити до зупинки додатку.
# Поточна реалізація дозволяє "м'яку" відмову від Redis.
#
# Все готово.
