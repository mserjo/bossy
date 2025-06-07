# backend/app/src/models/system/__init__.py

"""
This package contains system-level SQLAlchemy models, such as those for
system settings, monitoring, logs, and health checks.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("System models package initialized.")

# You can choose to expose specific models directly from the package level for convenience,
# e.g., from .settings import SystemSetting
# This makes imports shorter: from backend.app.src.models.system import SystemSetting

# For now, we'll keep it simple and require explicit imports from the submodules.

# __all__ = [
#     "SystemSetting",
#     "SystemLog",
#     "PerformanceMetric",
#     "ServiceHealthStatus",
# ] # Example if you were to re-export them here
