import redis.asyncio as aioredis
from typing import Optional, AsyncGenerator

from backend.app.src.config.settings import settings

# Global variable to hold the Redis client instance
# This allows for the client to be initialized once and reused.
_redis_client: Optional[aioredis.Redis] = None

async def get_redis_client() -> aioredis.Redis:
    """
    Provides an asynchronous Redis client instance.

    This function initializes the Redis client if it hasn't been already,
    using the REDIS_URL from the application settings.
    It's designed to be used as a dependency in FastAPI or other parts of the application
    that require Redis access.

    Returns:
        aioredis.Redis: An initialized asynchronous Redis client.

    Raises:
        ConnectionError: If the Redis client cannot be initialized or connect to the server.
    """
    global _redis_client
    if _redis_client is None:
        try:
            # Create a Redis client instance from the URL in settings
            # The from_url method handles parsing the DSN and configuring the client.
            _redis_client = aioredis.from_url(
                str(settings.REDIS_URL), # Ensure REDIS_URL is a string
                encoding="utf-8",
                decode_responses=True # Automatically decode responses from bytes to strings
            )
            # Test the connection
            await _redis_client.ping()
            print(f"Successfully connected to Redis at {settings.REDIS_URL}")
        except Exception as e:
            # Log the error or handle it as appropriate for your application
            print(f"Error connecting to Redis: {e}")
            # Depending on the application's needs, you might want to raise an error
            # or allow the app to continue without Redis (e.g., with caching disabled).
            # For now, we'll raise a ConnectionError to make it explicit.
            _redis_client = None # Ensure client is None if connection failed
            raise ConnectionError(f"Could not connect to Redis: {e}")
    return _redis_client

async def close_redis_client():
    """
    Closes the Redis client connection if it has been initialized.
    This is useful for graceful shutdowns of the application.
    """
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None # Reset the global client variable
        print("Redis connection closed.")

# --- Optional: FastAPI dependency wrapper ---
async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    FastAPI dependency that provides a Redis client for a single request.
    This is an alternative to using a global client directly if you prefer
    managing Redis client lifecycle per request or with a connection pool per request.

    However, for many use cases, a single global client (`get_redis_client`) is sufficient
    and more performant due to connection reuse.

    Yields:
        aioredis.Redis: An asynchronous Redis client.
    """
    client = await get_redis_client() # Reuses the global client logic
    try:
        yield client
    finally:
        # Typically, you don't close the client obtained from get_redis_client() here
        # if it's meant to be a long-lived global client. Connection closing is handled
        # by `close_redis_client()` during application shutdown.
        pass

if __name__ == "__main__":
    import asyncio

    async def main():
        print("Attempting to connect to Redis...")
        try:
            redis_client = await get_redis_client()
            print(f"Redis client obtained: {redis_client}")

            # Example usage:
            await redis_client.set("mykey", "Hello from Redis!")
            value = await redis_client.get("mykey")
            print(f"Retrieved value from Redis: {value}")
            await redis_client.delete("mykey")
            print("Cleaned up test key.")

        except ConnectionError as e:
            print(f"Failed to connect or use Redis: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            await close_redis_client()

    asyncio.run(main())
