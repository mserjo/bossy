# backend/app/src/services/cache/base_cache.py
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any, Set # Added Set for potential return type like smembers

# Initialize logger for this module
logger = logging.getLogger(__name__)

class BaseCacheService(ABC):
    """
    Abstract Base Class for cache services.
    Defines a common interface for interacting with different cache backends
    like Redis, Memcached, or an in-memory cache.

    Concrete implementations will provide the actual caching logic.
    This class itself does not inherit from BaseService as it typically
    doesn't directly need a database session for its core caching operations.
    Connection details for cache backends (like Redis URL) should come from settings.
    """

    # service_name: str # To be defined by concrete class if needed for specific config lookup

    def __init__(self): # Constructor might take specific cache client or config
        logger.info(f"BaseCacheService (subclass: {self.__class__.__name__}) initialized.")

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieves an item from the cache by key.

        Args:
            key (str): The key of the item to retrieve.

        Returns:
            Optional[Any]: The cached value if found and not expired, otherwise None.
                           The value will likely be deserialized from a string (e.g., JSON).
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """
        Stores an item in the cache.

        Args:
            key (str): The key under which to store the value.
            value (Any): The value to store. It will likely be serialized (e.g., to JSON string).
            expire_seconds (Optional[int]): Time in seconds until the item expires.
                                           If None, uses default expiry or persists indefinitely (backend-dependent).

        Returns:
            bool: True if the item was successfully set, False otherwise.
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Removes an item from the cache by key.

        Args:
            key (str): The key of the item to delete.

        Returns:
            bool: True if the item was deleted or did not exist, False on error.
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Checks if a key exists in the cache.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        pass

    @abstractmethod
    async def clear_all_prefix(self, prefix: str) -> int:
        """
        Removes all cache entries whose keys start with the given prefix.
        Warning: This can be a slow operation on some backends like Redis if not using SCAN.

        Args:
            prefix (str): The prefix for keys to delete (e.g., "user_session:").

        Returns:
            int: The number of keys deleted.
        """
        pass

    @abstractmethod
    async def clear_all(self) -> bool:
        """
        Clears the entire cache (all keys). Use with extreme caution, especially in production.

        Returns:
            bool: True if the cache was successfully cleared, False otherwise.
        """
        pass

    # --- Optional common utility methods for specific cache types ---

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increments the integer value of a key by a given amount.
        If key does not exist, it's set to 0 before performing the operation.
        Returns the value of key after the increment.
        Not all cache backends might support this atomically.
        Base implementation returns None and logs a warning.
        """
        logger.warning(f"Increment method not implemented for {self.__class__.__name__} by default.")
        return None

    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Decrements the integer value of a key by a given amount.
        If key does not exist, it's set to 0 before performing the operation.
        Returns the value of key after the decrement.
        Base implementation returns None and logs a warning.
        """
        logger.warning(f"Decrement method not implemented for {self.__class__.__name__} by default.")
        return None

    # Example methods for set operations (if backend supports, e.g., Redis SADD, SMEMBERS)
    # async def set_add(self, key: str, *values: Any) -> int:
    #     logger.warning(f"set_add method not implemented for {self.__class__.__name__} by default.")
    #     return 0 # Or raise NotImplementedError

    # async def set_get_all(self, key: str) -> Set[Any]:
    #     logger.warning(f"set_get_all method not implemented for {self.__class__.__name__} by default.")
    #     return set() # Or raise NotImplementedError

    # async def set_remove(self, key: str, *values: Any) -> int:
    #     logger.warning(f"set_remove method not implemented for {self.__class__.__name__} by default.")
    #     return 0 # Or raise NotImplementedError

    # async def set_is_member(self, key: str, value: Any) -> bool:
    #     logger.warning(f"set_is_member method not implemented for {self.__class__.__name__} by default.")
    #     return False # Or raise NotImplementedError

logger.info("BaseCacheService (ABC) defined.")
