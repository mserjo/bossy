# backend/app/src/services/system/initialization.py
import logging
from typing import Dict, Any, List, Type # Added Type for model_cls
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError # To catch potential duplicate key errors

from app.src.services.base import BaseService
# Assuming models and schemas for various entities to be initialized:
from app.src.models.auth.user import User
from app.src.models.dictionaries.user_roles import UserRole
from app.src.models.dictionaries.user_types import UserType
from app.src.models.dictionaries.group_types import GroupType
from app.src.models.dictionaries.task_types import TaskType
from app.src.models.dictionaries.bonus_types import BonusType
# from app.src.models.dictionaries.statuses import Status # If default statuses are needed

# For creating users, you might need password hashing utilities
from app.src.core.security import get_password_hash # Assuming this utility exists

# Pydantic schemas might be used if data comes from a config file, but here we define it directly.
# from app.src.schemas.auth.user import UserCreate # Example

# Initialize logger for this module
logger = logging.getLogger(__name__)

# --- Default Data Definitions ---
# These could also be loaded from a configuration file (e.g., YAML, JSON)

DEFAULT_USER_ROLES = [
    {"name": "Superuser", "code": "SUPERUSER", "description": "Full system access."},
    {"name": "Admin", "code": "ADMIN", "description": "Group administration access."},
    {"name": "User", "code": "USER", "description": "Standard user access within a group."},
]

DEFAULT_USER_TYPES = [
    {"name": "Superuser", "code": "SUPERUSER_TYPE", "description": "System superuser."},
    {"name": "Admin", "code": "ADMIN_TYPE", "description": "Group administrator."},
    {"name": "User", "code": "USER_TYPE", "description": "Regular platform user."},
    {"name": "Bot", "code": "BOT_TYPE", "description": "Automated system agent."},
]

DEFAULT_GROUP_TYPES = [
    {"name": "Family", "code": "FAMILY", "description": "For family groups."},
    {"name": "Department", "code": "DEPARTMENT", "description": "For work departments or teams."},
    {"name": "Organization", "code": "ORGANIZATION", "description": "For larger organizations."},
    {"name": "Friends", "code": "FRIENDS", "description": "For groups of friends."},
    {"name": "Project", "code": "PROJECT", "description": "For project-based groups."},
]

DEFAULT_TASK_TYPES = [
    {"name": "Regular Task", "code": "REGULAR", "description": "A standard task."},
    {"name": "Complex Task", "code": "COMPLEX", "description": "A task that might involve multiple steps or higher effort."},
    {"name": "Event", "code": "EVENT", "description": "A scheduled event or activity."},
    {"name": "Chore", "code": "CHORE", "description": "A recurring or routine task, often household-related."},
    {"name": "Reminder", "code": "REMINDER", "description": "A simple reminder item."},

]

DEFAULT_BONUS_TYPES = [
    {"name": "Standard Bonus", "code": "STANDARD_BONUS", "description": "A regular bonus point type."},
    {"name": "Achievement Bonus", "code": "ACHIEVEMENT_BONUS", "description": "Bonus awarded for specific achievements."},
    {"name": "Penalty", "code": "PENALTY_POINTS", "description": "Points deducted as a penalty."},
]

DEFAULT_SYSTEM_USERS = [
    {
        "username": "odin", "email": "odin@system.local", "password": "ChangeThisDefaultPasswordOdin!",
        "full_name": "Odin Superuser", "is_superuser": True, "is_active": True, "is_verified": True,
        "user_type_code": "SUPERUSER_TYPE", "user_role_codes": ["SUPERUSER"] # Assign role by code
    },
    {
        "username": "shadow", "email": "shadow@system.local", "password": "ChangeThisDefaultPasswordShadow!",
        "full_name": "Shadow System Bot", "is_superuser": False, "is_active": True, "is_verified": True, # Shadow may not be a superuser but a system bot
        "user_type_code": "BOT_TYPE", "user_role_codes": ["ADMIN"] # Example: Shadow might have admin rights for automated tasks
    },
    # As per technical_task.txt, 'root' was also mentioned. Adding it.
    {
        "username": "root", "email": "root@system.local", "password": "ChangeThisDefaultPasswordRoot!",
        "full_name": "Root Superuser", "is_superuser": True, "is_active": True, "is_verified": True,
        "user_type_code": "SUPERUSER_TYPE", "user_role_codes": ["SUPERUSER"]
    },
]


