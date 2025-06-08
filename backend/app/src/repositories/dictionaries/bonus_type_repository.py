# backend/app/src/repositories/dictionaries/bonus_type_repository.py

"""
Repository for BonusType dictionary entries.
"""

import logging

from backend.app.src.models.dictionaries.bonus_types import BonusType
from backend.app.src.schemas.dictionaries.bonus_types import BonusTypeCreate, BonusTypeUpdate
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

logger = logging.getLogger(__name__)

class BonusTypeRepository(BaseDictionaryRepository[BonusType, BonusTypeCreate, BonusTypeUpdate]):
    """
    Repository for managing BonusType dictionary records.
    Inherits common dictionary operations from BaseDictionaryRepository.
    """
    def __init__(self):
        super().__init__(BonusType)

    # Add any BonusType-specific methods here if needed.
    # For example, if BonusType had a 'is_penalty_type' field:
    # async def get_all_penalty_types(self, db: AsyncSession) -> List[BonusType]:
    #     statement = select(self.model).where(self.model.is_penalty_type == True)
    #     result = await db.execute(statement)
    #     return list(result.scalars().all())
