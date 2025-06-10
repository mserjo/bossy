# backend/app/src/schemas/system/__init__.py

"""
This package contains Pydantic schemas related to system management,
including system settings, monitoring data (logs, metrics), and health checks.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("System schemas package initialized.")

# Example of re-exporting for easier access:
# from .settings import SystemSettingResponse, SystemSettingCreate, SystemSettingUpdate
# from .monitoring import SystemLogResponse, PerformanceMetricResponse
# from .health import ServiceHealthStatusResponse

# __all__ = [
#     "SystemSettingResponse",
#     "SystemSettingCreate",
#     "SystemSettingUpdate",
#     # ... other system schemas
# ]
