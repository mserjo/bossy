# backend/app/src/repositories/auth/user_repository.py

"""
Repository for User entities.
Provides CRUD operations and specific methods for managing user accounts.
"""

import logging
from typing import Optional, List, Any # Added List, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_ # Added or_

from backend.app.src.models.auth.user import User
from backend.app.src.schemas.auth.user import UserCreate, UserAdminUpdate # Using UserAdminUpdate for broader update capabilities by admin
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository[User, UserCreate, UserAdminUpdate]):
    """
    Repository for managing User records.
    """

    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        Retrieves a user by their email address.
        Email is expected to be unique.

        Args:
            db: The SQLAlchemy asynchronous database session.
            email: The email address of the user.

        Returns:
            The User object if found, otherwise None.
        """
        statement = select(self.model).where(self.model.email == email) # type: ignore[attr-defined]
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_phone_number(self, db: AsyncSession, *, phone_number: str) -> Optional[User]:
        """
        Retrieves a user by their phone number.
        Phone number is expected to be unique if provided.

        Args:
            db: The SQLAlchemy asynchronous database session.
            phone_number: The phone number of the user.

        Returns:
            The User object if found, otherwise None.
        """
        statement = select(self.model).where(self.model.phone_number == phone_number) # type: ignore[attr-defined]
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_email_or_phone(self, db: AsyncSession, *, email: Optional[str] = None, phone_number: Optional[str] = None) -> Optional[User]:
        """
        Retrieves a user by their email address OR phone number.
        Useful for login where user can use either.

        Args:
            db: The SQLAlchemy asynchronous database session.
            email: The email address of the user (optional).
            phone_number: The phone number of the user (optional).

        Returns:
            The User object if found by either identifier, otherwise None.
            Returns None if neither email nor phone_number is provided.
        """
        if not email and not phone_number:
            return None

        conditions = []
        if email:
            conditions.append(self.model.email == email) # type: ignore[attr-defined]
        if phone_number:
            conditions.append(self.model.phone_number == phone_number) # type: ignore[attr-defined]

        statement = select(self.model).where(or_(*conditions))
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    def is_active(self, user: User) -> bool:
        """
        Checks if a user account is active.

        Args:
            user: The User object.

        Returns:
            True if the user is active, False otherwise.
        """
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """
        Checks if a user has superuser privileges.

        Args:
            user: The User object.

        Returns:
            True if the user is a superuser, False otherwise.
        """
        return user.is_superuser

    async def search_users(
        self,
        db: AsyncSession,
        *,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Searches for users by a search term matching against email, name, first_name, or last_name.

        Args:
            db: The SQLAlchemy asynchronous database session.
            search_term: The term to search for.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A list of User objects matching the search criteria.
        """
        search_filter = f"%{search_term.lower()}%"
        conditions = or_(
            self.model.email.ilike(search_filter), # type: ignore[attr-defined]
            self.model.name.ilike(search_filter), # type: ignore[attr-defined]
            self.model.first_name.ilike(search_filter), # type: ignore[attr-defined]
            self.model.last_name.ilike(search_filter) # type: ignore[attr-defined]
        )

        statement = select(self.model).where(conditions).offset(skip).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())

    # Note: Password hashing is NOT handled here. It should be done in the service layer
    # before passing data to `create` or `update` methods.
    # The `create` and `update` methods inherited from BaseRepository will be used.
    # `UserCreate` schema is used for creation.
    # `UserAdminUpdate` schema is used for updates, allowing admins more control.
    # If user self-update needs a different, more restricted schema, a separate
    # repository method or service layer logic would enforce that.

    # Example of a more specific update method if needed:
    # async def update_profile(self, db: AsyncSession, *, db_obj: User, obj_in: UserUpdate) -> User:
    #     """
    #     Allows a user to update their own profile with restricted fields.
    #     """
    #     # This would call the base update method, but with UserUpdate schema
    #     return await super().update(db, db_obj=db_obj, obj_in=obj_in)
