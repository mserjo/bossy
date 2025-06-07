# backend/app/src/models/__init__.py

"""
This file makes the 'models' directory a Python package.
It can also be used to provide easier imports for commonly used models or the Base class, for example:
# from .base import Base (if Base is defined or re-exported here)
# from .auth.user import User
# from .groups.group import Group
"""

# For now, keep it simple. Specific models will be imported directly from their modules.

# It's good practice to define what `from backend.app.src.models import *` would import,
# though explicit imports are generally preferred.
# __all__ = [
#     # List model names here if you want to support `import *`
# ]

import logging

# Attempt to get a logger instance. If logging is not yet configured,
# this will use the root logger's default settings (usually WARNING level to console).
# Once `setup_logging()` from `config.logging` is called, this logger will adopt that configuration.
logger = logging.getLogger(__name__)

# This log message is to confirm the package is recognized/imported during development.
logger.debug("Backend models package initialized.")
