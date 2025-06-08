# backend/app/src/services/cache/memory_service.py
import logging
import time # For handling expiration
from typing import Optional, Any, Dict, Set, Tuple, Union
from datetime import datetime, timedelta, timezone # For precise expiry

from app.src.services.cache.base_cache import BaseCacheService

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Internal class to store cache entries with expiry information
class _CacheEntry:
    def __init__(self, value: Any, expire_at: Optional[float] = None): # expire_at is Unix timestamp from time.monotonic()
        self.value = value
        self.expire_at = expire_at

    def is_expired(self) -> bool:
        if self.expire_at is None:
            return False # Never expires
        return time.monotonic() >= self.expire_at

class InMemoryCacheService(BaseCacheService):
    """
    Concrete implementation of BaseCacheService using a simple Python dictionary
    for in-memory caching. Handles item expiration.
    Suitable for development, testing, or small-scale single-process deployments.
    Not suitable for multi-process or distributed environments as cache is local to process.
    """
    # service_name = "IN_MEMORY_CACHE" # Optional

    def __init__(self):
        super().__init__()
        self._cache: Dict[str, _CacheEntry] = {}
        logger.info("InMemoryCacheService initialized.")

    async def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry:
            if entry.is_expired():
                logger.debug(f"Cache GET: key='{key}' found but expired. Deleting.")
                await self.delete(key)
                return None
            logger.debug(f"Cache GET: key='{key}', value='{str(entry.value)[:100]}...' (type: {type(entry.value)})")
            return entry.value
        logger.debug(f"Cache GET: key='{key}' not found.")
        return None

    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        expire_at: Optional[float] = None
        if expire_seconds is not None:
            if expire_seconds <= 0:
                logger.debug(f"Cache SET: key='{key}' with non-positive expire_seconds ({expire_seconds}). Deleting if exists.")
                return await self.delete(key)
            expire_at = time.monotonic() + expire_seconds

        self._cache[key] = _CacheEntry(value, expire_at)
        # For logging expiry time in a human-readable way, convert monotonic back to datetime (approximate)
        # This is mainly for debugging as monotonic time itself isn't a wall clock time.
        log_expire_str = "None"
        if expire_at is not None:
            # Calculate a rough datetime for logging based on current wall clock + remaining duration
            # This is not perfect as time.monotonic() and time.time() can drift, but gives an idea.
            current_monotonic = time.monotonic()
            remaining_seconds = expire_at - current_monotonic
            if remaining_seconds > 0:
                 log_expire_dt = datetime.now(timezone.utc) + timedelta(seconds=remaining_seconds)
                 log_expire_str = log_expire_dt.isoformat()
            else: # Already expired or very close
                 log_expire_str = "Past (or immediately)"


        logger.debug(f"Cache SET: key='{key}', value='{str(value)[:100]}...', expire_at (monotonic): {expire_at}, approx_utc_expiry: {log_expire_str}")
        return True

    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache DELETE: key='{key}' deleted.")
            return True
        logger.debug(f"Cache DELETE: key='{key}' not found, no action taken.")
        return True

    async def exists(self, key: str) -> bool:
        entry = self._cache.get(key)
        if entry:
            if not entry.is_expired():
                logger.debug(f"Cache EXISTS: key='{key}' found and not expired.")
                return True
            else: # Key exists but is expired
                logger.debug(f"Cache EXISTS: key='{key}' found but TTL expired. Cleaning up.")
                await self.delete(key) # Proactive cleanup
        logger.debug(f"Cache EXISTS: key='{key}' not found or was expired and cleaned.")
        return False

    async def clear_all_prefix(self, prefix: str) -> int:
        logger.info(f"Cache CLEAR_ALL_PREFIX: Attempting to delete keys matching prefix '{prefix}'.")
        # Iterate over a copy of keys if modifying dict during iteration (though delete handles it)
        keys_to_delete = [key for key in list(self._cache.keys()) if key.startswith(prefix)]

        deleted_count = 0
        for key in keys_to_delete:
            # self.delete() already checks for existence and handles expiry.
            # If it returns True (meaning key was either deleted or didn't exist), we can count it.
            # However, to count only *actually deleted* items by *this operation*:
            if key in self._cache: # Check if it's still there (might have expired and been cleaned by another call)
                 entry = self._cache.get(key)
                 if entry and not entry.is_expired(): # Only count if it was active before this delete call
                     if await self.delete(key): # This will delete it
                         deleted_count +=1
                 elif entry and entry.is_expired(): # It existed but was expired, delete it anyway
                     await self.delete(key) # Cleanup, but don't count as deleted by *this* prefix clear if already expired

        if deleted_count > 0 :
             logger.info(f"Cache CLEAR_ALL_PREFIX: Actively deleted {deleted_count} keys matching prefix '{prefix}'.")
        else:
             logger.info(f"Cache CLEAR_ALL_PREFIX: No active keys found matching prefix '{prefix}' to delete.")
        return deleted_count


    async def clear_all(self) -> bool:
        logger.warning("Cache CLEAR_ALL: Clearing entire in-memory cache.")
        self._cache.clear()
        logger.info("Cache CLEAR_ALL: In-memory cache successfully cleared.")
        return True

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        current_entry = self._cache.get(key)
        current_value = 0
        original_expire_at: Optional[float] = None

        if current_entry:
            if current_entry.is_expired():
                logger.debug(f"Cache INCREMENT: key='{key}' was expired. Treating as new.")
                # await self.delete(key) # delete is implicit as we overwrite
            elif isinstance(current_entry.value, int):
                current_value = current_entry.value
                original_expire_at = current_entry.expire_at # Preserve expiry
            else:
                logger.error(f"InMemoryCache INCREMENT error for key '{key}': existing value is not an integer (type: {type(current_entry.value)}). Cannot increment.")
                return None

        new_value = current_value + amount
        self._cache[key] = _CacheEntry(new_value, original_expire_at) # Use original_expire_at or None if new/expired

        logger.debug(f"Cache INCREMENT: key='{key}', amount={amount}. New value: {new_value}")
        return new_value

    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        current_entry = self._cache.get(key)
        current_value = 0
        original_expire_at: Optional[float] = None

        if current_entry:
            if current_entry.is_expired():
                logger.debug(f"Cache DECREMENT: key='{key}' was expired. Treating as new.")
            elif isinstance(current_entry.value, int):
                current_value = current_entry.value
                original_expire_at = current_entry.expire_at
            else:
                logger.error(f"InMemoryCache DECREMENT error for key '{key}': existing value is not an integer (type: {type(current_entry.value)}). Cannot decrement.")
                return None

        new_value = current_value - amount
        self._cache[key] = _CacheEntry(new_value, original_expire_at)

        logger.debug(f"Cache DECREMENT: key='{key}', amount={amount}. New value: {new_value}")
        return new_value

    async def set_add(self, key: str, *values: Any) -> int:
        entry = self._cache.get(key)
        current_set: Set[Any] = set()
        expire_at: Optional[float] = None # Default for new set

        if entry and not entry.is_expired():
            if isinstance(entry.value, set):
                current_set = entry.value
                expire_at = entry.expire_at
            else:
                logger.warning(f"InMemoryCache SADD: key '{key}' exists but is not a set (type: {type(entry.value)}). Overwriting with new set.")

        added_count = 0
        for v_item in values: # Changed v to v_item to avoid conflict with value from _CacheEntry
            if v_item not in current_set:
                current_set.add(v_item)
                added_count += 1

        if added_count > 0 or not entry or (entry and entry.is_expired()): # Only update cache if new items added or if entry was new/expired
            self._cache[key] = _CacheEntry(current_set, expire_at)
        logger.debug(f"Cache SADD: key='{key}', {added_count} new values added. Current size: {len(current_set)}.")
        return added_count

    async def set_get_all(self, key: str) -> Set[Any]:
        # self.get() already handles expiration and returns the value or None
        entry_value = await self.get(key)
        if isinstance(entry_value, set):
            logger.debug(f"Cache SMEMBERS: key='{key}', retrieved {len(entry_value)} members.")
            return entry_value
        if entry_value is not None:
            logger.warning(f"InMemoryCache SMEMBERS: key '{key}' exists but is not a set (type: {type(entry_value)}). Returning empty set.")
        # else: logger.debug(f"Cache SMEMBERS: key='{key}' not found or expired. Returning empty set.") # get() logs this
        return set()

logger.info("InMemoryCacheService class defined.")
