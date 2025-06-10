# backend/app/src/services/system/__init__.py
import logging

# Initialize logger for this module
logger = logging.getLogger(__name__)

logger.info("System services sub-package initialized.")

# Import system service classes to make them available when importing from this package
# e.g., from app.src.services.system import HealthCheckService

# These imports assume the service files (health.py, initialization.py, etc.)
# will be created in the same directory.
try:
    from .health import HealthCheckService
    logger.info("Successfully imported HealthCheckService from .health")
except ImportError:
    logger.warning("HealthCheckService could not be imported from .health. It might not be defined yet.")
    HealthCheckService = None # Placeholder

try:
    from .initialization import InitialDataService
    logger.info("Successfully imported InitialDataService from .initialization")
except ImportError:
    logger.warning("InitialDataService could not be imported from .initialization. It might not be defined yet.")
    InitialDataService = None # Placeholder

try:
    from .monitoring import SystemMonitoringService
    logger.info("Successfully imported SystemMonitoringService from .monitoring")
except ImportError:
    logger.warning("SystemMonitoringService could not be imported from .monitoring. It might not be defined yet.")
    SystemMonitoringService = None # Placeholder

try:
    from .settings import SystemSettingService
    logger.info("Successfully imported SystemSettingService from .settings")
except ImportError:
    logger.warning("SystemSettingService could not be imported from .settings. It might not be defined yet.")
    SystemSettingService = None # Placeholder


__all__ = [
    "HealthCheckService",
    "InitialDataService",
    "SystemMonitoringService",
    "SystemSettingService",
]

# Filter out None placeholders from __all__ in case some services are not yet implemented
__all__ = [name for name in __all__ if globals().get(name) is not None]

logger.info(f"System services sub-package exports: {__all__}")
