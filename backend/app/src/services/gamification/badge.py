# backend/app/src/services/gamification/badge.py
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.src.services.dictionaries.base_dict import BaseDictionaryService
from app.src.models.gamification.badge import Badge # SQLAlchemy Badge model
from app.src.schemas.gamification.badge import ( # Pydantic Schemas
    BadgeCreate,
    BadgeUpdate,
    BadgeResponse,
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class BadgeService(BaseDictionaryService[Badge, BadgeCreate, BadgeUpdate, BadgeResponse]):
    """
    Service for managing Badge definitions.
    Badges are awards users can earn, defined by criteria, name, description, and an icon.
    Inherits generic CRUD operations from BaseDictionaryService.

    The Badge model is assumed to have 'name' as its primary unique human-readable key.
    BaseDictionaryService's `create` and `update` methods will check for 'name' uniqueness if the model has 'name'.
    The `get_by_code` method from BaseDictionaryService might not be directly applicable if Badge has no 'code' field;
    use `get_badge_by_name` instead or override `get_by_code`.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the BadgeService.

        Args:
            db_session (AsyncSession): The SQLAlchemy asynchronous database session.
        """
        super().__init__(db_session, model=Badge, response_schema=BadgeResponse)
        logger.info("BadgeService initialized.")

    async def get_badge_by_name(self, name: str) -> Optional[BadgeResponse]:
        """Retrieves a badge by its unique name."""
        logger.debug(f"Attempting to retrieve Badge by name: {name}")
        # Assuming Badge model has a 'name' attribute for querying.
        if not hasattr(self.model, 'name'):
            logger.error(f"Model {self._model_name} does not have a 'name' attribute. Cannot get_badge_by_name.")
            return None

        stmt = select(self.model).where(self.model.name == name)
        result = await self.db_session.execute(stmt)
        item_db = result.scalar_one_or_none()

        if item_db:
            logger.info(f"{self._model_name} with name '{name}' found.")
            # return self.response_schema.model_validate(item_db) # Pydantic v2
            return self.response_schema.from_orm(item_db) # Pydantic v1
        logger.info(f"{self._model_name} with name '{name}' not found.")
        return None

    async def list_badges_by_criteria_keyword(self, keyword: str, skip: int = 0, limit: int = 100) -> List[BadgeResponse]:
        """
        Lists badges where the criteria description contains a specific keyword.
        Assumes Badge model has a 'criteria' text field.
        """
        logger.debug(f"Listing badges with criteria keyword: '{keyword}'")
        if not hasattr(self.model, 'criteria'):
            logger.warning(f"Badge model {self._model_name} does not have 'criteria' field. Cannot search by keyword.")
            return []

        stmt = select(self.model).where(self.model.criteria.ilike(f"%{keyword}%")) \
             .order_by(getattr(self.model, 'name', self.model.id)).offset(skip).limit(limit) # type: ignore

        badges_db = (await self.db_session.execute(stmt)).scalars().all()

        # response_list = [self.response_schema.model_validate(b) for b in badges_db] # Pydantic v2
        response_list = [self.response_schema.from_orm(b) for b in badges_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} badges matching criteria keyword '{keyword}'.")
        return response_list

logger.info("BadgeService class defined.")