class InitialDataService(BaseService):
    """
    Service for initializing the system with default data.
    This includes creating predefined dictionary items (roles, types) and system users.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("InitialDataService initialized.")

    async def _initialize_dictionary(self, model_cls: Type[Any], defaults: List[Dict[str, Any]], code_field: str = "code") -> int:
        """
        Generic helper to initialize a dictionary table.
        Checks if items with default codes exist before creating.
        """
        count = 0
        for item_data in defaults:
            code = item_data.get(code_field)
            if not code:
                logger.warning(f"Skipping item in {model_cls.__name__} due to missing code: {item_data}")
                continue

            # Check if item with this code already exists
            stmt = select(model_cls).where(getattr(model_cls, code_field) == code)
            result = await self.db_session.execute(stmt)
            existing_item = result.scalar_one_or_none()

            if not existing_item:
                try:
                    new_item = model_cls(**item_data)
                    self.db_session.add(new_item)
                    await self.db_session.flush() # Flush to ensure it's in session for potential later reads within transaction
                    logger.info(f"Created {model_cls.__name__} '{item_data.get('name', code)}' with code '{code}'.")
                    count += 1
                except IntegrityError: # Should be rare due to prior check, but good for safety
                    await self.db_session.rollback() # Rollback the specific failed add
                    logger.warning(f"IntegrityError while creating {model_cls.__name__} with code '{code}'. Item might have been created concurrently. Skipping.")
                except Exception as e:
                    await self.db_session.rollback()
                    logger.error(f"Error creating {model_cls.__name__} '{item_data.get('name', code)}': {e}", exc_info=True)
            else:
                logger.info(f"{model_cls.__name__} with code '{code}' already exists. Skipping.")
        return count

    async def initialize_user_roles(self) -> int:
        """Initializes default user roles."""
        logger.info("Initializing default user roles...")
        created_count = await self._initialize_dictionary(UserRole, DEFAULT_USER_ROLES)
        logger.info(f"Finished initializing user roles. Created {created_count} new roles.")
        return created_count

    async def initialize_user_types(self) -> int:
        """Initializes default user types."""
        logger.info("Initializing default user types...")
        created_count = await self._initialize_dictionary(UserType, DEFAULT_USER_TYPES)
        logger.info(f"Finished initializing user types. Created {created_count} new types.")
        return created_count

    async def initialize_group_types(self) -> int:
        """Initializes default group types."""
        logger.info("Initializing default group types...")
        created_count = await self._initialize_dictionary(GroupType, DEFAULT_GROUP_TYPES)
        logger.info(f"Finished initializing group types. Created {created_count} new types.")
        return created_count

    async def initialize_task_types(self) -> int:
        """Initializes default task types."""
        logger.info("Initializing default task types...")
        created_count = await self._initialize_dictionary(TaskType, DEFAULT_TASK_TYPES)
        logger.info(f"Finished initializing task types. Created {created_count} new types.")
        return created_count

    async def initialize_bonus_types(self) -> int:
        """Initializes default bonus types."""
        logger.info("Initializing default bonus types...")
        created_count = await self._initialize_dictionary(BonusType, DEFAULT_BONUS_TYPES)
        logger.info(f"Finished initializing bonus types. Created {created_count} new types.")
        return created_count

    async def initialize_system_users(self) -> int:
        """
        Initializes default system users (odin, shadow, root).
        Requires UserType and UserRole to be initialized first.
        """
        logger.info("Initializing default system users...")
        created_count = 0
        for user_data in DEFAULT_SYSTEM_USERS:
            username = user_data["username"]
            email = user_data["email"]

            # Check if user already exists by username or email
            stmt_username = select(User).where(User.username == username)
            stmt_email = select(User).where(User.email == email)

            existing_by_username = (await self.db_session.execute(stmt_username)).scalar_one_or_none()
            existing_by_email = (await self.db_session.execute(stmt_email)).scalar_one_or_none()

            if existing_by_username:
                logger.info(f"System user '{username}' already exists. Skipping.")
                continue
            if existing_by_email: # Should ideally not happen if username is also unique
                logger.info(f"System user with email '{email}' (intended for '{username}') already exists. Skipping.")
                continue

            try:
                # Fetch UserType by code
                user_type_code = user_data["user_type_code"]
                type_stmt = select(UserType).where(UserType.code == user_type_code)
                user_type = (await self.db_session.execute(type_stmt)).scalar_one_or_none()
                if not user_type:
                    logger.error(f"UserType with code '{user_type_code}' not found for system user '{username}'. Skipping.")
                    continue

                # Fetch UserRoles by codes
                user_role_codes = user_data.get("user_role_codes", [])
                roles_stmt = select(UserRole).where(UserRole.code.in_(user_role_codes))
                user_roles_db = (await self.db_session.execute(roles_stmt)).scalars().all()

                if len(user_roles_db) != len(user_role_codes):
                    found_codes = [r.code for r in user_roles_db]
                    missing_codes = [code for code in user_role_codes if code not in found_codes]
                    logger.warning(f"Not all roles found for system user '{username}'. Found: {found_codes}, Missing: {missing_codes}. User will be created with found roles.")
                    # Decide if this is critical or if user can be created with available roles

                hashed_password = get_password_hash(user_data["password"])

                new_user_db = User(
                    username=username,
                    email=email,
                    hashed_password=hashed_password,
                    full_name=user_data.get("full_name"),
                    is_active=user_data.get("is_active", True),
                    is_superuser=user_data.get("is_superuser", False),
                    is_verified=user_data.get("is_verified", True), # System users are typically pre-verified
                    user_type_id=user_type.id, # Link to UserType via ID
                    # user_type = user_type # If relationship is set up to take the object
                    roles=user_roles_db # Assign UserRole objects to the relationship
                )
                self.db_session.add(new_user_db)
                await self.db_session.flush() # Flush to get ID for logging if needed
                logger.info(f"System user '{username}' created successfully with ID {new_user_db.id}.")
                created_count += 1
            except IntegrityError: # Should be rare due to prior checks
                await self.db_session.rollback()
                logger.warning(f"IntegrityError while creating system user '{username}'. User might have been created concurrently. Skipping.")
            except Exception as e:
                await self.db_session.rollback()
                logger.error(f"Error creating system user '{username}': {e}", exc_info=True)

        logger.info(f"Finished initializing system users. Created {created_count} new users.")
        return created_count

    async def run_full_initialization(self, force_users: bool = False) -> Dict[str, int]:
        """
        Runs all initialization methods in the correct order.
        Commits changes at the end of all successful initializations.
        If any step fails critically, it should ideally roll back the entire transaction.
        The BaseService commit/rollback are per-call, so a transaction block might be needed here.
        For simplicity, each sub-initializer will attempt its own commit for now,
        but a single transaction for all initializers is better.

        Args:
            force_users (bool): If true, attempts to create users even if other initializations are skipped.
                                (Not fully implemented here, as user creation depends on roles/types).

        Returns:
            Dict[str, int]: A dictionary palavras_chave counts of created items per category.
        """
        logger.info("Starting full system data initialization...")
        # This method should ideally be wrapped in a single transaction.
        # However, BaseService.commit() is called by sub-methods.
        # For true atomicity, remove commits from sub-methods and commit here once.
        # Or, make sub-methods accept a 'commit_on_complete=False' flag.
        # For now, we proceed with sub-methods committing after each category.

        results = {}
        try:
            results["user_roles"] = await self.initialize_user_roles()
            await self.commit() # Commit after user roles

            results["user_types"] = await self.initialize_user_types()
            await self.commit() # Commit after user types

            results["group_types"] = await self.initialize_group_types()
            await self.commit() # Commit after group types

            results["task_types"] = await self.initialize_task_types()
            await self.commit() # Commit after task types

            results["bonus_types"] = await self.initialize_bonus_types()
            await self.commit() # Commit after bonus types

            # System users depend on roles and types being present
            # Check if dependent roles/types exist or if force_users is True
            essential_data_exists = await self._check_roles_types_exist()
            if force_users or essential_data_exists:
                 results["system_users"] = await self.initialize_system_users()
                 await self.commit() # Commit after system users
            else:
                logger.warning("Skipping system user initialization as essential roles/types may not exist and force_users is False.")
                results["system_users"] = 0

            logger.info("Full system data initialization completed successfully.")

        except Exception as e:
            logger.error(f"Full system data initialization failed during one of the steps: {e}", exc_info=True)
            await self.rollback() # Rollback any changes from the current transaction scope
            # Re-raise or handle as per application's error policy
            raise
        return results

    async def _check_roles_types_exist(self) -> bool:
        """Helper to check if essential roles and types exist for user creation."""
        # Check for a superuser role and type by code
        su_role_stmt = select(UserRole).where(UserRole.code == "SUPERUSER")
        su_type_stmt = select(UserType).where(UserType.code == "SUPERUSER_TYPE")
        bot_type_stmt = select(UserType).where(UserType.code == "BOT_TYPE")
        admin_role_stmt = select(UserRole).where(UserRole.code == "ADMIN")


        su_role_exists = (await self.db_session.execute(su_role_stmt)).scalar_one_or_none() is not None
        su_type_exists = (await self.db_session.execute(su_type_stmt)).scalar_one_or_none() is not None
        bot_type_exists = (await self.db_session.execute(bot_type_stmt)).scalar_one_or_none() is not None
        admin_role_exists = (await self.db_session.execute(admin_role_stmt)).scalar_one_or_none() is not None

        if not all([su_role_exists, su_type_exists, bot_type_exists, admin_role_exists]):
            logger.warning(f"Essential roles/types check: SuperUserRole: {su_role_exists}, SuperUserType: {su_type_exists}, BotUserType: {bot_type_exists}, AdminRole: {admin_role_exists}")
            return False
        return True


logger.info("InitialDataService class defined.")
