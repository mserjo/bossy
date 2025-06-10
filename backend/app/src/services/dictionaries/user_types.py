# backend/app/src/services/dictionaries/user_types.py
import logging
# from typing import Optional # For potential custom methods
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select # For potential custom methods

from app.src.services.dictionaries.base_dict import BaseDictionaryService
from app.src.models.dictionaries.user_types import UserType # SQLAlchemy Model
from app.src.schemas.dictionaries.user_types import ( # Pydantic Schemas
    UserTypeCreate,
    UserTypeUpdate,
    UserTypeResponse,
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class UserTypeService(BaseDictionaryService[UserType, UserTypeCreate, UserTypeUpdate, UserTypeResponse]):
    """
    Service for managing UserType dictionary items.
    Inherits generic CRUD operations from BaseDictionaryService.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the UserTypeService.

        Args:
            db_session (AsyncSession): The SQLAlchemy asynchronous database session.
        """
        super().__init__(db_session, model=UserType, response_schema=UserTypeResponse)
        logger.info("UserTypeService initialized.")

    # --- Custom methods for UserTypeService (if any) ---
    # e.g.,  async def get_default_user_type() -> Optional[UserTypeResponse]: ...

logger.info("UserTypeService class defined.")
