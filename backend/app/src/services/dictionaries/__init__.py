# backend/app/src/services/dictionaries/__init__.py
import logging

# Initialize logger for this module
logger = logging.getLogger(__name__)

logger.info("Dictionary services sub-package initialized.")

# Import BaseDictionaryService first as other services will inherit from it
try:
    from .base_dict import BaseDictionaryService
    logger.info("Successfully imported BaseDictionaryService from .base_dict")
except ImportError:
    logger.warning("BaseDictionaryService could not be imported from .base_dict. It might not be defined yet.")
    BaseDictionaryService = None # Placeholder

# Import specific dictionary service classes
# These imports assume the service files (statuses.py, user_roles.py, etc.)
# will be created in the same directory.

SERVICE_FILES = {
    "StatusService": ".statuses",
    "UserRoleService": ".user_roles",
    "UserTypeService": ".user_types",
    "GroupTypeService": ".group_types",
    "TaskTypeService": ".task_types",
    "BonusTypeService": ".bonus_types",
    "CalendarProviderService": ".calendars", # Name from structure doc for consistency
    "MessengerPlatformService": ".messengers", # Name from structure doc
}

# Dynamically import services and add to __all__
__all__ = ["BaseDictionaryService"] if BaseDictionaryService else []

for service_name, module_name in SERVICE_FILES.items():
    try:
        # The `level=1` in __import__ signifies a relative import from the current package
        module = __import__(module_name, globals(), locals(), [service_name], 1)
        service_class = getattr(module, service_name)
        globals()[service_name] = service_class # Make it available in the package namespace
        __all__.append(service_name)
        logger.info(f"Successfully imported {service_name} from {module_name}")
    except (ImportError, AttributeError) as e:
        logger.warning(f"{service_name} could not be imported from {module_name}: {e}. It might not be defined yet.")
        globals()[service_name] = None # Define as None if import fails

# Clean __all__ from None entries if any service failed to import and BaseDictionaryService was None
__all__ = [name for name in __all__ if globals().get(name) is not None]

logger.info(f"Dictionary services sub-package exports: {__all__}")
