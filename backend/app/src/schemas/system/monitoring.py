# backend/app/src/schemas/system/monitoring.py

"""
Pydantic schemas for System Monitoring, including System Logs and Performance Metrics.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone # Added timezone for __main__ example

from pydantic import Field, BaseModel # BaseModel needed if not inheriting from BaseSchema for Create schemas

from backend.app.src.schemas.base import BaseSchema, BaseResponseSchema

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- SystemLog Schemas ---

class SystemLogBase(BaseSchema):
    """Base schema for system log entries."""
    level: str = Field(..., max_length=50, description="Log level (e.g., INFO, WARNING, ERROR)", example="INFO")
    message: str = Field(..., description="The main log message", example="User authentication successful.")
    logger_name: Optional[str] = Field(None, max_length=255, description="Name of the logger that produced this entry", example="auth.service")
    module: Optional[str] = Field(None, max_length=255, description="Python module where the log originated", example="backend.app.src.services.auth")
    func_name: Optional[str] = Field(None, max_length=255, description="Function name where the log originated", example="login_user")
    line_no: Optional[int] = Field(None, ge=0, description="Line number where the log originated", example=101)
    exception_info: Optional[str] = Field(None, description="Traceback information if the log entry is associated with an exception.")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional contextual information (JSON)", example={"user_id": 123, "request_id": "xyz789"})

class SystemLogCreate(SystemLogBase):
    """
    Schema for creating a new system log entry.
    Typically used internally by the application's logging handlers.
    Timestamps (`created_at`, `updated_at`) will be set by the database via `BaseModel` in ORM.
    """
    pass # All fields inherited from SystemLogBase are suitable for creation

class SystemLogResponse(BaseResponseSchema, SystemLogBase):
    """
    Schema for representing a system log entry in API responses.
    Includes 'id', 'created_at', 'updated_at' from BaseResponseSchema.
    """
    # `created_at` from BaseResponseSchema serves as the log timestamp.
    pass


# --- PerformanceMetric Schemas ---

class PerformanceMetricBase(BaseSchema):
    """Base schema for performance metric entries."""
    metric_name: str = Field(..., max_length=255, description="Name of the metric", example="api_response_time")
    value: float = Field(..., description="The value of the metric", example=123.45)
    unit: Optional[str] = Field(None, max_length=50, description="Unit of the metric (e.g., 'ms', 'seconds', '%', 'count')", example="ms")
    tags: Optional[Dict[str, Any]] = Field(None, description="Key-value pairs for additional context or dimensions (JSON)", example={"endpoint": "/api/v1/users", "method": "POST"})

class PerformanceMetricCreate(PerformanceMetricBase):
    """
    Schema for creating a new performance metric entry.
    Timestamps (`created_at`, `updated_at`) will be set by the database.
    """
    pass # All fields from PerformanceMetricBase are suitable

class PerformanceMetricResponse(BaseResponseSchema, PerformanceMetricBase):
    """
    Schema for representing a performance metric entry in API responses.
    Includes 'id', 'created_at', 'updated_at' from BaseResponseSchema.
    `created_at` serves as the metric recording timestamp.
    """
    pass


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- System Monitoring Schemas --- Demonstration")

    # SystemLog Examples
    log_create_data = {
        "level": "ERROR",
        "message": "Database connection failed after 3 retries.",
        "loggerName": "db.connector", # camelCase alias for logger_name
        "module": "backend.app.src.db.session",
        "funcName": "get_db_session_with_retry",
        "lineNo": 55,
        "exceptionInfo": "Traceback (most recent call last):\n  ConnectionRefusedError: [Errno 111] Connection refused",
        "context": {"retry_attempts": 3, "db_host": "postgres-prod"}
    }
    try:
        log_create_schema = SystemLogCreate(**log_create_data) # type: ignore[call-arg] # Pydantic allows alias in constructor
        logger.info(f"SystemLogCreate valid: {log_create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating SystemLogCreate: {e}")

    log_response_data = {
        "id": 101,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "level": "ERROR",
        "message": "Database connection failed after 3 retries.",
        "loggerName": "db.connector",
        "module": "backend.app.src.db.session",
        "funcName": "get_db_session_with_retry",
        "lineNo": 55,
        "exceptionInfo": "Traceback (most recent call last):\n  ConnectionRefusedError: [Errno 111] Connection refused",
        "context": {"retry_attempts": 3, "db_host": "postgres-prod"}
    }
    try:
        log_response_schema = SystemLogResponse(**log_response_data) # type: ignore[call-arg]
        logger.info(f"SystemLogResponse: {log_response_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating SystemLogResponse: {e}")


    # PerformanceMetric Examples
    metric_create_data = {
        "metricName": "cpu_utilization", # camelCase alias for metric_name
        "value": 75.5,
        "unit": "%",
        "tags": {"host": "server-1", "service": "user_api"}
    }
    try:
        metric_create_schema = PerformanceMetricCreate(**metric_create_data) # type: ignore[call-arg]
        logger.info(f"PerformanceMetricCreate valid: {metric_create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating PerformanceMetricCreate: {e}")

    metric_response_data = {
        "id": 202,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "metricName": "cpu_utilization",
        "value": 75.5,
        "unit": "%",
        "tags": {"host": "server-1", "service": "user_api"}
    }
    try:
        metric_response_schema = PerformanceMetricResponse(**metric_response_data) # type: ignore[call-arg]
        logger.info(f"PerformanceMetricResponse: {metric_response_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating PerformanceMetricResponse: {e}")
