# backend/app/src/services/cache/memory_service.py
"""
Сервіс кешування в пам'яті.

Конкретна реалізація `BaseCacheService`, що використовує словник Python
для зберігання даних кешу в оперативній пам'яті. Підходить для розробки,
тестування або невеликих однопроцесних застосунків.
"""
import time  # Для обробки терміну дії
from typing import Optional, Any, Dict, Set # Union видалено
from datetime import datetime, timedelta, timezone  # Для точного терміну дії в логах

from backend.app.src.services.cache.base_cache import BaseCacheService
from backend.app.src.config.logging import get_logger  # Стандартизований імпорт логера
logger = get_logger(__name__) # Ініціалізація логера


# TODO: [Concurrency] Розглянути використання asyncio.Lock для операцій читання-модифікації-запису
#       для підвищення потокобезпечності, особливо якщо методи стануть більш складними
#       та матимуть `await` у критичних секціях.
#       Для простих операцій з dict GIL Python часто надає достатній захист.
#  хоча для простих операцій з dict GIL Python часто надає достатній захист.

# Внутрішній клас для зберігання записів кешу з інформацією про термін дії
class _CacheEntry:
    """
    Внутрішній клас для зберігання значення кешу та часу його закінчення.
    """

    def __init__(self, value: Any,
                 expire_at: Optional[float] = None):  # expire_at - це Unix timestamp від time.monotonic()
        self.value: Any = value  # Значення, що зберігається
        self.expire_at: Optional[float] = expire_at  # Монотонний час закінчення терміну дії або None

    def is_expired(self) -> bool:
        """
        Перевіряє, чи закінчився термін дії запису.
        :return: True, якщо термін дії закінчився, інакше False.
        """
        if self.expire_at is None:
            return False  # Ніколи не закінчується
        return time.monotonic() >= self.expire_at


