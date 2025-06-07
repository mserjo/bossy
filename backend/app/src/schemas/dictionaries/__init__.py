# backend/app/src/schemas/dictionaries/__init__.py

"""
This package contains Pydantic schemas related to dictionary/lookup tables,
such as statuses, roles, types, etc.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Dictionary schemas package initialized.")

# Example of re-exporting for easier access:
# from .base_dict import DictionaryCreate, DictionaryUpdate, DictionaryResponse
# from .statuses import StatusResponse, StatusCreate # etc.

# __all__ = [
#     "DictionaryCreate",
#     "DictionaryUpdate",
#     "DictionaryResponse",
#     # ... other dictionary schemas
# ]
