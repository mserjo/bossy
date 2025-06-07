# backend/app/src/services/system/health.py
import logging
import time # For measuring response times
from typing import List, Dict, Any, Literal, Optional # Added Optional for _check_redis_health
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text # For executing raw SQL like 'SELECT 1'

from app.src.services.base import BaseService
from app.src.schemas.system.health import ( # Pydantic schemas
    HealthCheckResponse,
    ComponentHealth,
    HealthStatusEnum # Assuming an Enum or Literal for status
)
# from app.src.config.redis import get_redis_client # Example for Redis check
# import httpx # Example for checking external HTTP services

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Use HealthStatusEnum if defined, otherwise fallback to Literal
try:
    # This ensures that if HealthStatusEnum is not available, the Literal is used.
    # However, for Pydantic schema generation, it's best if HealthStatusEnum is properly defined
    # in app.src.schemas.system.health and imported.
    # If HealthStatusEnum is `Literal["healthy", "unhealthy", "degraded"]`, this works.
    if HealthStatusEnum:
        ComponentStatusType = HealthStatusEnum
    else: # Fallback if HealthStatusEnum is None or not an actual Enum/Literal type
        ComponentStatusType = Literal["healthy", "unhealthy", "degraded"]
except NameError: # HealthStatusEnum not imported or defined
    ComponentStatusType = Literal["healthy", "unhealthy", "degraded"]


