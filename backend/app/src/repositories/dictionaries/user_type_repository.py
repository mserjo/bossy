# backend/app/src/repositories/dictionaries/user_type_repository.py

"""
Repository for UserType dictionary entries.
"""

import logging

from backend.app.src.models.dictionaries.user_types import UserType
from backend.app.src.schemas.dictionaries.user_types import UserTypeCreate, UserTypeUpdate
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

logger = logging.getLogger(__name__)

class UserTypeRepository(BaseDictionaryRepository[UserType, UserTypeCreate, UserTypeUpdate]):
    """
    Repository for managing UserType dictionary records.
    Inherits common dictionary operations from BaseDictionaryRepository.
    """
    def __init__(self):
        super().__init__(UserType)

    # Add any UserType-specific methods here if needed.
