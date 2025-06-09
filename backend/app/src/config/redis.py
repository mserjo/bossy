# /backend/app/src/config/redis.py
"""
Налаштування та управління з'єднанням з Redis для FastAPI програми Kudos.

Цей модуль відповідає за ініціалізацію, надання та закриття асинхронного клієнта Redis.
Він використовує глобальний екземпляр клієнта для ефективного повторного використання з'єднань.

Основні компоненти:
- `_redis_client`: Глобальна змінна для зберігання єдиного екземпляра `aioredis.Redis`.
- `get_redis_client()`: Асинхронна функція для отримання (та ініціалізації при першому виклику)
  глобального клієнта Redis. Включає перевірку з'єднання (ping) та обробку помилок.
- `close_redis_client()`: Асинхронна функція для коректного закриття з'єднання Redis,
  зазвичай викликається при завершенні роботи програми.
- `get_redis()`: Асинхронна функція-залежність для FastAPI, яка надає доступ до глобального
  клієнта Redis в обробниках запитів.

Налаштування Redis (URL, тощо) беруться з `settings.py`.
Використовується `redis.asyncio` для асинхронної взаємодії.
"""
import redis.asyncio as aioredis
from typing import Optional, AsyncGenerator

from backend.app.src.config.settings import settings
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)

# Глобальна змінна для зберігання єдиного екземпляра клієнта Redis.
# Це дозволяє ініціалізувати клієнт один раз і повторно використовувати його
# протягом життєвого циклу програми, що є більш ефективним.
_redis_client: Optional[aioredis.Redis] = None

async def get_redis_client() -> aioredis.Redis:
    """
    Надає (та за потреби ініціалізує) глобальний асинхронний екземпляр клієнта Redis.

    При першому виклику ця функція ініціалізує клієнт Redis, використовуючи `REDIS_URL`
    з конфігураційних налаштувань. Вона також виконує команду `ping` для перевірки
    успішності з'єднання. При наступних викликах повертає вже існуючий екземпляр.

    Returns:
        aioredis.Redis: Ініціалізований та підключений асинхронний клієнт Redis.

    Raises:
        ConnectionError: Якщо не вдалося підключитися до сервера Redis або
                         `REDIS_URL` не вказано в налаштуваннях.
    """
    global _redis_client
    if _redis_client is None:
        if not settings.REDIS_URL:
            logger.error("REDIS_URL не налаштовано. Неможливо ініціалізувати клієнт Redis.")
            # TODO i18n: Translatable message (хоча це переважно для логів/розробників)
            raise ConnectionError("REDIS_URL не налаштовано в конфігурації.")
        try:
            # Створення екземпляра клієнта Redis з URL-адреси, вказаної в налаштуваннях.
            # `aioredis.from_url` автоматично обробляє парсинг DSN.
            logger.info(f"Спроба підключення до Redis за адресою: {settings.REDIS_URL}")
            _redis_client = aioredis.from_url(
                str(settings.REDIS_URL), # REDIS_URL з settings.py
                encoding="utf-8",        # Кодування для рядків
                decode_responses=True    # Автоматично декодувати відповіді з байтів у рядки UTF-8.
                                         # Це зручно, якщо ви переважно працюєте з текстовими даними.
            )
            # Перевірка з'єднання з сервером Redis
            await _redis_client.ping()
            logger.info(f"Успішно підключено до Redis та отримано відповідь на ping: {settings.REDIS_URL}")
        except Exception as e:
            logger.error(f"Помилка підключення до Redis ({settings.REDIS_URL}): {e}", exc_info=True)
            # Скидаємо _redis_client, щоб при наступній спробі відбулася повторна ініціалізація.
            _redis_client = None
            # TODO i18n: Translatable message (хоча це переважно для логів/розробників)
            raise ConnectionError(f"Не вдалося підключитися до Redis ({settings.REDIS_URL}): {e}")
    return _redis_client

async def close_redis_client():
    """
    Закриває активне з'єднання з Redis, якщо воно було ініціалізоване.

    Цю функцію слід викликати при завершенні роботи програми (наприклад,
    в обробнику події `shutdown` FastAPI), щоб коректно звільнити ресурси.
    """
    global _redis_client
    if _redis_client:
        logger.info("Закриття з'єднання з Redis...")
        await _redis_client.close()
        _redis_client = None # Скидання глобальної змінної
        logger.info("З'єднання з Redis успішно закрито.")
    else:
        logger.info("Спроба закрити з'єднання з Redis, але клієнт не був ініціалізований.")

# --- Залежність FastAPI для надання клієнта Redis ---
async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Асинхронна функція-залежність для FastAPI, яка надає клієнт Redis.

    Ця залежність отримує клієнт Redis за допомогою `get_redis_client()`.
    Оскільки використовується глобальний клієнт, він не закривається після кожного запиту,
    а управляється централізовано через `get_redis_client` та `close_redis_client`.

    Yields:
        aioredis.Redis: Асинхронний клієнт Redis, готовий до використання.
    """
    client = await get_redis_client() # Отримуємо глобальний клієнт
    try:
        yield client # Передаємо клієнт в обробник запиту
    finally:
        # Життєвий цикл глобального клієнта Redis керується функціями
        # `get_redis_client` (ініціалізація) та `close_redis_client` (закриття при виході з програми).
        # Тому тут не потрібно явно закривати `client`.
        pass

# Блок для демонстраційних цілей або простого тестування функціональності модуля
if __name__ == "__main__":
    import asyncio

    # Налаштування логування для тестування (якщо воно ще не налаштоване)
    try:
        from backend.app.src.config.logging import setup_logging
        setup_logging()
    except ImportError:
        logging.basicConfig(level=logging.INFO) # Базове налаштування, якщо setup_logging недоступний
        logger.warning("Не вдалося імпортувати setup_logging. Використовується базова конфігурація логування.")


    async def main_redis_test():
        """Основна функція для тестування підключення та операцій Redis."""
        logger.info("Запуск тестування модуля Redis...")
        try:
            redis_cli = await get_redis_client()
            logger.info(f"Клієнт Redis успішно отримано: {redis_cli}")

            # Приклад використання клієнта Redis:
            await redis_cli.set("test_kudos_key", "Привіт від Kudos з Redis!")
            logger.info("Тестовий ключ 'test_kudos_key' встановлено.")

            value = await redis_cli.get("test_kudos_key")
            logger.info(f"Отримане значення з Redis для 'test_kudos_key': {value}")

            await redis_cli.delete("test_kudos_key")
            logger.info("Тестовий ключ 'test_kudos_key' видалено.")

        except ConnectionError as e:
            logger.error(f"Помилка з'єднання під час тестування Redis: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Неочікувана помилка під час тестування Redis: {e}", exc_info=True)
        finally:
            logger.info("Завершення тестування модуля Redis, закриття з'єднання...")
            await close_redis_client()

    asyncio.run(main_redis_test())
