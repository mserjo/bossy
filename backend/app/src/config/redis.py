# backend/app/src/config/redis.py
# -*- coding: utf-8 -*-
# # Модуль налаштування та управління з'єднанням з Redis для FastAPI програми Kudos (Virtus).
# #
# # Відповідає за ініціалізацію, надання та закриття асинхронного клієнта Redis
# # (`redis.asyncio`). Використовує глобальний екземпляр клієнта для ефективного
# # повторного використання з'єднань. Налаштування Redis (URL тощо)
# # завантажуються з модуля `backend.app.src.config.settings`.
# #
# # Основні компоненти:
# # - `get_redis_client()`: Асинхронна функція для отримання глобального клієнта Redis.
# # - `close_redis_client()`: Асинхронна функція для закриття з'єднання Redis.
# # - `get_redis()`: Асинхронна функція-залежність FastAPI для надання клієнта Redis.

import redis.asyncio as aioredis # Використовуємо псевдонім aioredis для ясності, що це асинхронна версія.
from typing import Optional, AsyncGenerator

# Абсолютний імпорт налаштувань та логера
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)

# Глобальна змінна для зберігання єдиного екземпляра клієнта Redis.
# Це дозволяє ініціалізувати клієнт один раз і повторно використовувати його
# протягом життєвого циклу програми, що є більш ефективним, ніж створення нового
# клієнта для кожного запиту або операції.
_redis_client: Optional[aioredis.Redis] = None

async def get_redis_client() -> aioredis.Redis:
    """
    Надає (та за потреби ініціалізує) глобальний асинхронний екземпляр клієнта Redis.

    При першому виклику ця функція ініціалізує клієнт Redis, використовуючи `REDIS_URL`
    з конфігураційних налаштувань (`settings.py`). Вона також виконує команду `ping` для перевірки
    успішності з'єднання. При наступних викликах повертає вже існуючий екземпляр.

    Returns:
        aioredis.Redis: Ініціалізований та підключений асинхронний клієнт Redis.

    Raises:
        ConnectionError: Якщо не вдалося підключитися до сервера Redis (наприклад, через невірний URL,
                         недоступність сервера) або якщо `REDIS_URL` не вказано в налаштуваннях.
    """
    global _redis_client
    if _redis_client is None:
        if not settings.REDIS_URL:
            # i18n: Error message for developers/logs
            logger.error("REDIS_URL не налаштовано. Неможливо ініціалізувати клієнт Redis.")
            raise ConnectionError("REDIS_URL не налаштовано в конфігурації.")
        try:
            # Створення екземпляра клієнта Redis з URL-адреси, вказаної в налаштуваннях.
            # `aioredis.from_url` автоматично обробляє парсинг DSN (Data Source Name).
            # i18n: Log message - Attempting to connect to Redis
            logger.info(f"Спроба підключення до Redis за адресою: {settings.REDIS_URL}")
            _redis_client = aioredis.from_url(
                str(settings.REDIS_URL), # REDIS_URL з settings.py (має бути рядком)
                encoding="utf-8",        # Кодування для рядків, що надсилаються та отримуються з Redis.
                decode_responses=True    # Автоматично декодувати відповіді з байтів у рядки UTF-8.
                                         # Це зручно, якщо ви переважно працюєте з текстовими даними в Redis.
            )
            # Перевірка з'єднання з сервером Redis шляхом відправки команди PING.
            await _redis_client.ping()
            # i18n: Log message - Successfully connected to Redis
            logger.info(f"Успішно підключено до Redis та отримано відповідь на ping: {settings.REDIS_URL}")
        except Exception as e:
            # i18n: Error message for developers/logs
            logger.error(f"Помилка підключення до Redis ({settings.REDIS_URL}): {e}", exc_info=True)
            # Скидаємо _redis_client, щоб при наступній спробі (якщо така буде) відбулася повторна ініціалізація.
            _redis_client = None
            raise ConnectionError(f"Не вдалося підключитися до Redis ({settings.REDIS_URL}): {e}")
    return _redis_client

