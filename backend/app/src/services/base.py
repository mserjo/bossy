# backend/app/src/services/base.py
import logging
from typing import TypeVar, Generic, Optional, Any # Added Any for get_object_or_none example
from uuid import UUID # Added for get_object_or_none example
# Assuming asynchronous operations with SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession

# For repository pattern, if used (example, replace with actual base repository if available)
# from app.src.repositories.base import BaseRepository # Placeholder

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Generic type for the repository, if we were to use one.
# RepositoryType = TypeVar("RepositoryType", bound=BaseRepository) # Placeholder

class BaseService(Generic): # Add RepositoryType if using generic repository: class BaseService(Generic[RepositoryType]):
    """
    Base class for all services.
    Provides common functionalities and dependencies for service classes,
    such as a database session.

    Services are responsible for encapsulating business logic and coordinating
    data access through repositories (if the repository pattern is used) or directly
    via ORM/database sessions.

    Attributes:
        db_session (AsyncSession): The SQLAlchemy asynchronous database session.
        # repo (RepositoryType): An instance of a repository specific to the service's domain.
                                 # This is commented out as per the decision to start with just the session.
    """

    def __init__(self, db_session: AsyncSession): # Add repo: RepositoryType = None if using generic repo
        """
        Initializes the BaseService with a database session.

        Args:
            db_session (AsyncSession): The SQLAlchemy asynchronous database session
                                       to be used for database operations.
            # repo (RepositoryType, optional): An instance of a repository.
            #                                 Defaults to None. If provided, it will be used
            #                                 for data access.
        """
        if db_session is None:
            # This check is crucial. Services should not operate without a db session.
            logger.error("BaseService initialized without a database session. This is not allowed.")
            raise ValueError("Database session cannot be None for BaseService.")

        self.db_session: AsyncSession = db_session
        # self.repo: Optional[RepositoryType] = repo # Uncomment if repository is used

        logger.debug(
            f"{self.__class__.__name__} initialized with DB session ID: {id(db_session)}"
            # Add {f"and repository: {type(repo).__name__}" if repo else ''} if repo is used
        )

    async def commit(self) -> None:
        """
        Commits the current database session.
        Logs the action and handles potential exceptions during commit.
        """
        try:
            await self.db_session.commit()
            logger.info(f"Database session {id(self.db_session)} committed successfully by {self.__class__.__name__}.")
        except Exception as e:
            logger.error(f"Error committing database session {id(self.db_session)} in {self.__class__.__name__}: {e}", exc_info=True)
            # Depending on error handling strategy, you might want to rollback here or raise the exception.
            # For now, just logging and re-raising to let the caller handle it or global exception handlers.
            await self.rollback() # Attempt a rollback on commit error
            raise

    async def rollback(self) -> None:
        """
        Rolls back the current database session.
        Logs the action and handles potential exceptions during rollback.
        """
        try:
            await self.db_session.rollback()
            logger.warning(f"Database session {id(self.db_session)} rolled back by {self.__class__.__name__}.")
        except Exception as e:
            logger.error(f"Error rolling back database session {id(self.db_session)} in {self.__class__.__name__}: {e}", exc_info=True)
            # If rollback fails, the session might be in an inconsistent state.
            # This is a critical error.
            raise

    # Example of a common utility method that might be useful in services
    # async def get_object_or_none(self, model_cls, object_id: UUID) -> Optional[Any]:
    #     """
    #     Fetches an object by its ID, returning None if not found.
    #     This would typically use self.repo if repository pattern is active,
    #     or self.db_session directly with SQLAlchemy queries.
    #     """
    #     logger.debug(f"Attempting to fetch {model_cls.__name__} with ID: {object_id}")
    #     # Example with direct session usage (replace with actual query)
    #     # from sqlalchemy.future import select
    #     # stmt = select(model_cls).where(model_cls.id == object_id)
    #     # result = await self.db_session.execute(stmt)
    #     # instance = result.scalar_one_or_none()
    #     # if instance:
    #     #     logger.info(f"Found {model_cls.__name__} with ID: {object_id}")
    #     # else:
    #     #     logger.info(f"{model_cls.__name__} with ID: {object_id} not found.")
    #     # return instance
    #     pass # Placeholder

logger.info("BaseService class defined successfully.")

# Example of how a specific service would inherit from BaseService:
#
# from app.src.models.user import User # Assuming a User model
# from app.src.repositories.user_repository import UserRepository # Assuming a UserRepository
#
# class UserService(BaseService[UserRepository]):
#     def __init__(self, db_session: AsyncSession, user_repo: UserRepository):
#         super().__init__(db_session, repo=user_repo)
#         logger.info("UserService initialized.")
#
#     async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
#         """Get a user by their ID."""
#         return await self.repo.get_by_id(user_id)
#
#     # ... other user-specific service methods ...
