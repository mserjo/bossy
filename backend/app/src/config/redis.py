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

# Глобальна змінна для зберігання пулу з'єднань Redis (або одного з'єднання).
# Це дозволяє уникнути створення нового з'єднання при кожному запиті.
_redis_pool: Optional[aioredis.Redis] = None # Або aioredis.ConnectionPool

async def get_redis_connection() -> Optional[aioredis.Redis]:
    """
    Повертає активне з'єднання (або з'єднання з пулу) до Redis.
    Якщо з'єднання ще не встановлено, намагається його створити.
    """
    global _redis_pool
    if _redis_pool is None:
        if settings.redis and settings.redis.REDIS_URL:
            try:
                logger.info(f"Спроба підключення до Redis за URL: {settings.redis.REDIS_URL}")
                # Створюємо пул з'єднань або одне з'єднання.
                # Для FastAPI, зазвичай, краще використовувати пул.
                # `aioredis.from_url` створює клієнта, який керує пулом всередині.
                _redis_pool = aioredis.from_url(
                    str(settings.redis.REDIS_URL), # Переконуємося, що це рядок
                    encoding="utf-8",
                    decode_responses=True # Автоматично декодувати відповіді з bytes в str
                )
                # Перевірка з'єднання
                await _redis_pool.ping()
                logger.info("Успішне підключення до Redis.")
            except Exception as e:
                logger.error(f"Помилка підключення до Redis: {e}")
                _redis_pool = None # Скидаємо, щоб не намагатися використовувати недійсний пул
        else:
            logger.warning("Налаштування Redis (REDIS_URL) не знайдено. Redis не буде використовуватися.")
            return None

    return _redis_pool

async def close_redis_connection() -> None:
    """
    Закриває пул з'єднань Redis при завершенні роботи додатку.
    """
    global _redis_pool
    if _redis_pool:
        logger.info("Закриття з'єднання з Redis.")
        await _redis_pool.close()
        # await _redis_pool.wait_closed() # Для старіших версій aioredis
        _redis_pool = None

# Функція-залежність FastAPI для отримання Redis клієнта.
# Це дозволить легко використовувати Redis в ендпоінтах.
async def get_redis_client() -> AsyncGenerator[Optional[aioredis.Redis], None]:
    """
    Залежність FastAPI для отримання клієнта Redis.
    Повертає None, якщо Redis не налаштований або недоступний.
    """
    redis_client = await get_redis_connection()
    # Ця залежність не керує життєвим циклом самого клієнта/пулу,
    # а лише надає доступ до нього.
    # Пул створюється один раз і закривається при зупинці додатку.
    try:
        yield redis_client
    finally:
        # З'єднання з пулу автоматично повертаються до пулу.
        # Явне закриття тут не потрібне, якщо `get_redis_connection` повертає клієнта,
        # який керує пулом.
        pass

# Приклад використання в ендпоінті:
# from fastapi import Depends
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