class HealthCheckService(BaseService):
    """
    Service for performing system health checks on various components
    like database, cache, and other dependent services.
    """

    def __init__(self, db_session: AsyncSession): # Add other clients like redis_client if needed
        super().__init__(db_session)
        # self.redis_client = get_redis_client() # Example: Initialize Redis client
        logger.info("HealthCheckService initialized.")

    async def _check_database_health(self) -> ComponentHealth:
        """
        Checks the health of the primary database.
        Attempts to execute a simple query.
        """
        component_name = "database"
        start_time = time.perf_counter()
        status: ComponentStatusType = HealthStatusEnum.HEALTHY # Default to healthy
        message = "Database connection successful."
        details: Dict[str, Any] = {}

        try:
            # Execute a simple query to check DB connectivity
            result = await self.db_session.execute(text("SELECT 1"))
            if result.scalar_one() != 1:
                raise Exception("Database health check query failed to return 1.")
            # You could also check specific tables or migrations status here if needed
            # details["migrations_status"] = "up-to-date" # Example
        except Exception as e:
            logger.error(f"Database health check failed: {e}", exc_info=True)
            status = HealthStatusEnum.UNHEALTHY
            message = f"Database connection error: {str(e)}"

        duration_ms = (time.perf_counter() - start_time) * 1000
        details["response_time_ms"] = round(duration_ms, 2)

        return ComponentHealth(
            component_name=component_name,
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow()
        )

    async def _check_redis_health(self) -> Optional[ComponentHealth]:
        """
        Checks the health of the Redis cache (example).
        This requires a Redis client to be available.
        """
        # This is an example, actual implementation depends on having a Redis client.
        # if not self.redis_client:
        #     logger.info("Redis client not configured, skipping Redis health check.")
        #     return None

        component_name = "redis_cache"
        start_time = time.perf_counter()
        # status: ComponentStatusType = HealthStatusEnum.HEALTHY # Commented out as it's a placeholder
        # message = "Redis connection successful and PING responded." # Commented out
        details: Dict[str, Any] = {}

        # try:
        #     if not await self.redis_client.ping():
        #         raise Exception("Redis PING command failed.")
        #     # Optionally, check some key or stats
        #     # info = await self.redis_client.info()
        #     # details["redis_version"] = info.get("redis_version")
        # except Exception as e:
        #     logger.error(f"Redis health check failed: {e}", exc_info=True)
        #     status = HealthStatusEnum.UNHEALTHY
        #     message = f"Redis connection error: {str(e)}"

        duration_ms = (time.perf_counter() - start_time) * 1000
        details["response_time_ms"] = round(duration_ms, 2)

        # Return a placeholder if Redis client is not implemented for real
        logger.warning("Redis health check is a placeholder as Redis client is not fully implemented in this example.")
        return ComponentHealth(
            component_name=component_name,
            status=HealthStatusEnum.DEGRADED, # Mark as degraded if it's just a placeholder
            message="Redis health check not fully implemented (placeholder).",
            details=details,
            timestamp=datetime.utcnow()
        )


    async def _check_external_api_health(self, api_name: str, api_url: str) -> ComponentHealth:
        """
        Checks the health of an external HTTP API dependency (example).
        """
        component_name = f"external_api:{api_name}"
        start_time = time.perf_counter()
        # status: ComponentStatusType = HealthStatusEnum.HEALTHY # Commented out as it's a placeholder
        # message = f"Connection to {api_name} API successful." # Commented out
        details: Dict[str, Any] = {"url": api_url}

        # try:
        #     async with httpx.AsyncClient(timeout=5.0) as client: # 5 second timeout
        #         response = await client.get(api_url) # Or a specific health endpoint
        #         response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
        #         # Optionally, check response content if it's a dedicated health endpoint
        #         # health_data = response.json()
        #         # if health_data.get("status") != "ok":
        #         #    raise Exception(f"{api_name} reported unhealthy status: {health_data.get('status')}")
        # except httpx.RequestError as e: # Covers network errors, DNS failures, timeouts
        #     logger.error(f"External API health check for {api_name} failed (RequestError): {e}", exc_info=True)
        #     status = HealthStatusEnum.UNHEALTHY
        #     message = f"Error connecting to {api_name} API: {str(e)}"
        # except httpx.HTTPStatusError as e: # Covers HTTP error responses
        #     logger.error(f"External API health check for {api_name} failed (HTTPStatusError {e.response.status_code}): {e}", exc_info=True)
        #     status = HealthStatusEnum.UNHEALTHY
        #     message = f"{api_name} API returned status {e.response.status_code}."
        #     details["status_code"] = e.response.status_code
        # except Exception as e:
        #     logger.error(f"External API health check for {api_name} failed (General Exception): {e}", exc_info=True)
        #     status = HealthStatusEnum.UNHEALTHY
        #     message = f"An unexpected error occurred while checking {api_name} API: {str(e)}"

        duration_ms = (time.perf_counter() - start_time) * 1000
        details["response_time_ms"] = round(duration_ms, 2)

        # Return a placeholder if httpx is not used for real
        logger.warning(f"External API health check for {api_name} is a placeholder as httpx is not fully implemented in this example.")
        return ComponentHealth(
            component_name=component_name,
            status=HealthStatusEnum.DEGRADED, # Mark as degraded if it's just a placeholder
            message=f"External API check for {api_name} not fully implemented (placeholder).",
            details=details,
            timestamp=datetime.utcnow()
        )

    async def perform_full_health_check(self) -> HealthCheckResponse:
        """
        Performs a comprehensive health check of all critical system components.
        Aggregates individual component health statuses.
        """
        logger.info("Performing full system health check...")
        components_health: List[ComponentHealth] = []

        # Database health
        db_health = await self._check_database_health()
        components_health.append(db_health)

        # Redis health (example, enable if Redis is used)
        redis_health = await self._check_redis_health()
        if redis_health: # It might return None if not configured
             components_health.append(redis_health)

        # Example: External API check (if any critical external dependencies)
        # For demonstration, let's add one placeholder external API check
        external_example_api_health = await self._check_external_api_health(
            api_name="ExampleService",
            api_url="https://api.example.com/health" # Replace with actual URL
        )
        components_health.append(external_example_api_health)

        # Determine overall system status
        overall_status: ComponentStatusType = HealthStatusEnum.HEALTHY
        for component in components_health:
            if component.status == HealthStatusEnum.UNHEALTHY:
                overall_status = HealthStatusEnum.UNHEALTHY
                break # If one is unhealthy, the whole system is unhealthy
            if component.status == HealthStatusEnum.DEGRADED and overall_status == HealthStatusEnum.HEALTHY:
                overall_status = HealthStatusEnum.DEGRADED # Degraded is less severe than unhealthy

        response = HealthCheckResponse(
            overall_status=overall_status,
            components=components_health,
            system_timestamp=datetime.utcnow()
        )

        log_level = logging.INFO if overall_status == HealthStatusEnum.HEALTHY else logging.WARNING
        # Ensure overall_status has .value if it's an Enum, or just use it if it's Literal
        status_value = overall_status.value if hasattr(overall_status, 'value') else overall_status
        logger.log(log_level, f"Full system health check completed. Overall status: {status_value}")
        return response

logger.info("HealthCheckService class defined.")
