# backend/app/src/services/cache/redis_service.py
"""
Сервіс кешування з використанням Redis.

Конкретна реалізація `BaseCacheService`, що взаємодіє з Redis
для зберігання, отримання та управління кешованими даними.
Включає логіку серіалізації/десеріалізації даних.
"""
import json  # Для серіалізації/десеріалізації складних типів даних
from typing import Optional, Any, Set # List видалено
from decimal import Decimal  # Для обробки типу Decimal

import redis.asyncio as aioredis  # Використання асинхронних можливостей redis-py

from backend.app.src.services.cache.base_cache import BaseCacheService
from backend.app.src.config.redis import get_redis_client  # Змінено на get_redis_client
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


# TODO: [Serialization] Розглянути використання більш надійної бібліотеки або підходів для серіалізації/десеріалізації.
#  Поточна реалізація json.dumps/loads може не коректно обробляти всі типи (наприклад, datetime без кастомного енкодера).
#  Для Pydantic моделей краще використовувати model_dump_json() / model_validate_json(), але це потребує інформації про тип при десеріалізації.
#  Можливі альтернативи: msgpack. Уникати pickle через проблеми з безпекою, якщо дані кешу не є повністю довіреними.
#  Також варто додати обробку datetime об'єктів у _serialize_value та _deserialize_value.

# Допоміжні функції для серіалізації/десеріалізації значень
def _serialize_value(value: Any) -> str:
    """Серіалізує значення Python у рядок для зберігання в Redis."""
    if isinstance(value, str):
        return value  # Рядки зберігаються як є
    if isinstance(value, bool):  # Явна перевірка для bool
        return "true" if value else "false"  # Зберігаємо як 'true'/'false' для консистентності
    if isinstance(value, (int, float)):  # Числа перетворюються на рядки
        return str(value)
    if isinstance(value, Decimal):
        return f"decimal:{str(value)}"  # Спеціальний префікс для Decimal
    if isinstance(value, datetime):
        return f"datetime:{value.isoformat()}" # Спеціальний префікс для datetime
    try:
        # Для складних типів (dict, list, Pydantic моделі через .dict()) використовуємо JSON
        return f"json:{json.dumps(value)}"
    except TypeError as e:
        logger.warning(
            f"Не вдалося серіалізувати значення типу {type(value)} в JSON. Зберігання як рядок. Помилка: {e}")  # i18n log
        return str(value)  # Запасний варіант


def _deserialize_value(value_str: Optional[str]) -> Any:
    """Десеріалізує рядок з Redis у значення Python."""
    if value_str is None:
        return None

    if value_str.startswith("datetime:"):
        try:
            return datetime.fromisoformat(value_str[len("datetime:"):])
        except ValueError as e:
            logger.error(f"Не вдалося десеріалізувати datetime значення '{value_str}': {e}. Повернення None.", exc_info=True)
            return None
    if value_str.startswith("json:"):
        try:
            return json.loads(value_str[len("json:"):])
        except json.JSONDecodeError as e:
            logger.error(
                f"Не вдалося десеріалізувати JSON значення '{value_str[:100]}...': {e}. Повернення частини рядка.",
                exc_info=True)  # i18n log
            return value_str[len("json:"):]  # Повертаємо "сиру" частину рядка

    if value_str.startswith("decimal:"):
        try:
            return Decimal(value_str[len("decimal:"):])
        except Exception as e:
            logger.error(f"Не вдалося десеріалізувати Decimal значення '{value_str}': {e}. Повернення None.",
                         exc_info=True)  # i18n log
            return None

    # Перевірка для bool значень 'true'/'false'
    if value_str == 'true': return True
    if value_str == 'false': return False

    # Спроба конвертації в int, потім float
    try:
        return int(value_str)
    except ValueError:
        pass
    try:
        return float(value_str)
    except ValueError:
        pass

    return value_str  # Якщо нічого не підійшло, повертаємо як рядок


