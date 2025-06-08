# backend/app/src/services/integrations/__init__.py
import logging

# Initialize logger for this module
logger = logging.getLogger(__name__)

logger.info("Integration services sub-package initialized.")

# Import base and specific integration service classes
# These imports assume the service files will be created in this directory or subdirectories.

SERVICE_FILES = {
    # Calendar Services
    "BaseCalendarIntegrationService": ".calendar_base",
    "GoogleCalendarService": ".google_calendar_service",
    "OutlookCalendarService": ".outlook_calendar_service",

    # Messenger Services Base (optional, but good for structure)
    "BaseMessengerIntegrationService": ".messenger_base",

    # Specific Messenger Services
    "TelegramIntegrationService": ".telegram_service",
    "ViberIntegrationService": ".viber_service", # Placeholder, Viber might be complex
    "SlackIntegrationService": ".slack_service",
    "TeamsIntegrationService": ".teams_service", # Microsoft Teams

    # Other potential integrations
    # "PaymentGatewayService": ".payment_gateway_service", # Example
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
        # Log as warning because some services might be planned but not yet implemented
        logger.warning(f"{service_name} could not be imported from {module_name}: {e}. It might not be defined yet.")
        globals()[service_name] = None # Define as None if import fails

# Clean __all__ from None entries if any service failed to import
__all__ = [name for name in __all__ if globals().get(name) is not None]

logger.info(f"Integration services sub-package exports: {__all__}")
