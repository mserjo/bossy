# backend/app/src/repositories/dictionaries/messenger_platform_repository.py

"""
Repository for MessengerPlatform dictionary entries.
"""

import logging

from backend.app.src.models.dictionaries.messengers import MessengerPlatform
from backend.app.src.schemas.dictionaries.messengers import MessengerPlatformCreate, MessengerPlatformUpdate
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

logger = logging.getLogger(__name__)

class MessengerPlatformRepository(BaseDictionaryRepository[MessengerPlatform, MessengerPlatformCreate, MessengerPlatformUpdate]):
    """
    Repository for managing MessengerPlatform dictionary records.
    Inherits common dictionary operations from BaseDictionaryRepository.
    """
    def __init__(self):
        super().__init__(MessengerPlatform)

    # Add any MessengerPlatform-specific methods here if needed.
