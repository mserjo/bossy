# backend/app/src/schemas/__init__.py

"""
This package will contain Pydantic schemas used for data validation,
serialization, and API request/response models.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Schemas package initialized.")

# It can be useful to re-export base schemas or common schemas from here, for example:
# from .base import BaseSchema, PaginatedResponse, MessageResponse
#
# __all__ = [
#     "BaseSchema",
#     "PaginatedResponse",
#     "MessageResponse",
#     # other re-exported schemas
# ]
