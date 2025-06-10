# backend/app/src/services/gamification/user_level.py
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal # For current_points_value

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.gamification.user_level import UserLevel # SQLAlchemy UserLevel model
from app.src.models.gamification.level import Level # For Level definitions
from app.src.models.auth.user import User
from app.src.models.groups.group import Group # If levels are per-group

from app.src.schemas.gamification.user_level import ( # Pydantic Schemas
    UserLevelResponse
)
from app.src.schemas.gamification.level import LevelResponse # For nested level details

# Initialize logger for this module
logger = logging.getLogger(__name__)

class UserLevelService(BaseService):
    """
    Service for managing users' levels based on their accumulated points or achievements.
    Handles calculation and updates of UserLevel records.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("UserLevelService initialized.")

    async def get_user_level(
        self,
        user_id: UUID,
        group_id: Optional[UUID] = None
    ) -> Optional[UserLevelResponse]:
        log_ctx = f"user ID '{user_id}'" + (f" in group ID '{group_id}'" if group_id and hasattr(UserLevel, 'group_id') else " (global)")
        logger.debug(f"Attempting to retrieve UserLevel for {log_ctx}.")

        stmt = select(UserLevel).options(
            selectinload(UserLevel.user).options(selectinload(User.user_type)),
            selectinload(UserLevel.level),
            selectinload(UserLevel.group) if hasattr(UserLevel, 'group') else None
        ).where(UserLevel.user_id == user_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))


        if hasattr(UserLevel, 'group_id'):
            stmt = stmt.where(UserLevel.group_id == group_id)
        elif group_id:
            logger.warning(f"UserLevel model does not have 'group_id', but one was provided for {log_ctx}. Ignoring group context for UserLevel retrieval.")

        user_level_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if user_level_db:
            level_name = getattr(getattr(user_level_db, 'level', None), 'name', 'N/A')
            logger.info(f"UserLevel record found for {log_ctx} (Level: {level_name}).")
            # return UserLevelResponse.model_validate(user_level_db) # Pydantic v2
            return UserLevelResponse.from_orm(user_level_db) # Pydantic v1

        logger.info(f"No UserLevel record found for {log_ctx}.")
        return None

    async def update_user_level(
        self,
        user_id: UUID,
        group_id: Optional[UUID] = None,
    ) -> Optional[UserLevelResponse]:
        log_ctx = f"user ID '{user_id}'" + (f" in group ID '{group_id}'" if group_id and hasattr(UserLevel, 'group_id') else " (global)")
        logger.info(f"Attempting to update level for {log_ctx}.")

        from app.src.services.bonuses.account import UserAccountService
        account_service = UserAccountService(self.db_session)

        user_account = await account_service.get_user_account(user_id, group_id=group_id)
        if not user_account:
            logger.warning(f"No bonus account found for {log_ctx}. Assuming 0 points for level update.")
            current_points_value = Decimal("0.0")
        else:
            current_points_value = user_account.balance

        logger.info(f"Current points for {log_ctx}: {current_points_value}")

        from app.src.services.gamification.level import LevelService
        level_service = LevelService(self.db_session)

        target_level_schema: Optional[LevelResponse] = await level_service.get_level_for_points(int(current_points_value))

        # Determine current UserLevel record query conditions
        user_level_conditions = [UserLevel.user_id == user_id]
        if hasattr(UserLevel, 'group_id'):
            user_level_conditions.append(UserLevel.group_id == group_id)

        existing_user_level_db = (await self.db_session.execute(
            select(UserLevel).where(*user_level_conditions)
        )).scalar_one_or_none()

        if not target_level_schema: # No level for current points (e.g. below minimum)
            logger.info(f"No specific level defined for {current_points_value} points for {log_ctx}.")
            if existing_user_level_db:
                logger.info(f"User {log_ctx} has {current_points_value} points, falling below any defined level. Deleting existing UserLevel record ID {existing_user_level_db.id}.")
                await self.db_session.delete(existing_user_level_db)
                await self.commit()
            return None # No level assigned or existing one removed

        # Target level identified
        if existing_user_level_db:
            if existing_user_level_db.level_id == target_level_schema.id:
                logger.info(f"User {log_ctx} is already at the correct level: '{target_level_schema.name}'. No update needed.")
                return await self.get_user_level(user_id, group_id)
            else:
                logger.info(f"Updating level for {log_ctx} from ID '{existing_user_level_db.level_id}' to new Level ID '{target_level_schema.id}' ('{target_level_schema.name}').")
                existing_user_level_db.level_id = target_level_schema.id
                existing_user_level_db.achieved_at = datetime.now(timezone.utc)
                user_level_to_save = existing_user_level_db
        else:
            logger.info(f"Creating new UserLevel record for {log_ctx} at Level ID '{target_level_schema.id}' ('{target_level_schema.name}').")
            user_level_data = {
                "user_id": user_id,
                "level_id": target_level_schema.id,
                "achieved_at": datetime.now(timezone.utc),
            }
            if hasattr(UserLevel, 'group_id'):
                user_level_data['group_id'] = group_id

            user_level_to_save = UserLevel(**user_level_data)
            self.db_session.add(user_level_to_save)

        try:
            await self.commit()
            # Refresh to load all relationships for the response
            refresh_attrs = ['user', 'level']
            if hasattr(UserLevel, 'group') and group_id: # Only refresh group if it's relevant and was set
                 refresh_attrs.append('group')
            await self.db_session.refresh(user_level_to_save, attribute_names=refresh_attrs)
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error updating/creating UserLevel for {log_ctx}: {e}", exc_info=True)
            raise ValueError(f"Could not update/create UserLevel due to data conflict: {e}")

        logger.info(f"UserLevel for {log_ctx} successfully set to Level '{target_level_schema.name}'.")
        # return UserLevelResponse.model_validate(user_level_to_save) # Pydantic v2
        return UserLevelResponse.from_orm(user_level_to_save) # Pydantic v1

    async def list_users_at_level(
        self,
        level_id: UUID,
        group_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserLevelResponse]:
        log_ctx = f"level ID '{level_id}'" + (f" in group ID '{group_id}'" if group_id and hasattr(UserLevel, 'group_id') else " (global)")
        logger.debug(f"Listing users at {log_ctx}, skip={skip}, limit={limit}.")

        stmt = select(UserLevel).options(
            selectinload(UserLevel.user).options(selectinload(User.user_type)),
            selectinload(UserLevel.level),
            selectinload(UserLevel.group) if hasattr(UserLevel, 'group') else None
        ).where(UserLevel.level_id == level_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))


        if hasattr(UserLevel, 'group_id'):
            stmt = stmt.where(UserLevel.group_id == group_id)
        elif group_id:
             logger.warning(f"UserLevel model does not have 'group_id', but one was provided for listing. Ignoring group context.")

        stmt = stmt.order_by(UserLevel.achieved_at.desc()).offset(skip).limit(limit)

        user_levels_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # response_list = [UserLevelResponse.model_validate(ul) for ul in user_levels_db] # Pydantic v2
        response_list = [UserLevelResponse.from_orm(ul) for ul in user_levels_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} users at {log_ctx}.")
        return response_list

logger.info("UserLevelService class defined.")
