# backend/app/src/services/dictionaries/group_types.py
import logging
# from typing import List # For potential custom methods
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select # For potential custom methods

from app.src.services.dictionaries.base_dict import BaseDictionaryService
from app.src.models.dictionaries.group_types import GroupType # SQLAlchemy Model
from app.src.schemas.dictionaries.group_types import ( # Pydantic Schemas
    GroupTypeCreate,
    GroupTypeUpdate,
    GroupTypeResponse,
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class GroupTypeService(BaseDictionaryService[GroupType, GroupTypeCreate, GroupTypeUpdate, GroupTypeResponse]):
    """
    Service for managing GroupType dictionary items.
    Inherits generic CRUD operations from BaseDictionaryService.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the GroupTypeService.

        Args:
            db_session (AsyncSession): The SQLAlchemy asynchronous database session.
        """
        super().__init__(db_session, model=GroupType, response_schema=GroupTypeResponse)
        logger.info("GroupTypeService initialized.")

    # --- Custom methods for GroupTypeService (if any) ---
    # e.g.,  async def get_group_types_for_organizations() -> List[GroupTypeResponse]: ...

logger.info("GroupTypeService class defined.")
