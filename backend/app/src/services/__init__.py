# backend/app/src/services/__init__.py
import logging

# Initialize logger for this module
logger = logging.getLogger(__name__)

logger.info("Services package initialized.")

# Import BaseService to make it directly available when importing from 'services'
try:
    from .base import BaseService
    logger.info("Successfully imported BaseService from .base")
except ImportError:
    logger.warning("BaseService could not be imported from .base. It might not be defined yet.")
    BaseService = None

# Import system services
try:
    from .system import (
        HealthCheckService,
        InitialDataService,
        SystemMonitoringService,
        SystemSettingService
    )
    logger.info("Successfully imported system services: HealthCheck, InitialData, SystemMonitoring, SystemSetting.")
    system_services_imported = True
except ImportError as e:
    logger.warning(f"Could not import one or more system services from .system: {e}")
    # Define placeholders if import fails, so hasattr checks or direct use won't immediately break
    # if code elsewhere defensively checks for these names.
    HealthCheckService = None
    InitialDataService = None
    SystemMonitoringService = None
    SystemSettingService = None
    system_services_imported = False


__all__ = [
    "BaseService",
]

# Add system services to __all__ if they were imported
if system_services_imported:
    __all__.extend([
        "HealthCheckService",
        "InitialDataService",
        "SystemMonitoringService",
        "SystemSettingService",
    ])

# Filter out None placeholders from __all__
# This ensures that if BaseService or any system service failed to import (and is None),
# it won't be listed in __all__, preventing AttributeError for `from services import NonExistentService`.
__all__ = [name for name in __all__ if globals().get(name) is not None]

# Further imports for specific service classes can be added here as they are created.
# For example:
# from .auth import AuthService
# from .user import UserService
#
# And then extend __all__:
# __all__.extend([
#     "AuthService",
#     "UserService",
# ])
# Remember to also filter them if they are imported conditionally.

logger.info(f"Services package exports: {__all__}")