class RedisCacheService(BaseCacheService):
    """
    Конкретна реалізація BaseCacheService, що використовує Redis як бекенд.
    Обробляє підключення до Redis, серіалізацію/десеріалізацію та операції кешування.
    """

    # service_name = "REDIS_CACHE" # Опціонально

    def __init__(self):
        super().__init__()
        self._redis_client: Optional[aioredis.Redis] = None
        # Ініціалізація клієнта відбувається "ліниво" при першому запиті або може бути викликана при старті додатку.
        # Для негайної ініціалізації можна викликати self._initialize_client() тут,
        # але це може бути проблематично в контексті асинхронного запуску (поза event loop).
        # Краще покладатися на _get_client для ініціалізації при потребі.
        logger.info("RedisCacheService створено, клієнт буде ініціалізовано при першому використанні.")

    async def _get_client(self) -> aioredis.Redis:
        """
        Забезпечує наявність активного Redis клієнта.
        Якщо клієнт не ініціалізований, намагається його ініціалізувати.
        :raises ConnectionError: Якщо клієнт не вдалося ініціалізувати.
        """
        if self._redis_client is None:
            logger.info("Redis клієнт не ініціалізований. Спроба ініціалізації через get_redis_client...")
            try:
                # get_redis_client є асинхронною функцією
                self._redis_client = await get_redis_client()
                logger.info("RedisCacheService: клієнт успішно отримано/ініціалізовано.")
            except ConnectionError as e:
                logger.error(f"RedisCacheService: не вдалося ініціалізувати клієнта Redis через get_redis_client: {e}")
                # Можна залишити self._redis_client як None, помилка буде кинута нижче
                # або кинути помилку тут же
                raise  # Перекидаємо помилку ConnectionError з get_redis_client
            except Exception as e:
                logger.error(f"RedisCacheService: неочікувана помилка при ініціалізації клієнта Redis: {e}", exc_info=True)
                self._redis_client = None # Залишаємо None, щоб наступний блок кинув помилку

        if self._redis_client is None:
            # i18n
            raise ConnectionError("Клієнт Redis не ініціалізований або не вдалося підключитися.")
        return self._redis_client

    async def get(self, key: str) -> Optional[Any]:
        """Отримує елемент з кешу Redis за ключем."""
        try:
            client = await self._get_client()
            value_bytes = await client.get(key)
            if value_bytes is not None:
                value_str = value_bytes.decode('utf-8')
                deserialized_value = _deserialize_value(value_str)
                logger.debug(
                    f"Кеш GET (Redis): ключ='{key}', значення='{str(deserialized_value)[:100]}...' (тип: {type(deserialized_value)})")
                return deserialized_value
            logger.debug(f"Кеш GET (Redis): ключ='{key}' не знайдено.")
            return None
        except ConnectionError:  # Якщо _get_client кинув помилку
            logger.error(f"Кеш GET (Redis): помилка з'єднання для ключа '{key}'.")
            return None  # Або re-raise, залежно від бажаної поведінки
        except Exception as e:
            logger.error(f"Кеш GET (Redis) помилка для ключа '{key}': {e}", exc_info=True)
            return None  # Повертаємо None при будь-якій помилці кешу

    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """Зберігає елемент в кеші Redis."""
        try:
            client = await self._get_client()
            serialized_value = _serialize_value(value)
            # `ex` - час життя в секундах
            result = await client.set(name=key, value=serialized_value, ex=expire_seconds)
            logger.debug(
                f"Кеш SET (Redis): ключ='{key}', значення='{serialized_value[:100]}...', expire_seconds={expire_seconds}. Результат: {result}")
            return bool(result)  # Повертає True при успіху, інакше може кинути помилку або повернути False
        except ConnectionError:
            logger.error(f"Кеш SET (Redis): помилка з'єднання для ключа '{key}'.")
            return False
        except Exception as e:
            logger.error(f"Кеш SET (Redis) помилка для ключа '{key}': {e}", exc_info=True)
            return False

    async def delete(self, key: str) -> bool:
        """Видаляє елемент з кешу Redis за ключем."""
        try:
            client = await self._get_client()
            num_deleted = await client.delete(key)
            # client.delete повертає кількість видалених ключів (0 або 1 в даному випадку)
            logger.debug(f"Кеш DELETE (Redis): ключ='{key}'. Кількість видалених: {num_deleted}")
            return True  # Відповідає інтерфейсу (True, якщо видалено або не існувало)
        except ConnectionError:
            logger.error(f"Кеш DELETE (Redis): помилка з'єднання для ключа '{key}'.")
            return False
        except Exception as e:
            logger.error(f"Кеш DELETE (Redis) помилка для ключа '{key}': {e}", exc_info=True)
            return False

    async def exists(self, key: str) -> bool:
        """Перевіряє, чи існує ключ в кеші Redis."""
        try:
            client = await self._get_client()
            exists_result = await client.exists(key)
            # client.exists повертає кількість знайдених ключів (0 або 1)
            logger.debug(f"Кеш EXISTS (Redis): ключ='{key}'. Результат: {exists_result > 0}")
            return exists_result > 0
        except ConnectionError:
            logger.error(f"Кеш EXISTS (Redis): помилка з'єднання для ключа '{key}'.")
            return False
        except Exception as e:
            logger.error(f"Кеш EXISTS (Redis) помилка для ключа '{key}': {e}", exc_info=True)
            return False

    async def clear_all_prefix(self, prefix: str) -> int:
        """Видаляє всі записи кешу Redis, ключі яких починаються з заданого префіксу, використовуючи SCAN."""
        try:
            client = await self._get_client()
            # Переконуємося, що префікс не порожній і закінчується на '*' для SCAN
            if not prefix:
                logger.warning("Кеш CLEAR_ALL_PREFIX (Redis): Надано порожній префікс. Операцію скасовано.")
                return 0

            prefix_pattern = f"{prefix}*" if not prefix.endswith('*') else prefix

            logger.warning(
                f"Кеш CLEAR_ALL_PREFIX (Redis): Спроба видалення ключів за шаблоном '{prefix_pattern}'. Це може бути тривалою операцією.")
            deleted_count = 0
            cursor = 0  # Для aioredis.Redis.scan курсор є int
            while True:
                cursor, keys_bytes = await client.scan(cursor=cursor, match=prefix_pattern,
                                                       count=1000)  # count - підказка для Redis
                if keys_bytes:
                    # Конвертуємо ключі з байтів у рядки для логування та консистентності
                    # Хоча client.delete може приймати байти напряму
                    keys_to_delete_str = [k.decode('utf-8') for k in keys_bytes]
                    logger.debug(f"Видалення пакету з {len(keys_to_delete_str)} ключів, що починаються з '{prefix}'.")
                    num_deleted_batch = await client.delete(*keys_to_delete_str)  # Передаємо як окремі аргументи
                    deleted_count += num_deleted_batch
                if cursor == 0:  # Кінець ітерації SCAN
                    break
            logger.info(
                f"Кеш CLEAR_ALL_PREFIX (Redis): Видалено {deleted_count} ключів за шаблоном '{prefix_pattern}'.")
            return deleted_count
        except ConnectionError:
            logger.error(f"Кеш CLEAR_ALL_PREFIX (Redis): помилка з'єднання для префіксу '{prefix}'.")
            return 0
        except Exception as e:
            logger.error(f"Кеш CLEAR_ALL_PREFIX (Redis) помилка для префіксу '{prefix}': {e}", exc_info=True)
            return 0  # Повертаємо 0, оскільки не можемо гарантувати кількість видалених

    async def clear_all(self) -> bool:
        """Очищає всю поточну базу даних Redis. Використовувати з обережністю!"""
        try:
            client = await self._get_client()
            logger.warning(
                "Кеш CLEAR_ALL (Redis): Спроба очищення всієї поточної бази даних Redis (FLUSHDB). Це деструктивна операція!")
            await client.flushdb()
            logger.info("Кеш CLEAR_ALL (Redis): Поточну базу даних Redis успішно очищено.")
            return True
        except ConnectionError:
            logger.error(f"Кеш CLEAR_ALL (Redis): помилка з'єднання.")
            return False
        except Exception as e:
            logger.error(f"Кеш CLEAR_ALL (Redis) помилка: {e}", exc_info=True)
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Атомарно збільшує цілочисельне значення ключа в Redis."""
        try:
            client = await self._get_client()
            # INCRBY повертає нове значення ключа
            new_value = await client.incrby(name=key, amount=amount)
            logger.debug(f"Кеш INCREMENT (Redis): ключ='{key}', сума={amount}. Нове значення: {new_value}")
            return int(new_value)
        except ConnectionError:
            logger.error(f"Кеш INCREMENT (Redis): помилка з'єднання для ключа '{key}'.")
            return None
        except aioredis.exceptions.ResponseError as e:
            logger.error(
                f"Кеш INCREMENT (Redis) помилка відповіді для ключа '{key}': {e}. Можливо, значення не є цілим числом або рядком, що представляє число.",
                exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Кеш INCREMENT (Redis) помилка для ключа '{key}': {e}", exc_info=True)
            return None

    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Атомарно зменшує цілочисельне значення ключа в Redis."""
        try:
            client = await self._get_client()
            # DECRBY повертає нове значення ключа
            new_value = await client.decrby(name=key, amount=amount)
            logger.debug(f"Кеш DECREMENT (Redis): ключ='{key}', сума={amount}. Нове значення: {new_value}")
            return int(new_value)
        except ConnectionError:
            logger.error(f"Кеш DECREMENT (Redis): помилка з'єднання для ключа '{key}'.")
            return None
        except aioredis.exceptions.ResponseError as e:
            logger.error(
                f"Кеш DECREMENT (Redis) помилка відповіді для ключа '{key}': {e}. Можливо, значення не є цілим числом або рядком, що представляє число.",
                exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Кеш DECREMENT (Redis) помилка для ключа '{key}': {e}", exc_info=True)
            return None

    async def set_add(self, key: str, *values: Any, expire_seconds: Optional[int] = None) -> int:
        """
        Додає елементи до множини в Redis.
        Опціонально встановлює або оновлює TTL для ключа.

        :param key: Ключ множини.
        :param values: Значення для додавання.
        :param expire_seconds: Час життя в секундах. Якщо <= 0, ключ буде видалено.
        :return: Кількість фактично доданих нових елементів.
        """
        if not values: return 0 # Нічого не додавати, якщо значення не надані
        try:
            client = await self._get_client()

            if expire_seconds is not None and expire_seconds <= 0:
                logger.debug(f"Кеш SADD (Redis): ключ='{key}' з непозитивним expire_seconds ({expire_seconds}). Видалення ключа.")
                await client.delete(key)
                return 0 # Елементи не були ефективно додані на тривалий термін

            serialized_values = [_serialize_value(v) for v in values]
            num_added = await client.sadd(key, *serialized_values)

            if expire_seconds is not None: # Тут expire_seconds > 0
                await client.expire(key, expire_seconds)
                logger.debug(f"Кеш SADD (Redis): ключ='{key}', додано {num_added} з {len(values)} наданих значень. Встановлено TTL: {expire_seconds}s.")
            else:
                logger.debug(f"Кеш SADD (Redis): ключ='{key}', додано {num_added} з {len(values)} наданих значень. TTL не змінено/встановлено.")

            return num_added
        except ConnectionError:
            logger.error(f"Кеш SADD (Redis): помилка з'єднання для ключа '{key}'.")
            return 0
        except Exception as e:
            logger.error(f"Кеш SADD (Redis) помилка для ключа '{key}': {e}", exc_info=True)
            return 0

    async def set_get_all(self, key: str) -> Set[Any]:
        """Повертає всі елементи множини з Redis."""
        try:
            client = await self._get_client()
            members_bytes: Set[bytes] = await client.smembers(key)
            deserialized_members = {_deserialize_value(m.decode('utf-8')) for m in members_bytes}
            logger.debug(f"Кеш SMEMBERS (Redis): ключ='{key}', отримано {len(deserialized_members)} елементів.")
            return deserialized_members
        except ConnectionError:
            logger.error(f"Кеш SMEMBERS (Redis): помилка з'єднання для ключа '{key}'.")
            return set()
        except Exception as e:
            logger.error(f"Кеш SMEMBERS (Redis) помилка для ключа '{key}': {e}", exc_info=True)
            return set()

    async def set_remove(self, key: str, *values: Any) -> int:
        """Видаляє елементи з множини в Redis."""
        if not values: return 0
        try:
            client = await self._get_client()
            serialized_values = [_serialize_value(v) for v in values]
            num_removed = await client.srem(key, *serialized_values)
            logger.debug(f"Кеш SREM (Redis): ключ='{key}', видалено {num_removed} з {len(values)} наданих значень.")
            return num_removed
        except ConnectionError:
            logger.error(f"Кеш SREM (Redis): помилка з'єднання для ключа '{key}'.")
            return 0
        except Exception as e:
            logger.error(f"Кеш SREM (Redis) помилка для ключа '{key}': {e}", exc_info=True)
            return 0

    async def set_is_member(self, key: str, value: Any) -> bool:
        """Перевіряє, чи є елемент членом множини в Redis."""
        try:
            client = await self._get_client()
            serialized_value = _serialize_value(value)
            is_member = await client.sismember(key, serialized_value)
            logger.debug(f"Кеш SISMEMBER (Redis): ключ='{key}', значення='{serialized_value}', є членом: {is_member}.")
            return bool(is_member)
        except ConnectionError:
            logger.error(f"Кеш SISMEMBER (Redis): помилка з'єднання для ключа '{key}'.")
            return False
        except Exception as e:
            logger.error(f"Кеш SISMEMBER (Redis) помилка для ключа '{key}', значення='{value}': {e}", exc_info=True)
            return False


logger.info("RedisCacheService клас визначено.")
