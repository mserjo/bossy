# backend/app/src/services/dictionaries/messengers.py
import logging
# from typing import Optional, Dict, Any # For potential custom methods
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select # For potential custom methods

from app.src.services.dictionaries.base_dict import BaseDictionaryService
from app.src.models.dictionaries.messengers import MessengerPlatform # SQLAlchemy Model
from app.src.schemas.dictionaries.messengers import ( # Pydantic Schemas
    MessengerPlatformCreate,
    MessengerPlatformUpdate,
    MessengerPlatformResponse,
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class MessengerPlatformService(BaseDictionaryService[MessengerPlatform, MessengerPlatformCreate, MessengerPlatformUpdate, MessengerPlatformResponse]):
    """
    Service for managing MessengerPlatform dictionary items.
    These represent different messaging platforms the system can integrate with for notifications (e.g., Telegram, Slack).
    Inherits generic CRUD operations from BaseDictionaryService.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the MessengerPlatformService.

        Args:
            db_session (AsyncSession): The SQLAlchemy asynchronous database session.
        """
        super().__init__(db_session, model=MessengerPlatform, response_schema=MessengerPlatformResponse)
        logger.info("MessengerPlatformService initialized.")

    # --- Custom methods for MessengerPlatformService (if any) ---
    # For example, methods to retrieve webhook URLs or API keys if stored (though sensitive data should be in config/secrets):
    # async def get_platform_config_details(self, platform_code: str) -> Optional[Dict[str, Any]]:
    #     platform = await self.get_by_code(platform_code)
    #     if platform and hasattr(platform, 'configuration_details'): # Assuming a field in model
    #         # Ensure that 'configuration_details' is a dict or can be converted to one.
    #         # If it's a JSON string in the DB, you might need to json.loads() here.
    #         # For Pydantic models, this might already be handled if the field type is Dict.
    #         return platform.configuration_details # type: ignore
    #     return None

logger.info("MessengerPlatformService class defined.")
