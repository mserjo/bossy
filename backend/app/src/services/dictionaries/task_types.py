# backend/app/src/services/dictionaries/task_types.py
import logging
# from typing import List # For potential custom methods
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select # For potential custom methods

from app.src.services.dictionaries.base_dict import BaseDictionaryService
from app.src.models.dictionaries.task_types import TaskType # SQLAlchemy Model
from app.src.schemas.dictionaries.task_types import ( # Pydantic Schemas
    TaskTypeCreate,
    TaskTypeUpdate,
    TaskTypeResponse,
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class TaskTypeService(BaseDictionaryService[TaskType, TaskTypeCreate, TaskTypeUpdate, TaskTypeResponse]):
    """
    Service for managing TaskType dictionary items.
    Inherits generic CRUD operations from BaseDictionaryService.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the TaskTypeService.

        Args:
            db_session (AsyncSession): The SQLAlchemy asynchronous database session.
        """
        super().__init__(db_session, model=TaskType, response_schema=TaskTypeResponse)
        logger.info("TaskTypeService initialized.")

    # --- Custom methods for TaskTypeService (if any) ---
    # e.g.,  async def get_task_types_for_events() -> List[TaskTypeResponse]: ...

logger.info("TaskTypeService class defined.")
