# backend/app/src/services/dictionaries/bonus_types.py
import logging
# from typing import List # For potential custom methods
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select # For potential custom methods

from app.src.services.dictionaries.base_dict import BaseDictionaryService
from app.src.models.dictionaries.bonus_types import BonusType # SQLAlchemy Model
from app.src.schemas.dictionaries.bonus_types import ( # Pydantic Schemas
    BonusTypeCreate,
    BonusTypeUpdate,
    BonusTypeResponse,
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class BonusTypeService(BaseDictionaryService[BonusType, BonusTypeCreate, BonusTypeUpdate, BonusTypeResponse]):
    """
    Service for managing BonusType dictionary items.
    Inherits generic CRUD operations from BaseDictionaryService.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the BonusTypeService.

        Args:
            db_session (AsyncSession): The SQLAlchemy asynchronous database session.
        """
        super().__init__(db_session, model=BonusType, response_schema=BonusTypeResponse)
        logger.info("BonusTypeService initialized.")

    # --- Custom methods for BonusTypeService (if any) ---
    # e.g.,  async def get_bonus_types_for_penalties() -> List[BonusTypeResponse]: ...

logger.info("BonusTypeService class defined.")
