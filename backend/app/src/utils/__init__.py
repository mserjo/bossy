# backend/app/src/utils/__init__.py

import logging

"""
This package contains various utility modules and helper functions for the application.

Modules within this package provide reusable logic for common tasks such as
hashing, security operations, data validation, formatting, generation,
type conversion, and other miscellaneous helpers.

Selective imports can be done here to make commonly used utilities
accessible directly from `app.src.utils`, for example:

    # from .hash import get_password_hash, verify_password
    # from .security import generate_secure_random_string

    # __all__ = [
    #     "get_password_hash",
    #     "verify_password",
    #     "generate_secure_random_string",
    #     # Add other frequently used utilities here
    # ]

For now, this __init__.py is kept simple, allowing direct imports from submodules.
"""

# Example: If you want to expose specific functions directly from `app.src.utils`
# you can uncomment and adjust the following lines once the modules are created:

from .hash import get_password_hash, verify_password
from .security import generate_secure_random_string
from .validators import is_strong_password, is_valid_phone_number
from .formatters import format_datetime, format_currency
from .generators import generate_random_code, generate_unique_slug
from .converters import markdown_to_html
from .helpers import get_current_utc_timestamp

__all__ = [
    "get_password_hash",
    "verify_password",
    "generate_secure_random_string",
    "is_strong_password",
    "is_valid_phone_number",
    "format_datetime",
    "format_currency",
    "generate_random_code",
    "generate_unique_slug",
    "markdown_to_html",
    "get_current_utc_timestamp",
]

logger = logging.getLogger(__name__)
logger.debug("Utilities package initialized.")