async def close_redis_client():
    """
    Закриває активне з'єднання з Redis, якщо воно було ініціалізоване.

    Цю функцію слід викликати при завершенні роботи програми (наприклад,
    в обробнику події `shutdown` FastAPI), щоб коректно звільнити ресурси
    та закрити TCP-з'єднання з сервером Redis.
    """
    global _redis_client
    if _redis_client:
        # i18n: Log message - Closing Redis connection
        logger.info("Закриття з'єднання з Redis...")
        await _redis_client.close()
        _redis_client = None # Скидання глобальної змінної, щоб вказати, що клієнт більше не активний.
        # i18n: Log message - Redis connection closed successfully
        logger.info("З'єднання з Redis успішно закрито.")
    else:
        # i18n: Log message - Attempted to close Redis, but client not initialized
        logger.info("Спроба закрити з'єднання з Redis, але клієнт не був ініціалізований.")

# --- Залежність FastAPI для надання клієнта Redis ---
async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Асинхронна функція-залежність для FastAPI, яка надає клієнт Redis.

    Ця залежність отримує клієнт Redis за допомогою `get_redis_client()`.
    Оскільки використовується глобальний, спільно використовуваний клієнт (`_redis_client`),
    він не закривається після кожного запиту. Життєвий цикл цього глобального клієнта
    керується централізовано через функції `get_redis_client` (ініціалізація при першому запиті)
    та `close_redis_client` (закриття при виході з програми).

    Yields:
        aioredis.Redis: Асинхронний клієнт Redis, готовий до використання в обробниках запитів.
    """
    client = await get_redis_client() # Отримуємо (або ініціалізуємо) глобальний клієнт
    try:
        yield client # Передаємо клієнт в обробник запиту
    finally:
        # Життєвий цикл глобального клієнта Redis керується поза цією залежністю.
        # Тут НЕ потрібно викликати `await client.close()`, оскільки це закрило б
        # глобальний клієнт, що вплинуло б на інші запити.
        pass

# Блок для демонстраційних цілей або простого тестування функціональності модуля
if __name__ == "__main__":
    import asyncio

    # Налаштування логування для тестування (якщо воно ще не налаштоване глобально)
    try:
        from backend.app.src.config.logging import setup_logging
        if settings.LOG_TO_FILE: # Налаштовуємо логування у файл, якщо вказано
            log_file_path = settings.LOG_DIR / f"{Path(__file__).stem}_test.log"
            setup_logging(log_file_path=log_file_path)
        else:
            setup_logging() # Стандартне логування в консоль
    except ImportError:
        import logging as base_logging # Використовуємо стандартний logging, якщо кастомний недоступний
        base_logging.basicConfig(level=logging.INFO)
        logger.warning("Не вдалося імпортувати setup_logging. Використовується базова конфігурація логування для redis.py.")

    async def main_redis_test():
        """Основна функція для тестування підключення та базових операцій з Redis."""
        # i18n: Log message - Starting Redis module test
        logger.info("Запуск тестування модуля Redis...")
        try:
            redis_cli = await get_redis_client()
            # i18n: Log message - Redis client successfully obtained
            logger.info(f"Клієнт Redis успішно отримано: {redis_cli}")

            # Приклад використання клієнта Redis: встановлення, отримання та видалення ключа
            test_key = "kudos_test_key_redis_module"
            test_value = "Привіт від Kudos з Redis! Модуль redis.py працює."

            await redis_cli.set(test_key, test_value)
            # i18n: Log message - Test key set in Redis
            logger.info(f"Тестовий ключ '{test_key}' встановлено в Redis.")

            retrieved_value = await redis_cli.get(test_key)
            # i18n: Log message - Value retrieved from Redis
            logger.info(f"Отримане значення з Redis для ключа '{test_key}': {retrieved_value}")

            assert retrieved_value == test_value, "Значення з Redis не співпадає з встановленим!"

            await redis_cli.delete(test_key)
            # i18n: Log message - Test key deleted from Redis
            logger.info(f"Тестовий ключ '{test_key}' видалено з Redis.")

            # i18n: Log message - Redis module test successful
            logger.info("Тестування базових операцій Redis пройшло успішно.")

        except ConnectionError as e:
            # i18n: Error message - Connection error during Redis test
            logger.error(f"Помилка з'єднання під час тестування Redis: {e}", exc_info=settings.DEBUG)
        except Exception as e:
            # i18n: Error message - Unexpected error during Redis test
            logger.error(f"Неочікувана помилка під час тестування Redis: {e}", exc_info=settings.DEBUG)
        finally:
            # i18n: Log message - Finishing Redis module test, closing connection
            logger.info("Завершення тестування модуля Redis, закриття з'єднання...")
            await close_redis_client()

    asyncio.run(main_redis_test())
