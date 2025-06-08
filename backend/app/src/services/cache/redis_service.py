# backend/app/src/services/cache/redis_service.py
import logging
import json # For serializing/deserializing complex data types to store in Redis
from typing import Optional, Any, Set, Union, List
from decimal import Decimal # For handling Decimal type if stored and retrieved

import redis.asyncio as aioredis # Using redis-py's async capabilities

from app.src.services.cache.base_cache import BaseCacheService
from app.src.config.redis import get_redis_pool # Assuming a get_redis_pool for connection pooling
# from app.src.config.settings import settings # If specific Redis settings are needed directly

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Helper for serialization/deserialization
def _serialize_value(value: Any) -> str:
    if isinstance(value, str): # Keep string as is, no extra quotes
        return value
    if isinstance(value, (int, float)): # bool is instance of int
        return str(value)
    if isinstance(value, bool): # Explicit bool check
        return "true" if value else "false"
    if isinstance(value, Decimal):
        return f"decimal:{str(value)}"
    try:
        return f"json:{json.dumps(value)}"
    except TypeError as e:
        logger.warning(f"Could not JSON serialize value of type {type(value)}. Storing as string. Error: {e}")
        return str(value)

def _deserialize_value(value_str: Optional[str]) -> Any:
    if value_str is None:
        return None
    if value_str.startswith("json:"):
        try:
            return json.loads(value_str[len("json:"):])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to JSON deserialize value '{value_str[:50]}...': {e}. Returning raw string part.")
            return value_str[len("json:"):]
    if value_str.startswith("decimal:"):
        try:
            return Decimal(value_str[len("decimal:"):])
        except Exception as e:
            logger.error(f"Failed to deserialize Decimal value '{value_str}': {e}. Returning None.")
            return None

    # Check for boolean strings after prefixes
    if value_str.lower() == 'true': return True
    if value_str.lower() == 'false': return False

    try: return int(value_str)
    except ValueError: pass
    try: return float(value_str)
    except ValueError: pass

    return value_str


