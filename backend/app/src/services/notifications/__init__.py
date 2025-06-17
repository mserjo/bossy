# backend/app/src/services/notifications/__init__.py
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

logger.info("Notification services sub-package initialized.")

# Import specific notification-related service classes
# These imports assume the service files (template.py, notification.py, delivery.py, etc.)
# will be created in the same directory or sub-directories.

SERVICE_FILES = {
    "NotificationTemplateService": ".template",
    "NotificationService": ".notification", # Or InternalNotificationService
    "NotificationDeliveryService": ".delivery",
    # Specific channel senders might be imported directly if not too many,
    # or re-exported from a delivery_channels sub-module.
    "EmailNotificationService": ".delivery_channels", # Assuming they are in delivery_channels.py
    "SmsNotificationService": ".delivery_channels",   # Or e.g., ".email_service" if in separate files
    "PushNotificationService": ".delivery_channels",
}

# Dynamically import services and add to __all__
__all__ = []

for service_name, module_name in SERVICE_FILES.items():
    try:
        # Attempt to import the service class from the specified module
        # The `[service_name]` part in __import__ ensures we get the module itself if service_name is in it.
        # The `level=1` signifies a relative import from the current package.
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

logger.info(f"Notification services sub-package exports: {__all__}")
