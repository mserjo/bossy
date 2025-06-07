# backend/app/src/models/system/health.py

"""
SQLAlchemy model for storing the health status of various internal or external services
that the application relies on or monitors.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta # Added timedelta for __main__
from enum import Enum as PythonEnum # For HealthStatusEnum definition

from sqlalchemy import String, Text, JSON, Enum as SQLAlchemyEnum, DateTime # Added DateTime
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.src.models.base import BaseModel # Import your base model

# Configure logger for this module
logger = logging.getLogger(__name__)

class HealthStatusEnum(PythonEnum): # Changed to inherit from PythonEnum for clarity in definition
    """ Defines the possible health statuses for a service. """
    OK = "ok"             # Service is operating normally.
    WARNING = "warning"   # Service is operational but has issues (e.g., degraded performance, minor errors).
    ERROR = "error"       # Service is experiencing significant errors or is partially unavailable.
    CRITICAL = "critical" # Service is down or completely unresponsive.
    UNKNOWN = "unknown"     # Service health status cannot be determined.

class ServiceHealthStatus(BaseModel):
    """
    Represents the health status of a dependent service or component.
    This can be used for a dashboard that shows the status of critical dependencies
    like the database, Redis, external APIs, etc.

    Attributes:
        service_name (str): A unique name identifying the service or component (e.g., 'Database', 'RedisCache', 'PaymentGatewayAPI').
        status (HealthStatusEnum): The current health status of the service.
        details (Optional[str]): A human-readable message providing more details about the status (e.g., error message, response time).
        last_checked_at (datetime): Timestamp of when this health status was last checked/updated (should be UTC).
        metadata (Optional[Dict]): Additional structured information about the check (e.g., specific check endpoint, duration).
        # `created_at` and `updated_at` from BaseModel track the record itself.
    """
    __tablename__ = "service_health_statuses"

    service_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True, comment="Unique name of the service being monitored")

    status: Mapped[HealthStatusEnum] = mapped_column(
        SQLAlchemyEnum(HealthStatusEnum, name="healthstatusenum", create_constraint=True, native_enum=False), # native_enum=False for string storage
        nullable=False,
        default=HealthStatusEnum.UNKNOWN,
        index=True,
        comment="Current health status of the service (e.g., ok, warning, error)"
    )

    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Detailed information about the health status")

    # last_checked_at is distinct from updated_at. updated_at is for the record in this table.
    # last_checked_at is when the actual service health was probed.
    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="Timestamp of the last health check (UTC)")

    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="Additional metadata from the health check (e.g., response time, error codes)")

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<ServiceHealthStatus(id={id_val}, service_name='{self.service_name}', status='{self.status.value}')>"

if __name__ == "__main__":
    # This block is for demonstration and basic testing of model structure.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- ServiceHealthStatus Model --- Demonstration")

    db_health = ServiceHealthStatus(
        service_name="PostgreSQL_DB",
        status=HealthStatusEnum.OK,
        details="Connection successful, latency normal.",
        last_checked_at=datetime.now(timezone.utc),
        metadata={"ping_latency_ms": 15}
    )
    # Simulate ORM-set fields for demo
    db_health.id = 1
    db_health.created_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_health.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example ServiceHealthStatus: {db_health!r}")
    logger.info(f"  Details: {db_health.details}")
    logger.info(f"  Metadata: {db_health.metadata}")
    logger.info(f"  Last Checked: {db_health.last_checked_at.isoformat()}")

    redis_health_error = ServiceHealthStatus(
        service_name="Redis_Cache",
        status=HealthStatusEnum.ERROR,
        details="Failed to connect to Redis server: Connection timed out.",
        last_checked_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        metadata={"error_code": "TIMEOUT"}
    )
    redis_health_error.id = 2
    redis_health_error.created_at = datetime.now(timezone.utc) - timedelta(days=1)
    redis_health_error.updated_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    logger.info(f"Example ServiceHealthStatus (Error): {redis_health_error!r}")
    logger.info(f"  Details: {redis_health_error.details}")
    logger.info(f"  Last Checked: {redis_health_error.last_checked_at.isoformat()}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup.
    # It's here for illustrative purposes of what could be inspected.
    # logger.info(f"ServiceHealthStatus attributes (conceptual table columns): {[c.name for c in ServiceHealthStatus.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
