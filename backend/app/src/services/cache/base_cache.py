# backend/app/src/services/cache/base_cache.py
from abc import ABC, abstractmethod
from typing import Optional, Any # Set видалено, оскільки використовується лише в коментарях

from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class BaseCacheService(ABC):
    """
    Абстрактний базовий клас для сервісів кешування.
    Визначає спільний інтерфейс для взаємодії з різними бекендами кешу,
    такими як Redis, Memcached або кеш в пам'яті.

    Конкретні реалізації надаватимуть фактичну логіку кешування.
    Цей клас сам по собі не успадковує BaseService, оскільки зазвичай
    не потребує прямого доступу до сесії бази даних для своїх основних операцій кешування.
    Деталі підключення до бекендів кешу (наприклад, URL Redis) повинні надходити з налаштувань.
    """

    # service_name: str # Може бути визначено конкретним класом, якщо потрібно для специфічного пошуку конфігурації

    def __init__(self): # Конструктор може приймати специфічний клієнт кешу або конфігурацію
        logger.info(f"BaseCacheService (підклас: {self.__class__.__name__}) ініціалізовано.")

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Отримує елемент з кешу за ключем.

        :param key: Ключ елемента для отримання.
        :return: Значення з кешу, якщо знайдено і не прострочено, інакше None.
                 Значення, ймовірно, буде десеріалізовано з рядка (наприклад, JSON).
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """
        Зберігає елемент в кеші.

        :param key: Ключ, за яким зберігається значення.
        :param value: Значення для зберігання. Ймовірно, буде серіалізовано (наприклад, у JSON рядок).
        :param expire_seconds: Час у секундах до закінчення терміну дії елемента.
                               Якщо None, використовується стандартний термін дії або зберігається безстроково (залежить від бекенду).
        :return: True, якщо елемент успішно встановлено, інакше False.
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Видаляє елемент з кешу за ключем.

        :param key: Ключ елемента для видалення.
        :return: True, якщо елемент було видалено або він не існував, False у разі помилки.
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Перевіряє, чи існує ключ в кеші.

        :param key: Ключ для перевірки.
        :return: True, якщо ключ існує, інакше False.
        """
        pass

    @abstractmethod
    async def clear_all_prefix(self, prefix: str) -> int:
        """
        Видаляє всі записи кешу, ключі яких починаються з заданого префіксу.
        Увага: Це може бути повільною операцією на деяких бекендах, таких як Redis, якщо не використовувати SCAN.

        :param prefix: Префікс для ключів, що підлягають видаленню (наприклад, "user_session:").
        :return: Кількість видалених ключів.
        """
        pass

    @abstractmethod
    async def clear_all(self) -> bool:
        """
        Очищає весь кеш (всі ключі). Використовувати з особливою обережністю, особливо в робочому середовищі.

        :return: True, якщо кеш успішно очищено, інакше False.
        """
        pass

    # --- Опціональні загальні утилітні методи для специфічних типів кешу ---

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Збільшує цілочисельне значення ключа на задану величину.
        Якщо ключ не існує, він встановлюється в 0 перед виконанням операції.
        Повертає значення ключа після інкременту.
        Не всі бекенди кешу можуть підтримувати цю операцію атомарно.
        Базова реалізація повертає None та логує попередження.

        :param key: Ключ для інкременту.
        :param amount: Величина, на яку збільшити значення.
        :return: Значення після інкременту або None, якщо не реалізовано.
        """
        logger.warning(f"Метод 'increment' не реалізований для {self.__class__.__name__} за замовчуванням.")
        return None

    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Зменшує цілочисельне значення ключа на задану величину.
        Якщо ключ не існує, він встановлюється в 0 перед виконанням операції.
        Повертає значення ключа після декременту.
        Базова реалізація повертає None та логує попередження.

        :param key: Ключ для декременту.
        :param amount: Величина, на яку зменшити значення.
        :return: Значення після декременту або None, якщо не реалізовано.
        """
        logger.warning(f"Метод 'decrement' не реалізований для {self.__class__.__name__} за замовчуванням.")
        return None

    # --- Приклади методів для операцій з множинами (якщо бекенд підтримує, наприклад, Redis SADD, SMEMBERS) ---
    # (Закоментовано, оскільки це специфічно для певних бекендів і не є частиною базового інтерфейсу)

    # async def set_add(self, key: str, *values: Any, expire_seconds: Optional[int] = None) -> int:
    #     """Додає один або більше елементів до множини, що зберігається за ключем. Опціонально встановлює TTL."""
    #     logger.warning(f"Метод 'set_add' не реалізований для {self.__class__.__name__} за замовчуванням.")
    #     return 0 # Або викликати NotImplementedError

    # async def set_get_all(self, key: str) -> Set[Any]:
    #     """Повертає всі елементи множини, що зберігається за ключем."""
    #     logger.warning(f"Метод 'set_get_all' не реалізований для {self.__class__.__name__} за замовчуванням.")
    #     return set() # Або викликати NotImplementedError

    # async def set_remove(self, key: str, *values: Any) -> int:
    #     """Видаляє один або більше елементів з множини, що зберігається за ключем."""
    #     logger.warning(f"Метод 'set_remove' не реалізований для {self.__class__.__name__} за замовчуванням.")
    #     return 0 # Або викликати NotImplementedError

    # async def set_is_member(self, key: str, value: Any) -> bool:
    #     """Перевіряє, чи є елемент членом множини, що зберігається за ключем."""
    #     logger.warning(f"Метод 'set_is_member' не реалізований для {self.__class__.__name__} за замовчуванням.")
    #     return False # Або викликати NotImplementedError

logger.info("BaseCacheService (ABC) визначено.")
