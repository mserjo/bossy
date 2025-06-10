# backend/app/src/services/dictionaries/statuses.py
import logging
from typing import List # Required for commented out example
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select # Required for commented out example

from app.src.services.dictionaries.base_dict import BaseDictionaryService
from app.src.models.dictionaries.statuses import Status # SQLAlchemy Model
from app.src.schemas.dictionaries.statuses import ( # Pydantic Schemas
    StatusCreate,
    StatusUpdate,
    StatusResponse,
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class StatusService(BaseDictionaryService[Status, StatusCreate, StatusUpdate, StatusResponse]):
    """
    Service for managing Status dictionary items.
    Inherits generic CRUD operations from BaseDictionaryService.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the StatusService.

        Args:
            db_session (AsyncSession): The SQLAlchemy asynchronous database session.
        """
        super().__init__(db_session, model=Status, response_schema=StatusResponse)
        logger.info("StatusService initialized.")

    # --- Custom methods for StatusService (if any) ---
    # For example, if statuses had specific business logic beyond simple CRUD:
    # async def get_active_statuses(self) -> List[StatusResponse]:
    #     logger.debug("Attempting to retrieve all active statuses.")
    #     # Assuming an 'is_active' field on the Status model
    #     # stmt = select(self.model).where(self.model.is_active == True).order_by(self.model.name)
    #     # result = await self.db_session.execute(stmt)
    #     # items_db = result.scalars().all()
    #     # Pydantic v1:
    #     # response_list = [self.response_schema.from_orm(item) for item in items_db]
    #     # Pydantic v2:
    #     # response_list = [self.response_schema.model_validate(item) for item in items_db]
    #     # logger.info(f"Retrieved {len(response_list)} active statuses.")
    #     # return response_list
    #     pass # Placeholder for custom methods

    # The generic CRUD methods (get_by_id, get_by_code, get_all, create, update, delete)
    # are inherited from BaseDictionaryService and will use the Status model and schemas.

logger.info("StatusService class defined.")
