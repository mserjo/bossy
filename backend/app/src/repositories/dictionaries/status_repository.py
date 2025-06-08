# backend/app/src/repositories/dictionaries/status_repository.py

"""
Repository for Status dictionary entries.
"""

import logging

from backend.app.src.models.dictionaries.statuses import Status
from backend.app.src.schemas.dictionaries.statuses import StatusCreate, StatusUpdate
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

logger = logging.getLogger(__name__)

class StatusRepository(BaseDictionaryRepository[Status, StatusCreate, StatusUpdate]):
    """
    Repository for managing Status dictionary records.
    Inherits common dictionary operations from BaseDictionaryRepository.
    """
    def __init__(self):
        super().__init__(Status)

    # Add any Status-specific methods here if needed.
    # For example, if Status model had a 'category' field:
    # async def get_by_category(self, db: AsyncSession, *, category: str) -> List[Status]:
    #     statement = select(self.model).where(self.model.category == category)
    #     result = await db.execute(statement)
    #     return list(result.scalars().all())
