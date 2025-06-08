# backend/app/src/repositories/dictionaries/calendar_provider_repository.py

"""
Repository for CalendarProvider dictionary entries.
"""

import logging

from backend.app.src.models.dictionaries.calendars import CalendarProvider
from backend.app.src.schemas.dictionaries.calendars import CalendarProviderCreate, CalendarProviderUpdate
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

logger = logging.getLogger(__name__)

class CalendarProviderRepository(BaseDictionaryRepository[CalendarProvider, CalendarProviderCreate, CalendarProviderUpdate]):
    """
    Repository for managing CalendarProvider dictionary records.
    Inherits common dictionary operations from BaseDictionaryRepository.
    """
    def __init__(self):
        super().__init__(CalendarProvider)

    # Add any CalendarProvider-specific methods here if needed.