class InMemoryCacheService(BaseCacheService):
    """
    Конкретна реалізація BaseCacheService, що використовує простий словник Python
    для кешування в пам'яті. Обробляє закінчення терміну дії елементів.

    Підходить для розробки, тестування або невеликих однопроцесних розгортань.
    Не підходить для багатопроцесних або розподілених середовищ, оскільки кеш є локальним для процесу.
    """

    # service_name = "IN_MEMORY_CACHE" # Опціонально, для ідентифікації сервісу

    def __init__(self):
        super().__init__()
        self._cache: Dict[str, _CacheEntry] = {}  # Сховище кешу
        logger.info("InMemoryCacheService (кеш в пам'яті) ініціалізовано.")

    async def get(self, key: str) -> Optional[Any]:
        """Отримує елемент з кешу за ключем."""
        entry = self._cache.get(key)
        if entry:
            if entry.is_expired():
                logger.debug(f"Кеш GET: ключ='{key}' знайдено, але термін дії закінчився. Видалення.")
                await self.delete(key)  # Видаляємо прострочений ключ
                return None
            logger.debug(f"Кеш GET: ключ='{key}', значення='{str(entry.value)[:100]}...' (тип: {type(entry.value)})")
            return entry.value
        logger.debug(f"Кеш GET: ключ='{key}' не знайдено.")
        return None

    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """Зберігає елемент в кеші."""
        expire_at: Optional[float] = None
        if expire_seconds is not None:
            if expire_seconds <= 0:  # Якщо термін дії не позитивний, видаляємо ключ
                logger.debug(
                    f"Кеш SET: ключ='{key}' з непозитивним expire_seconds ({expire_seconds}). Видалення, якщо існує.")
                return await self.delete(key)
            expire_at = time.monotonic() + expire_seconds

        self._cache[key] = _CacheEntry(value, expire_at)

        log_expire_str = "безстроково"  # i18n
        if expire_at is not None:
            # Приблизний час UTC для логування (не для логіки)
            remaining_seconds = expire_at - time.monotonic()
            if remaining_seconds > 0:
                log_expire_dt = datetime.now(timezone.utc) + timedelta(seconds=remaining_seconds)
                log_expire_str = log_expire_dt.isoformat()
            else:
                log_expire_str = "в минулому (або негайно)"  # i18n

        logger.debug(
            f"Кеш SET: ключ='{key}', значення='{str(value)[:100]}...', expire_at (монотонний): {expire_at}, приблизний UTC час закінчення: {log_expire_str}")
        return True

    async def delete(self, key: str) -> bool:
        """Видаляє елемент з кешу за ключем."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Кеш DELETE: ключ='{key}' видалено.")
            return True
        logger.debug(f"Кеш DELETE: ключ='{key}' не знайдено, жодних дій.")
        return True  # Повертає True, навіть якщо ключ не існував, згідно з інтерфейсом

    async def exists(self, key: str) -> bool:
        """Перевіряє, чи існує ключ в кеші (і чи не прострочений)."""
        entry = self._cache.get(key)
        if entry:
            if not entry.is_expired():
                logger.debug(f"Кеш EXISTS: ключ='{key}' існує та активний.")
                return True
            else:  # Ключ існує, але прострочений
                logger.debug(f"Кеш EXISTS: ключ='{key}' знайдено, але термін дії закінчився. Очищення.")
                await self.delete(key)  # Проактивне очищення
        logger.debug(f"Кеш EXISTS: ключ='{key}' не знайдено або був прострочений та очищений.")
        return False

    async def clear_all_prefix(self, prefix: str) -> int:
        """Видаляє всі записи кешу, ключі яких починаються з заданого префіксу."""
        logger.info(f"Кеш CLEAR_ALL_PREFIX: Спроба видалення ключів з префіксом '{prefix}'.")
        # Створюємо копію ключів для безпечної ітерації та модифікації словника
        keys_to_delete = [key for key in list(self._cache.keys()) if key.startswith(prefix)]

        deleted_count = 0
        for key in keys_to_delete:
            entry = self._cache.get(key)  # Перевіряємо стан перед видаленням
            if entry and not entry.is_expired():
                deleted_count += 1  # Рахуємо тільки ті, що були активні
            # delete видалить ключ незалежно від того, чи був він прострочений
            await self.delete(key)

        logger.info(f"Кеш CLEAR_ALL_PREFIX: Видалено {deleted_count} активних ключів з префіксом '{prefix}'.")
        return deleted_count

    async def clear_all(self) -> bool:
        """Очищає весь кеш в пам'яті."""
        logger.warning("Кеш CLEAR_ALL: Повне очищення кешу в пам'яті.")
        self._cache.clear()
        logger.info("Кеш CLEAR_ALL: Кеш в пам'яті успішно очищено.")
        return True

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Атомарно збільшує цілочисельне значення ключа."""
        current_entry = self._cache.get(key)
        current_value = 0
        original_expire_at: Optional[float] = None

        if current_entry:
            if current_entry.is_expired():
                logger.debug(f"Кеш INCREMENT: ключ='{key}' був прострочений. Розглядається як новий.")
            elif isinstance(current_entry.value, int):
                current_value = current_entry.value
                original_expire_at = current_entry.expire_at  # Зберігаємо термін дії
            else:
                logger.error(
                    f"Кеш INCREMENT помилка для ключа '{key}': існуюче значення не є цілим числом (тип: {type(current_entry.value)}). Інкремент неможливий.")
                return None  # Помилка типу

        new_value = current_value + amount
        # Встановлюємо нове значення, зберігаючи оригінальний термін дії або None, якщо ключ новий/прострочений
        self._cache[key] = _CacheEntry(new_value, original_expire_at)
        logger.debug(f"Кеш INCREMENT: ключ='{key}', сума={amount}. Нове значення: {new_value}")
        return new_value

    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Атомарно зменшує цілочисельне значення ключа."""
        # Логіка аналогічна increment
        current_entry = self._cache.get(key)
        current_value = 0
        original_expire_at: Optional[float] = None

        if current_entry:
            if current_entry.is_expired():
                logger.debug(f"Кеш DECREMENT: ключ='{key}' був прострочений. Розглядається як новий.")
            elif isinstance(current_entry.value, int):
                current_value = current_entry.value
                original_expire_at = current_entry.expire_at
            else:
                logger.error(
                    f"Кеш DECREMENT помилка для ключа '{key}': існуюче значення не є цілим числом (тип: {type(current_entry.value)}). Декремент неможливий.")
                return None

        new_value = current_value - amount
        self._cache[key] = _CacheEntry(new_value, original_expire_at)
        logger.debug(f"Кеш DECREMENT: ключ='{key}', сума={amount}. Нове значення: {new_value}")
        return new_value

    async def set_add(self, key: str, *values: Any, expire_seconds: Optional[int] = None) -> int:
        """
        Додає один або більше елементів до множини, що зберігається за ключем.
        Оновлює TTL множини, якщо надано `expire_seconds`.

        :param key: Ключ множини.
        :param values: Значення для додавання до множини.
        :param expire_seconds: Опціональний час життя в секундах для множини.
        :return: Кількість елементів, що були фактично додані до множини.
        """
        entry = self._cache.get(key)
        current_set: Set[Any] = set()
        existing_expire_at: Optional[float] = None

        if entry and not entry.is_expired():
            if isinstance(entry.value, set):
                current_set = entry.value
                existing_expire_at = entry.expire_at  # Зберігаємо поточний TTL
            else:
                logger.warning(
                    f"Кеш SADD: ключ '{key}' існує, але не є множиною (тип: {type(entry.value)}). Буде перезаписано новою множиною.")
                # existing_expire_at залишається None, новий TTL буде встановлено нижче

        added_count = 0
        for v_item in values:
            if v_item not in current_set:
                current_set.add(v_item)
                added_count += 1

        new_expire_at = existing_expire_at # За замовчуванням зберігаємо старий TTL (або None, якщо його не було)

        if expire_seconds is not None:
            if expire_seconds <= 0:
                logger.debug(f"Кеш SADD: ключ='{key}' з непозитивним expire_seconds ({expire_seconds}). Видалення ключа.")
                # Якщо елементи були формально додані до current_set, але ключ видаляється, added_count відображає це.
                # Якщо ключ не існував, added_count може бути > 0, але нічого не збережеться.
                if key in self._cache: # Видаляємо тільки якщо ключ справді існував
                    await self.delete(key)
                return added_count
            new_expire_at = time.monotonic() + expire_seconds
        elif not entry or entry.is_expired() or not isinstance(entry.value, set):
            # Якщо це новий запис (або перезапис неправильного типу/простроченого) і expire_seconds не надано,
            # то new_expire_at залишиться None (безстроковий кеш).
            pass

        # Оновлюємо кеш, якщо:
        # 1. Були фактично додані нові елементи.
        # 2. Або запис був новий (not entry).
        # 3. Або існуючий запис був прострочений або мав неправильний тип.
        # 4. Або TTL був змінений (new_expire_at відрізняється від existing_expire_at, навіть якщо added_count = 0).
        ttl_changed = (expire_seconds is not None and new_expire_at != existing_expire_at)

        if added_count > 0 or not entry or (entry and (entry.is_expired() or not isinstance(entry.value, set))) or ttl_changed :
            self._cache[key] = _CacheEntry(current_set, new_expire_at)
            log_action = "оновлено/створено" if added_count > 0 or ttl_changed else "перезаписано (тип/прострочення)"
        else:
            log_action = "не змінено (елементи вже існували, TTL не вказано)"

        logger.debug(
            f"Кеш SADD: ключ='{key}', {added_count} нових значень додано. Множину {log_action}. "
            f"Поточний розмір: {len(current_set)}. TTL (монотонний): {new_expire_at}")
        return added_count

    async def set_get_all(self, key: str) -> Set[Any]:
        """Повертає всі елементи множини."""
        entry_value = await self.get(key)  # get вже обробляє прострочення
        if isinstance(entry_value, set):
            logger.debug(f"Кеш SMEMBERS: ключ='{key}', отримано {len(entry_value)} елементів.")
            return entry_value
        if entry_value is not None:  # Якщо ключ існує, але не є множиною
            logger.warning(
                f"Кеш SMEMBERS: ключ '{key}' існує, але не є множиною (тип: {type(entry_value)}). Повернення порожньої множини.")
        return set()

    async def set_remove(self, key: str, *values: Any) -> int:
        """Видаляє елементи з множини."""
        entry = self._cache.get(key)
        removed_count = 0
        if entry and not entry.is_expired() and isinstance(entry.value, set):
            current_set: Set[Any] = entry.value
            for v_item in values:
                if v_item in current_set:
                    current_set.remove(v_item)
                    removed_count += 1
            if removed_count > 0:  # Зберігаємо зміни, якщо щось було видалено
                self._cache[key] = _CacheEntry(current_set, entry.expire_at)
            logger.debug(
                f"Кеш SREM: ключ='{key}', {removed_count} значень видалено. Поточний розмір: {len(current_set)}.")
        else:
            if not entry or entry.is_expired():
                logger.debug(f"Кеш SREM: ключ='{key}' не знайдено або прострочено.")
            elif not isinstance(entry.value, set):
                logger.warning(f"Кеш SREM: ключ '{key}' існує, але не є множиною (тип: {type(entry.value)}).")
        return removed_count

    async def set_is_member(self, key: str, value: Any) -> bool:
        """Перевіряє, чи є елемент членом множини."""
        entry_value = await self.get(key)  # get обробляє прострочення
        if isinstance(entry_value, set):
            is_member = value in entry_value
            logger.debug(f"Кеш SISMEMBER: ключ='{key}', значення='{value}', є членом: {is_member}.")
            return is_member
        # Якщо ключ не існує, прострочений, або не є множиною
        logger.debug(
            f"Кеш SISMEMBER: ключ='{key}' не знайдено, прострочено, або не є множиною. Значення='{value}' не є членом.")
        return False


logger.info("InMemoryCacheService (кеш в пам'яті) клас визначено.")
