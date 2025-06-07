# backend/app/src/services/__init__.py
import logging

# Initialize logger for this module
logger = logging.getLogger(__name__)

logger.info("Services package initialized.")

# Import BaseService to make it directly available when importing from 'services'
# e.g., from app.src.services import BaseService
try:
    from .base import BaseService
    logger.info("Successfully imported BaseService from .base")
except ImportError:
    logger.warning("BaseService could not be imported from .base. It might not be defined yet.")
    # Define a placeholder if needed, or let it fail if BaseService is critical for package init
    BaseService = None

__all__ = [
    "BaseService",
]

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

logger.info(f"Services package exports: {__all__}")
