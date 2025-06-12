# backend/app/src/config/redis.py
# -*- coding: utf-8 -*-
"""Налаштування та управління з'єднанням з Redis для додатку.

Цей модуль відповідає за ініціалізацію, надання та закриття асинхронного
клієнта Redis. Він використовує глобальний екземпляр клієнта для ефективного
повторного використання з'єднань протягом життєвого циклу програми.

Основні компоненти:
- `_redis_client`: Глобальна змінна для зберігання єдиного екземпляра `redis.asyncio.Redis`.
- `get_redis_client()`: Асинхронна функція для отримання (та ініціалізації
  при першому виклику) глобального клієнта Redis. Включає перевірку з'єднання
  (ping) та обробку можливих помилок підключення.
- `close_redis_client()`: Асинхронна функція для коректного закриття
  з'єднання з Redis, зазвичай викликається при завершенні роботи програми
  (наприклад, під час події `shutdown` у FastAPI).
- `get_redis()`: Асинхронна функція-залежність (dependency) для FastAPI,
  яка надає доступ до глобального клієнта Redis в обробниках запитів.

Налаштування Redis (URL та інші параметри) беруться з об'єкта `settings`
(з `backend.app.src.config.settings`). Використовується бібліотека `redis[hiredis]`
та її модуль `redis.asyncio` для асинхронної взаємодії з Redis.
"""
import asyncio # Для демонстраційного блоку if __name__ == "__main__"
from typing import AsyncGenerator, Optional

import redis.asyncio as aioredis # Використовуємо redis.asyncio для асинхронного клієнта

# Абсолютний імпорт налаштувань та централізованого логера
from backend.app.src.config import logger, settings

# Глобальна змінна для зберігання єдиного екземпляра клієнта Redis.
# Це дозволяє ініціалізувати клієнт один раз і повторно використовувати його
# протягом життєвого циклу програми, що є більш ефективним, ніж створення
# нового підключення для кожного запиту.
_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """Надає (та за потреби ініціалізує) глобальний асинхронний екземпляр клієнта Redis.

    При першому виклику ця функція ініціалізує клієнт Redis, використовуючи
    `REDIS_URL` з конфігураційних налаштувань. Вона також виконує команду `PING`
    для перевірки успішності з'єднання. При наступних викликах повертає
    вже існуючий, ініціалізований екземпляр клієнта.

    Returns:
        aioredis.Redis: Ініціалізований та підключений асинхронний клієнт Redis.

    Raises:
        ConnectionError: Якщо `REDIS_URL` не вказано в налаштуваннях, або якщо
                         не вдалося підключитися до сервера Redis чи виконати `PING`.
    """
    global _redis_client
    if _redis_client is None:
        if not settings.REDIS_URL:
            logger.error("REDIS_URL не налаштовано. Неможливо ініціалізувати клієнт Redis.")
            # TODO i18n: Повідомлення для перекладу (хоча це переважно для логів/розробників)
            # Можна розглянути кастомний виняток, якщо потрібно обробляти цю помилку специфічно.
            raise ConnectionError("URL для підключення до Redis (REDIS_URL) не налаштовано в конфігурації.")
        try:
            # Створення екземпляра клієнта Redis з URL-адреси, вказаної в налаштуваннях.
            # `aioredis.from_url` автоматично обробляє парсинг DSN (Data Source Name).
            logger.info("Спроба підключення до Redis за адресою: %s", settings.REDIS_URL)
            _redis_client = aioredis.from_url(
                str(settings.REDIS_URL),  # Переконуємось, що URL є рядком
                encoding="utf-8",         # Стандартне кодування для рядків
                decode_responses=True     # Автоматично декодувати відповіді з байтів у рядки UTF-8.
                                          # Це зручно, якщо ви переважно працюєте з текстовими даними.
            )
            # Перевірка з'єднання з сервером Redis шляхом виконання команди PING
            await _redis_client.ping()
            logger.info("Успішно підключено до Redis та отримано відповідь на PING: %s", settings.REDIS_URL)
        except Exception as e: # pylint: disable=broad-except
            # Логуємо детальну помилку та скидаємо _redis_client,
            # щоб при наступній спробі відбулася повторна ініціалізація.
            logger.error(
                "Помилка підключення до Redis (%s): %s", settings.REDIS_URL, e, exc_info=True
            )
            _redis_client = None # Важливо для можливості повторної спроби
            # TODO i18n: Повідомлення для перекладу (для логів/розробників)
            raise ConnectionError(
                f"Не вдалося підключитися до Redis ({settings.REDIS_URL}) або виконати PING: {e}"
            )
    return _redis_client


