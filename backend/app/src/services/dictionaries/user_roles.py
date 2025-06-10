# backend/app/src/services/dictionaries/user_roles.py
import logging
from typing import Optional # Required for commented out example
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select # Required for commented out example

from app.src.services.dictionaries.base_dict import BaseDictionaryService
from app.src.models.dictionaries.user_roles import UserRole # SQLAlchemy Model
from app.src.schemas.dictionaries.user_roles import ( # Pydantic Schemas
    UserRoleCreate,
    UserRoleUpdate,
    UserRoleResponse,
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class UserRoleService(BaseDictionaryService[UserRole, UserRoleCreate, UserRoleUpdate, UserRoleResponse]):
    """
    Service for managing UserRole dictionary items.
    Inherits generic CRUD operations from BaseDictionaryService.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the UserRoleService.

        Args:
            db_session (AsyncSession): The SQLAlchemy asynchronous database session.
        """
        super().__init__(db_session, model=UserRole, response_schema=UserRoleResponse)
        logger.info("UserRoleService initialized.")

    # --- Custom methods for UserRoleService (if any) ---
    # For example, assigning a default role or checking role permissions might go here
    # if not handled by a more specialized auth/permission service.

    # async def get_role_by_name(self, name: str) -> Optional[UserRoleResponse]:
    #     """Retrieves a user role by its unique name (if name is unique)."""
    #     logger.debug(f"Attempting to retrieve UserRole by name: {name}")
    #     if not hasattr(self.model, 'name'):
    #         logger.error(f"Model {self._model_name} does not have a 'name' attribute for get_role_by_name.")
    #         return None
    #     stmt = select(self.model).where(self.model.name == name) # type: ignore
    #     result = await self.db_session.execute(stmt)
    #     item_db = result.scalar_one_or_none()
    #     if item_db:
    #         logger.info(f"UserRole with name '{name}' found.")
    #         # Pydantic v1: return self.response_schema.from_orm(item_db)
    #         # Pydantic v2: return self.response_schema.model_validate(item_db)
    #         return self.response_schema.from_orm(item_db) # Assuming Pydantic v1 for now
    #     logger.info(f"UserRole with name '{name}' not found.")
    #     return None


logger.info("UserRoleService class defined.")
