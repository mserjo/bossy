# backend/app/src/schemas/system/health.py

"""
Pydantic schemas for Service Health Status.
"""

import logging
from typing import Optional, Dict, Any, List # Added List for OverallSystemHealthResponse
from datetime import datetime, timezone # Added timezone for default_factory and examples

from pydantic import Field

from backend.app.src.schemas.base import BaseSchema, BaseResponseSchema
from backend.app.src.models.system.health import HealthStatusEnum # Import Enum from model

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- ServiceHealthStatus Schemas ---

class ServiceHealthStatusBase(BaseSchema):
    """Base schema for service health status entries."""
    service_name: str = Field(..., max_length=255, description="Unique name identifying the service or component.", example="Database Main Cluster")
    status: HealthStatusEnum = Field(..., description="Current health status of the service.", example=HealthStatusEnum.OK)
    details: Optional[str] = Field(None, description="Human-readable message providing more details about the status.", example="All systems operational.")
    last_checked_at: datetime = Field(..., description="Timestamp of when this health status was last checked/updated (UTC).", example=datetime.now(timezone.utc))
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional structured information about the check (JSON).", example={"response_time_ms": 55, "active_connections": 120})

class ServiceHealthStatusCreate(ServiceHealthStatusBase):
    """
    Schema for creating a new service health status entry.
    Typically used by monitoring services or health check endpoints.
    """
    # All fields from ServiceHealthStatusBase are typically required on creation,
    # though some might have defaults if appropriate (e.g., details, metadata).
    pass

class ServiceHealthStatusUpdate(BaseSchema):
    """
    Schema for updating an existing service health status entry.
    All fields are optional for partial updates. `service_name` is usually not updatable.
    """
    status: Optional[HealthStatusEnum] = Field(None, description="Current health status of the service.")
    details: Optional[str] = Field(None, description="Human-readable message providing more details about the status.")
    last_checked_at: Optional[datetime] = Field(None, description="Timestamp of when this health status was last checked/updated (UTC).")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional structured information about the check (JSON).")

class ServiceHealthStatusResponse(BaseResponseSchema, ServiceHealthStatusBase):
    """
    Schema for representing a service health status in API responses.
    Includes 'id', 'created_at', 'updated_at' from BaseResponseSchema.
    """
    # `created_at` from BaseResponseSchema indicates when the health record was first logged.
    # `updated_at` indicates when this record (e.g. its status or details) was last modified.
    # `last_checked_at` is specific to when the service itself was probed.
    pass


# --- Overall System Health Schema (Example for a /health endpoint) ---

class ComponentHealth(BaseSchema):
    """Individual component health status for the overall system health response."""
    service_name: str = Field(..., description="Name of the service/component")
    status: HealthStatusEnum = Field(..., description="Health status of this component")
    details: Optional[str] = Field(None, description="Optional details about the component's status")

class OverallSystemHealthResponse(BaseSchema):
    """
    Schema for an API endpoint that reports the overall system health,
    possibly including the status of critical components.
    """
    overall_status: HealthStatusEnum = Field(..., description="Overall health status of the system (e.g., OK if all critical components are OK)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the health check was performed (UTC)")
    components: List[ComponentHealth] = Field(default_factory=list, description="Health status of individual critical components")
    # Can add more fields like system version, uptime, etc.


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    from datetime import timedelta # For example datetimes

    logger.info("--- ServiceHealthStatus Schemas --- Demonstration")

    # Create
    health_create_data = {
        "serviceName": "Payment Gateway API", # camelCase alias for service_name
        "status": HealthStatusEnum.WARNING,
        "details": "Experiencing intermittent timeouts, but operational.",
        "lastCheckedAt": datetime.now(timezone.utc).isoformat(),
        "metadata": {"avg_timeout_rate_percent": 5, "error_codes": ["P-504"]}
    }
    try:
        health_create_schema = ServiceHealthStatusCreate(**health_create_data) # type: ignore[call-arg]
        logger.info(f"ServiceHealthStatusCreate valid: {health_create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating ServiceHealthStatusCreate: {e}")

    # Update
    health_update_data = {"status": HealthStatusEnum.OK, "details": "Service fully recovered."}
    health_update_schema = ServiceHealthStatusUpdate(**health_update_data)
    logger.info(f"ServiceHealthStatusUpdate: {health_update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # Response
    health_response_data = {
        "id": 303,
        "createdAt": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "serviceName": "Redis Cache",
        "status": "ok", # Can pass string value of enum for Pydantic to coerce
        "details": "Running smoothly.",
        "lastCheckedAt": datetime.now(timezone.utc).isoformat(),
        "metadata": {"connected_clients": 55}
    }
    try:
        health_response_schema = ServiceHealthStatusResponse(**health_response_data) # type: ignore[call-arg]
        logger.info(f"ServiceHealthStatusResponse: {health_response_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating ServiceHealthStatusResponse: {e}")


    logger.info("\n--- OverallSystemHealthResponse Schema --- Demonstration")
    overall_health = OverallSystemHealthResponse(
        overall_status=HealthStatusEnum.OK,
        components=[
            ComponentHealth(service_name="Database", status=HealthStatusEnum.OK),
            ComponentHealth(service_name="BackgroundWorker", status=HealthStatusEnum.OK),
            ComponentHealth(service_name="ExternalEmailAPI", status=HealthStatusEnum.WARNING, details="Slight delay in email sending")
        ]
    )
    logger.info(f"OverallSystemHealthResponse: {overall_health.model_dump_json(by_alias=True, indent=2)}")
