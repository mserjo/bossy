# backend/app/src/repositories/dictionaries/group_type_repository.py

"""
Repository for GroupType dictionary entries.
"""

import logging

from backend.app.src.models.dictionaries.group_types import GroupType
from backend.app.src.schemas.dictionaries.group_types import GroupTypeCreate, GroupTypeUpdate
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

logger = logging.getLogger(__name__)

class GroupTypeRepository(BaseDictionaryRepository[GroupType, GroupTypeCreate, GroupTypeUpdate]):
    """
    Repository for managing GroupType dictionary records.
    Inherits common dictionary operations from BaseDictionaryRepository.
    """
    def __init__(self):
        super().__init__(GroupType)

    # Add any GroupType-specific methods here if needed.
