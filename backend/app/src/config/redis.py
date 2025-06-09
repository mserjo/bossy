import redis.asyncio as aioredis
from typing import Optional, AsyncGenerator

from backend.app.src.config.settings import settings

# Глобальна змінна для зберігання екземпляра клієнта Redis
# Це дозволяє ініціалізувати клієнт один раз і використовувати його повторно.
_redis_client: Optional[aioredis.Redis] = None

async def get_redis_client() -> aioredis.Redis:
    """
    Надає асинхронний екземпляр клієнта Redis.

    Ця функція ініціалізує клієнт Redis, якщо він ще не був ініціалізований,
    використовуючи REDIS_URL з налаштувань програми.
    Вона призначена для використання як залежність у FastAPI або інших частинах програми,
    які потребують доступу до Redis.

    Returns:
        aioredis.Redis: Ініціалізований асинхронний клієнт Redis.

    Raises:
        ConnectionError: Якщо клієнт Redis не може бути ініціалізований або підключений до сервера.
    """
    global _redis_client
    if _redis_client is None:
        try:
            # Створити екземпляр клієнта Redis з URL-адреси в налаштуваннях
            # Метод from_url обробляє парсинг DSN та налаштування клієнта.
            _redis_client = aioredis.from_url(
                str(settings.REDIS_URL), # Переконайтеся, що REDIS_URL є рядком
                encoding="utf-8",
                decode_responses=True # Автоматично декодувати відповіді з байтів у рядки
            )
            # Перевірити з'єднання
            await _redis_client.ping()
            print(f"Успішно підключено до Redis за адресою {settings.REDIS_URL}")
        except Exception as e:
            # Залогувати помилку або обробити її відповідно до потреб вашої програми
            print(f"Помилка підключення до Redis: {e}")
            # Залежно від потреб програми, ви можете викликати помилку
            # або дозволити програмі продовжувати роботу без Redis (наприклад, з вимкненим кешуванням).
            # Наразі ми викличемо ConnectionError, щоб зробити це явним.
            _redis_client = None # Переконайтеся, що клієнт None, якщо з'єднання не вдалося
            raise ConnectionError(f"Не вдалося підключитися до Redis: {e}")
    return _redis_client

async def close_redis_client():
    """
    Закриває з'єднання клієнта Redis, якщо воно було ініціалізоване.
    Це корисно для коректного завершення роботи програми.
    """
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None # Скинути глобальну змінну клієнта
        print("З'єднання Redis закрито.")

# --- Опціонально: обгортка залежності FastAPI ---
async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Залежність FastAPI, яка надає клієнт Redis для одного запиту.
    Це альтернатива прямому використанню глобального клієнта, якщо ви віддаєте перевагу
    керуванню життєвим циклом клієнта Redis для кожного запиту або з пулом з'єднань для кожного запиту.

    Однак для багатьох випадків використання єдиний глобальний клієнт (`get_redis_client`) є достатнім
    і більш продуктивним завдяки повторному використанню з'єднань.

    Yields:
        aioredis.Redis: Асинхронний клієнт Redis.
    """
    client = await get_redis_client() # Повторно використовує логіку глобального клієнта
    try:
        yield client
    finally:
        # Зазвичай, ви не закриваєте тут клієнт, отриманий з get_redis_client(),
        # якщо він призначений бути довготривалим глобальним клієнтом. Закриття з'єднання обробляється
        # `close_redis_client()` під час завершення роботи програми.
        pass

if __name__ == "__main__":
    import asyncio

    async def main():
        print("Спроба підключитися до Redis...")
        try:
            redis_client = await get_redis_client()
            print(f"Клієнт Redis отримано: {redis_client}")

            # Приклад використання:
            await redis_client.set("mykey", "Привіт від Redis!")
            value = await redis_client.get("mykey")
            print(f"Отримане значення з Redis: {value}")
            await redis_client.delete("mykey")
            print("Тестовий ключ очищено.")

        except ConnectionError as e:
            print(f"Не вдалося підключитися або використати Redis: {e}")
        except Exception as e:
            print(f"Сталася неочікувана помилка: {e}")
        finally:
            await close_redis_client()

    asyncio.run(main())
