# backend/app/src/services/dictionaries/calendars.py
import logging
# from typing import Optional # For potential custom methods
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select # For potential custom methods

from app.src.services.dictionaries.base_dict import BaseDictionaryService
from app.src.models.dictionaries.calendars import CalendarProvider # SQLAlchemy Model
from app.src.schemas.dictionaries.calendars import ( # Pydantic Schemas
    CalendarProviderCreate,
    CalendarProviderUpdate,
    CalendarProviderResponse,
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class CalendarProviderService(BaseDictionaryService[CalendarProvider, CalendarProviderCreate, CalendarProviderUpdate, CalendarProviderResponse]):
    """
    Service for managing CalendarProvider dictionary items.
    These represent different calendar platforms the system can integrate with (e.g., Google Calendar, Outlook).
    Inherits generic CRUD operations from BaseDictionaryService.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the CalendarProviderService.

        Args:
            db_session (AsyncSession): The SQLAlchemy asynchronous database session.
        """
        super().__init__(db_session, model=CalendarProvider, response_schema=CalendarProviderResponse)
        logger.info("CalendarProviderService initialized.")

    # --- Custom methods for CalendarProviderService (if any) ---
    # For example, methods to check if a provider is enabled or requires specific configuration:
    # async def is_provider_enabled(self, provider_code: str) -> bool:
    #     provider = await self.get_by_code(provider_code)
    #     if provider and hasattr(provider, 'is_enabled') and provider.is_enabled: # Assuming an 'is_enabled' field
    #         return True
    #     return False

logger.info("CalendarProviderService class defined.")
