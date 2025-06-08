# backend/app/src/repositories/dictionaries/user_role_repository.py

"""
Repository for UserRole dictionary entries.
"""

import logging

from backend.app.src.models.dictionaries.user_roles import UserRole
from backend.app.src.schemas.dictionaries.user_roles import UserRoleCreate, UserRoleUpdate
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

logger = logging.getLogger(__name__)

class UserRoleRepository(BaseDictionaryRepository[UserRole, UserRoleCreate, UserRoleUpdate]):
    """
    Repository for managing UserRole dictionary records.
    Inherits common dictionary operations from BaseDictionaryRepository.
    """
    def __init__(self):
        super().__init__(UserRole)

    # Add any UserRole-specific methods here if needed.
    # For example, if UserRole had an 'is_system_role' field:
    # async def get_all_system_roles(self, db: AsyncSession) -> List[UserRole]:
    #     statement = select(self.model).where(self.model.is_system_role == True)
    #     result = await db.execute(statement)
    #     return list(result.scalars().all())
