# backend/app/src/services/gamification/level.py
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.src.services.dictionaries.base_dict import BaseDictionaryService
from app.src.models.gamification.level import Level # SQLAlchemy Level model
from app.src.schemas.gamification.level import ( # Pydantic Schemas
    LevelCreate,
    LevelUpdate,
    LevelResponse,
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class LevelService(BaseDictionaryService[Level, LevelCreate, LevelUpdate, LevelResponse]):
    """
    Service for managing Level definitions.
    Levels are typically defined by minimum points required and have a name/description.
    Inherits generic CRUD operations from BaseDictionaryService.

    The Level model is assumed to have 'name' as its primary unique human-readable key.
    BaseDictionaryService's `create` and `update` methods will check for 'name' uniqueness if the model has 'name'.
    The `get_by_code` method from BaseDictionaryService would not be directly applicable if Level has no 'code' field;
    use `get_level_by_name` instead or override `get_by_code` if 'code' behavior is desired on 'name'.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the LevelService.

        Args:
            db_session (AsyncSession): The SQLAlchemy asynchronous database session.
        """
        super().__init__(db_session, model=Level, response_schema=LevelResponse)
        logger.info("LevelService initialized.")

    async def get_level_by_name(self, name: str) -> Optional[LevelResponse]:
        """Retrieves a level by its unique name."""
        logger.debug(f"Attempting to retrieve Level by name: {name}")
        # Assuming Level model has a 'name' attribute for querying.
        if not hasattr(self.model, 'name'):
            logger.error(f"Model {self._model_name} does not have a 'name' attribute. Cannot get_level_by_name.")
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

    async def get_levels_ordered_by_points(self, ascending: bool = True, skip: int = 0, limit: int = 100) -> List[LevelResponse]:
        """
        Retrieves all levels, ordered by min_points.
        """
        logger.debug(f"Attempting to retrieve all levels ordered by points {'ASC' if ascending else 'DESC'}")

        # Ensure Level model has 'min_points' attribute
        if not hasattr(self.model, 'min_points'):
            logger.error(f"Model {self._model_name} does not have 'min_points' attribute. Cannot order by points.")
            return [] # Or raise error

        order_field = self.model.min_points
        if not ascending:
            order_field = self.model.min_points.desc()

        stmt = select(self.model).order_by(order_field).offset(skip).limit(limit)
        result = await self.db_session.execute(stmt)
        items_db = result.scalars().all()

        # response_list = [self.response_schema.model_validate(item) for item in items_db] # Pydantic v2
        response_list = [self.response_schema.from_orm(item) for item in items_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} levels ordered by points.")
        return response_list

    async def get_level_for_points(self, points: int) -> Optional[LevelResponse]:
        """
        Determines the appropriate level for a given number of points.
        This typically means finding the highest level whose min_points <= given points.
        """
        logger.debug(f"Determining level for points: {points}")

        if not hasattr(self.model, 'min_points'):
            logger.error(f"Model {self._model_name} does not have 'min_points' attribute. Cannot determine level for points.")
            return None

        stmt = select(self.model).            where(self.model.min_points <= points).            order_by(self.model.min_points.desc(), self.model.id.desc()) # Ensure deterministic result if points are same

        level_db = (await self.db_session.execute(stmt)).scalars().first()

        if level_db:
            logger.info(f"Level '{level_db.name}' (ID: {level_db.id}) determined for {points} points.")
            # return self.response_schema.model_validate(level_db) # Pydantic v2
            return self.response_schema.from_orm(level_db) # Pydantic v1

        logger.info(f"No specific level found for {points} points (e.g., below lowest level threshold).")
        return None

logger.info("LevelService class defined.")