class RedisCacheService(BaseCacheService):
    """
    Concrete implementation of BaseCacheService using Redis as the backend.
    Handles connection to Redis, serialization/deserialization, and cache operations.
    """
    # service_name = "REDIS_CACHE" # Optional: if needed for specific config lookup

    def __init__(self):
        super().__init__()
        self._redis_client: Optional[aioredis.Redis] = None
        self._initialize_client()

    def _initialize_client(self):
        """Initializes the Redis client using the global pool."""
        try:
            redis_pool = get_redis_pool()
            if redis_pool:
                self._redis_client = aioredis.Redis(connection_pool=redis_pool)
                logger.info("RedisCacheService client initialized using connection pool.")
            else:
                logger.error("Failed to get Redis connection pool. RedisCacheService will be non-functional.")
                self._redis_client = None
        except Exception as e:
            logger.error(f"Error initializing Redis client: {e}", exc_info=True)
            self._redis_client = None


    async def _get_client(self) -> aioredis.Redis:
        """Ensures Redis client is available, raising an error if not."""
        if not self._redis_client:
            logger.error("Redis client not available. Attempting to re-initialize.")
            self._initialize_client()
            if not self._redis_client:
                 raise ConnectionError("Redis client is not initialized or connection failed.")
        return self._redis_client

    async def get(self, key: str) -> Optional[Any]:
        client = await self._get_client()
        try:
            value_bytes = await client.get(key)
            if value_bytes is not None:
                value_str = value_bytes.decode('utf-8')
                deserialized_value = _deserialize_value(value_str)
                logger.debug(f"Cache GET: key='{key}', value='{str(deserialized_value)[:100]}...' (type: {type(deserialized_value)})")
                return deserialized_value
            logger.debug(f"Cache GET: key='{key}' not found.")
            return None
        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}", exc_info=True)
            return None

    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        client = await self._get_client()
        serialized_value = _serialize_value(value)
        try:
            result = await client.set(name=key, value=serialized_value, ex=expire_seconds)
            logger.debug(f"Cache SET: key='{key}', value='{serialized_value[:100]}...', expire_seconds={expire_seconds}. Result: {result}")
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}", exc_info=True)
            return False

    async def delete(self, key: str) -> bool:
        client = await self._get_client()
        try:
            num_deleted = await client.delete(key)
            logger.debug(f"Cache DELETE: key='{key}'. Num deleted: {num_deleted}")
            return num_deleted >= 0
        except Exception as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}", exc_info=True)
            return False

    async def exists(self, key: str) -> bool:
        client = await self._get_client()
        try:
            exists_result = await client.exists(key)
            logger.debug(f"Cache EXISTS: key='{key}'. Result: {exists_result > 0}")
            return exists_result > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}", exc_info=True)
            return False

    async def clear_all_prefix(self, prefix: str) -> int:
        client = await self._get_client()
        if not prefix.endswith('*'):
            prefix_pattern = f"{prefix}*"
        else:
            prefix_pattern = prefix

        logger.warning(f"Cache CLEAR_ALL_PREFIX: Attempting to delete keys matching pattern '{prefix_pattern}'. This can be slow.")
        deleted_count = 0
        try:
            cursor = b'0' # SSCAN cursor starts as bytes
            while cursor != b'0': # Loop until cursor is 0 again
                cursor, keys_bytes = await client.scan(cursor=cursor, match=prefix_pattern, count=1000)
                if keys_bytes:
                    # Convert keys from bytes to str for logging and consistency, though delete takes bytes too
                    keys_str = [k.decode('utf-8') for k in keys_bytes]
                    num_deleted_batch = await client.delete(*keys_str)
                    deleted_count += num_deleted_batch
                    logger.debug(f"Deleted batch of {num_deleted_batch} keys matching '{prefix_pattern}'. Total deleted so far: {deleted_count}.")
                if cursor == b'0': # Break after processing the last batch
                    break
            logger.info(f"Cache CLEAR_ALL_PREFIX: Deleted {deleted_count} keys matching pattern '{prefix_pattern}'.")
            return deleted_count
        except Exception as e:
            logger.error(f"Redis SCAN/DELETE error for prefix '{prefix_pattern}': {e}", exc_info=True)
            return deleted_count

    async def clear_all(self) -> bool:
        client = await self._get_client()
        logger.warning("Cache CLEAR_ALL: Attempting to flush entire Redis database. This is destructive.")
        try:
            await client.flushdb()
            logger.info("Cache CLEAR_ALL: Successfully flushed current Redis database.")
            return True
        except Exception as e:
            logger.error(f"Redis FLUSHDB error: {e}", exc_info=True)
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        client = await self._get_client()
        try:
            new_value = await client.incrby(name=key, amount=amount)
            logger.debug(f"Cache INCREMENT: key='{key}', amount={amount}. New value: {new_value}")
            return int(new_value)
        except Exception as e:
            logger.error(f"Redis INCRBY error for key '{key}': {e}", exc_info=True)
            return None

    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        client = await self._get_client()
        try:
            new_value = await client.decrby(name=key, amount=amount)
            logger.debug(f"Cache DECREMENT: key='{key}', amount={amount}. New value: {new_value}")
            return int(new_value)
        except Exception as e:
            logger.error(f"Redis DECRBY error for key '{key}': {e}", exc_info=True)
            return None

    async def set_add(self, key: str, *values: Any) -> int:
        client = await self._get_client()
        if not values: return 0
        serialized_values = [_serialize_value(v) for v in values]
        try:
            num_added = await client.sadd(key, *serialized_values)
            logger.debug(f"Cache SADD: key='{key}', values added: {num_added} from {len(values)} provided.")
            return num_added
        except Exception as e:
            logger.error(f"Redis SADD error for key '{key}': {e}", exc_info=True)
            return 0

    async def set_get_all(self, key: str) -> Set[Any]:
        client = await self._get_client()
        try:
            members_bytes = await client.smembers(key)
            deserialized_members = {_deserialize_value(m.decode('utf-8')) for m in members_bytes}
            logger.debug(f"Cache SMEMBERS: key='{key}', retrieved {len(deserialized_members)} members.")
            return deserialized_members
        except Exception as e:
            logger.error(f"Redis SMEMBERS error for key '{key}': {e}", exc_info=True)
            return set()

logger.info("RedisCacheService class defined.")