async def close_redis_client() -> None:
    """Закриває активне з'єднання з Redis, якщо воно було ініціалізоване.

    Цю функцію слід викликати при завершенні роботи програми (наприклад,
    в обробнику події `shutdown` FastAPI), щоб коректно звільнити ресурси
    та закрити мережеві з'єднання.
    """
    global _redis_client
    if _redis_client:
        logger.info("Закриття з'єднання з Redis...")
        try:
            await _redis_client.close()
            logger.info("З'єднання з Redis успішно закрито.")
        except Exception as e: # pylint: disable=broad-except
            logger.error("Помилка під час закриття з'єднання з Redis: %s", e, exc_info=True)
        finally:
            _redis_client = None # Скидання глобальної змінної в будь-якому випадку
    else:
        logger.info("Спроба закрити з'єднання з Redis, але клієнт не був ініціалізований.")


# --- Залежність FastAPI для надання клієнта Redis ---
async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Асинхронна функція-залежність для FastAPI, яка надає клієнт Redis.

    Ця залежність отримує клієнт Redis за допомогою `get_redis_client()`.
    Оскільки використовується глобальний, спільно використовуваний клієнт,
    він не закривається після кожного запиту. Його життєвий цикл керується
    централізовано через функції `get_redis_client` (ініціалізація при першому
    запиті або при старті програми) та `close_redis_client` (закриття
    при завершенні роботи програми).

    Yields:
        aioredis.Redis: Асинхронний клієнт Redis, готовий до використання в обробнику запиту.
    """
    # Отримуємо (або ініціалізуємо) глобальний клієнт Redis
    redis_client = await get_redis_client()
    try:
        logger.debug("Надано клієнт Redis (%s) для обробника запиту.", id(redis_client))
        yield redis_client # Передаємо клієнт в обробник запиту
    finally:
        # Життєвий цикл глобального клієнта Redis керується централізовано.
        # Тут не потрібно явно закривати `redis_client`, оскільки він
        # призначений для повторного використання протягом роботи додатку.
        # Закриття відбувається лише при виході з програми через `close_redis_client`.
        logger.debug("Завершено використання клієнта Redis (%s) для поточного запиту.", id(redis_client))


# Блок для демонстраційних цілей або простого тестування функціональності модуля
if __name__ == "__main__":
    # Логер вже налаштований через імпорт `from backend.app.src.config import logger, settings`
    # та виклик setup_logging() в __init__.py пакета config.
    # Якщо цей файл запускається абсолютно окремо і config.__init__ не виконувався,
    # може знадобитися локальне налаштування логування тут.
    # Однак, припускаючи, що logger з config вже налаштований:

    async def main_redis_test() -> None:
        """Основна функція для тестування підключення та операцій Redis."""
        logger.info("=== Запуск тестування модуля Redis ===")
        redis_cli = None # Ініціалізуємо змінну
        try:
            redis_cli = await get_redis_client()
            logger.info("Клієнт Redis успішно отримано: %s", redis_cli)

            # Приклад використання клієнта Redis:
            test_key = "test_kudos_app_key"
            test_value = "Привіт від Kudos з Redis! Перевірка UTF-8: українські літери."

            await redis_cli.set(test_key, test_value)
            logger.info("Тестовий ключ '%s' успішно встановлено зі значенням '%s'.", test_key, test_value)

            retrieved_value = await redis_cli.get(test_key)
            logger.info("Отримане значення з Redis для ключа '%s': '%s'", test_key, retrieved_value)
            assert retrieved_value == test_value, \
                f"Отримане значення '{retrieved_value}' не співпадає з очікуваним '{test_value}'."

            await redis_cli.delete(test_key)
            logger.info("Тестовий ключ '%s' успішно видалено.", test_key)
            assert await redis_cli.get(test_key) is None, "Ключ все ще існує після видалення."

            logger.info("Тестування операцій Redis пройшло успішно.")

        except ConnectionError as e:
            logger.error("Помилка з'єднання під час тестування Redis: %s", e, exc_info=True)
        except Exception as e: # pylint: disable=broad-except
            logger.error("Неочікувана помилка під час тестування Redis: %s", e, exc_info=True)
        finally:
            logger.info("Завершення тестування модуля Redis, спроба закрити з'єднання...")
            # close_redis_client закриє глобальний _redis_client, якщо він був ініціалізований.
            await close_redis_client()
            # Перевірка, чи _redis_client справді None після закриття
            assert _redis_client is None, "Глобальний _redis_client не було скинуто після close_redis_client."
            logger.info("Тестування Redis завершено.")

    asyncio.run(main_redis_test())
