# backend/app/src/services/auth/user.py
import logging
from typing import List, Optional, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload # For eager loading relationships like roles
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.auth.user import User # SQLAlchemy User model
from app.src.models.dictionaries.user_roles import UserRole # For assigning roles
from app.src.models.dictionaries.user_types import UserType # For assigning user type
from app.src.schemas.auth.user import ( # Pydantic User schemas
    UserCreate,
    UserUpdate,
    UserResponse, # Base response without roles, might be used internally or for specific endpoints
    UserResponseWithRoles, # Assuming a schema that includes roles
    # UserCreateSuperuser # Specific schema for superuser creation by admin - can be handled by create_user with flags
)
# Assuming PasswordService will be available for hashing passwords
# from .password import PasswordService # Circular dependency if PasswordService also imports UserService
# For now, assume password hashing is done before calling user service or by a direct utility import
from app.src.core.security import get_password_hash # Direct utility import

# Initialize logger for this module
logger = logging.getLogger(__name__)

class UserService(BaseService):
    """
    Service for managing users, including creation, profile updates,
    role assignments, and administrative actions.
    """

    def __init__(self, db_session: AsyncSession): # Add other dependent services if needed
        super().__init__(db_session)
        # self.password_service = PasswordService() # If PasswordService is stateless and needed
        logger.info("UserService initialized.")

    async def get_user_by_id(self, user_id: UUID, include_roles: bool = True) -> Optional[UserResponse]: # Returns base or with roles
        """
        Retrieves a user by their ID.
        Optionally includes their roles based on include_roles flag.
        """
        logger.debug(f"Attempting to retrieve user by ID: {user_id}, include_roles: {include_roles}")
        query = select(User)
        if include_roles:
            query = query.options(selectinload(User.roles))
        stmt = query.where(User.id == user_id)

        result = await self.db_session.execute(stmt)
        user_db = result.scalar_one_or_none()

        if user_db:
            logger.info(f"User with ID '{user_id}' found.")
            if include_roles:
                # return UserResponseWithRoles.model_validate(user_db) # Pydantic v2
                return UserResponseWithRoles.from_orm(user_db) # Pydantic v1
            # return UserResponse.model_validate(user_db) # Pydantic v2
            return UserResponse.from_orm(user_db) # Pydantic v1

        logger.info(f"User with ID '{user_id}' not found.")
        return None

    async def get_user_by_email(self, email: str, include_roles: bool = True) -> Optional[UserResponse]:
        """
        Retrieves a user by their email address.
        Optionally includes their roles.
        """
        logger.debug(f"Attempting to retrieve user by email: {email}, include_roles: {include_roles}")
        query = select(User)
        if include_roles:
            query = query.options(selectinload(User.roles))
        stmt = query.where(User.email == email.lower())

        result = await self.db_session.execute(stmt)
        user_db = result.scalar_one_or_none()

        if user_db:
            logger.info(f"User with email '{email}' found.")
            if include_roles:
                # return UserResponseWithRoles.model_validate(user_db) # Pydantic v2
                return UserResponseWithRoles.from_orm(user_db) # Pydantic v1
            # return UserResponse.model_validate(user_db) # Pydantic v2
            return UserResponse.from_orm(user_db) # Pydantic v1
        logger.info(f"User with email '{email}' not found.")
        return None

    async def get_user_by_username(self, username: str, include_roles: bool = True) -> Optional[UserResponse]:
        """
        Retrieves a user by their username.
        Optionally includes their roles.
        """
        logger.debug(f"Attempting to retrieve user by username: {username}, include_roles: {include_roles}")
        query = select(User)
        if include_roles:
            query = query.options(selectinload(User.roles))
        stmt = query.where(User.username == username)

        result = await self.db_session.execute(stmt)
        user_db = result.scalar_one_or_none()

        if user_db:
            logger.info(f"User with username '{username}' found.")
            if include_roles:
                # return UserResponseWithRoles.model_validate(user_db) # Pydantic v2
                return UserResponseWithRoles.from_orm(user_db) # Pydantic v1
            # return UserResponse.model_validate(user_db) # Pydantic v2
            return UserResponse.from_orm(user_db) # Pydantic v1
        logger.info(f"User with username '{username}' not found.")
        return None

    async def create_user(self, user_create_data: UserCreate,
                          user_type_code: str = "USER_TYPE",
                          role_codes: Optional[List[str]] = None,
                          is_superuser_creation: bool = False # Flag for superuser specific logic if any
                         ) -> UserResponseWithRoles:
        """
        Creates a new user.
        Handles password hashing and assignment of user type and roles.
        """
        logger.debug(f"Attempting to create new user: {user_create_data.username}, superuser_creation: {is_superuser_creation}")

        # Check for existing user by username or email
        # Pass include_roles=False as roles are not needed for this existence check
        if await self.get_user_by_username(user_create_data.username, include_roles=False):
            logger.warning(f"Username '{user_create_data.username}' already exists.")
            raise ValueError(f"Username '{user_create_data.username}' already exists.")
        if await self.get_user_by_email(user_create_data.email, include_roles=False):
            logger.warning(f"Email '{user_create_data.email}' already registered.")
            raise ValueError(f"Email '{user_create_data.email}' already registered.")

        hashed_password = get_password_hash(user_create_data.password)

        type_stmt = select(UserType).where(UserType.code == user_type_code)
        user_type_db = (await self.db_session.execute(type_stmt)).scalar_one_or_none()
        if not user_type_db:
            logger.error(f"UserType with code '{user_type_code}' not found. Cannot create user '{user_create_data.username}'.")
            raise ValueError(f"UserType '{user_type_code}' not found. User creation failed.")

        # user_db_data = user_create_data.model_dump(exclude={"password"}) # Pydantic v2
        user_db_data = user_create_data.dict(exclude={"password"}) # Pydantic v1

        new_user_db = User(
            **user_db_data,
            hashed_password=hashed_password,
            user_type_id=user_type_db.id,
            email=user_create_data.email.lower(), # Ensure email is stored in lowercase
            is_superuser=is_superuser_creation
        )

        if role_codes:
            roles_stmt = select(UserRole).where(UserRole.code.in_(role_codes))
            user_roles_db = (await self.db_session.execute(roles_stmt)).scalars().all()
            if user_roles_db:
                new_user_db.roles = user_roles_db # Assign list of role objects
            else:
                logger.warning(f"Specified roles with codes {role_codes} not found for new user '{user_create_data.username}'. User will have no roles.")

        self.db_session.add(new_user_db)
        try:
            await self.commit() # BaseService commit
            await self.db_session.refresh(new_user_db)
            # Eager load roles for the response, even if roles list was empty initially
            await self.db_session.refresh(new_user_db, attribute_names=['roles'])
        except IntegrityError as e:
            await self.rollback() # BaseService rollback
            logger.error(f"Integrity error creating user '{user_create_data.username}': {e}", exc_info=True)
            # Convert IntegrityError to a more specific ValueError for the client
            # Check for common unique constraint violation texts (adapt to your DB if needed)
            err_str = str(e).lower()
            if "users_username_key" in err_str or "unique_username" in err_str or "constraint failed: users.username" in err_str :
                 raise ValueError(f"Username '{user_create_data.username}' already exists.")
            if "users_email_key" in err_str or "unique_email" in err_str or "constraint failed: users.email" in err_str:
                 raise ValueError(f"Email '{user_create_data.email}' already registered.")
            raise ValueError(f"Could not create user due to a data conflict: {e}") # Generic conflict

        logger.info(f"User '{new_user_db.username}' (ID: {new_user_db.id}) created successfully.")
        # return UserResponseWithRoles.model_validate(new_user_db) # Pydantic v2
        return UserResponseWithRoles.from_orm(new_user_db) # Pydantic v1

    async def update_user(self, user_id: UUID, user_update_data: UserUpdate) -> Optional[UserResponseWithRoles]:
        """Updates a user's profile information. Password updates should use a dedicated password service method."""
        logger.debug(f"Attempting to update user ID: {user_id}")

        user_db = await self._get_user_model_by_id(user_id) # This helper already loads roles
        if not user_db:
            logger.warning(f"User ID '{user_id}' not found for update.")
            return None

        # update_data = user_update_data.model_dump(exclude_unset=True) # Pydantic v2
        update_data = user_update_data.dict(exclude_unset=True) # Pydantic v1

        if 'email' in update_data and update_data['email'].lower() != user_db.email:
            new_email = update_data['email'].lower()
            # Check if new email is taken by another user
            existing_email_user_stmt = select(User).where(User.email == new_email, User.id != user_id)
            if (await self.db_session.execute(existing_email_user_stmt)).scalar_one_or_none():
                logger.warning(f"Cannot update email for user ID '{user_id}' to '{new_email}': email already in use.")
                raise ValueError(f"Email '{new_email}' is already registered to another user.")
            user_db.email = new_email
            # Email change implies re-verification unless 'is_verified' is explicitly part of the update
            if 'is_verified' not in update_data:
                 user_db.is_verified = False
                 logger.info(f"User ID '{user_id}' email changed. Marked as unverified pending re-verification.")

        for field, value in update_data.items():
            if field == 'email': continue # Already handled
            if hasattr(user_db, field): # Check if the field exists on the model
                setattr(user_db, field, value)
            else:
                logger.warning(f"Field '{field}' not found on User model during update of user ID '{user_id}'. Skipping field.")

        self.db_session.add(user_db)
        await self.commit()
        await self.db_session.refresh(user_db)
        # Ensure roles are loaded for the response, _get_user_model_by_id should have done this
        # but an explicit refresh here ensures it if the instance was modified in a way that detaches roles.
        await self.db_session.refresh(user_db, attribute_names=['roles'])

        logger.info(f"User ID '{user_id}' updated successfully.")
        # return UserResponseWithRoles.model_validate(user_db) # Pydantic v2
        return UserResponseWithRoles.from_orm(user_db) # Pydantic v1

    async def _get_user_model_by_id(self, user_id: UUID) -> Optional[User]:
        """Internal helper to fetch the User ORM model instance by ID, with roles eagerly loaded."""
        stmt = select(User).options(selectinload(User.roles)).where(User.id == user_id)
        return (await self.db_session.execute(stmt)).scalar_one_or_none()

    async def assign_roles_to_user(self, user_id: UUID, role_codes: List[str], replace_existing: bool = False) -> Optional[UserResponseWithRoles]:
        """Assigns one or more roles to a user by role codes."""
        logger.debug(f"Assigning roles {role_codes} to user ID {user_id}. Replace existing: {replace_existing}")
        user_db = await self._get_user_model_by_id(user_id)
        if not user_db:
            logger.warning(f"User ID '{user_id}' not found for role assignment.")
            return None

        roles_stmt = select(UserRole).where(UserRole.code.in_(role_codes))
        roles_to_assign_db = (await self.db_session.execute(roles_stmt)).scalars().all()

        if not roles_to_assign_db:
            logger.warning(f"No valid roles found for codes {role_codes} for user ID '{user_id}'. No roles changed if replacing, or no new roles added.")
            if not replace_existing and not user_db.roles: # If not replacing and user has no roles, effectively no change
                 return UserResponseWithRoles.from_orm(user_db)
            # If replacing and no valid roles found, roles list becomes empty
            # If not replacing but some roles were expected, this path is fine, user_db.roles remains as is or gets non-found roles filtered out below.

        if replace_existing:
            user_db.roles = roles_to_assign_db
        else:
            # Add new roles, ensuring no duplicates based on object identity (if already loaded) or ID.
            current_role_ids = {role.id for role in user_db.roles}
            for role in roles_to_assign_db:
                if role.id not in current_role_ids:
                    user_db.roles.append(role)

        self.db_session.add(user_db) # Mark user_db as dirty due to relationship change
        await self.commit()
        # Refresh to ensure the session has the latest state, especially for relationships
        await self.db_session.refresh(user_db, attribute_names=['roles'])
        logger.info(f"Roles updated for user ID '{user_id}'. Current roles: {[r.code for r in user_db.roles]}.")
        # return UserResponseWithRoles.model_validate(user_db) # Pydantic v2
        return UserResponseWithRoles.from_orm(user_db) # Pydantic v1

    async def remove_roles_from_user(self, user_id: UUID, role_codes: List[str]) -> Optional[UserResponseWithRoles]:
        """Removes one or more roles from a user by role codes."""
        logger.debug(f"Removing roles {role_codes} from user ID {user_id}")
        user_db = await self._get_user_model_by_id(user_id)
        if not user_db:
            logger.warning(f"User ID '{user_id}' not found for role removal.")
            return None

        if not user_db.roles: # No roles to remove
            logger.info(f"User ID '{user_id}' has no roles. No roles removed.")
            # return UserResponseWithRoles.model_validate(user_db) # Pydantic v2
            return UserResponseWithRoles.from_orm(user_db) # Pydantic v1

        initial_role_count = len(user_db.roles)
        # Filter out roles to be removed
        user_db.roles = [role for role in user_db.roles if role.code not in role_codes]

        if len(user_db.roles) < initial_role_count:
            self.db_session.add(user_db) # Mark as dirty
            await self.commit()
            await self.db_session.refresh(user_db, attribute_names=['roles'])
            logger.info(f"Roles matching {role_codes} removed from user ID '{user_id}'.")
        else:
            logger.info(f"No roles matching codes {role_codes} found on user ID '{user_id}'. No changes made.")

        # return UserResponseWithRoles.model_validate(user_db) # Pydantic v2
        return UserResponseWithRoles.from_orm(user_db) # Pydantic v1

    async def list_users(self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[UserResponseWithRoles]:
        """(Admin/Superuser) Lists users with pagination and optional active status filter."""
        logger.debug(f"Listing users: skip={skip}, limit={limit}, is_active={is_active}")
        stmt = select(User).options(selectinload(User.roles))
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        stmt = stmt.order_by(User.username).offset(skip).limit(limit)

        result = await self.db_session.execute(stmt)
        users_db = result.scalars().all()

        # response_list = [UserResponseWithRoles.model_validate(user) for user in users_db] # Pydantic v2
        response_list = [UserResponseWithRoles.from_orm(user) for user in users_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} users.")
        return response_list

logger.info("UserService class defined.")
