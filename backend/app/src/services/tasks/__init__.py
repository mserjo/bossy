# backend/app/src/services/tasks/__init__.py
import logging

# Initialize logger for this module
logger = logging.getLogger(__name__)

logger.info("Task and Event services sub-package initialized.")

# Import specific task-related service classes
# These imports assume the service files (task.py, event.py, etc.)
# will be created in the same directory.

SERVICE_FILES = {
    "TaskService": ".task",
    "EventService": ".event",
    "TaskAssignmentService": ".assignment",
    "TaskCompletionService": ".completion",
    "TaskReviewService": ".review",
    "TaskSchedulingService": ".scheduler",
}

# Dynamically import services and add to __all__
__all__ = []

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

# Clean __all__ from None entries if any service failed to import
__all__ = [name for name in __all__ if globals().get(name) is not None]

logger.info(f"Task and Event services sub-package exports: {__all__}")
