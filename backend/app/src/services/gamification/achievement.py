# backend/app/src/services/gamification/achievement.py
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.gamification.achievement import UserAchievement # SQLAlchemy UserAchievement model
from app.src.models.gamification.badge import Badge # For badge context
from app.src.models.auth.user import User # For user context
from app.src.models.groups.group import Group # If achievements are group-contextual

from app.src.schemas.gamification.achievement import ( # Pydantic Schemas
    UserAchievementCreate, # Schema for awarding an achievement
    UserAchievementResponse
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class UserAchievementService(BaseService):
    """
    Service for managing user achievements (awarding badges to users).
    Handles creation and retrieval of UserAchievement records.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("UserAchievementService initialized.")

    async def award_achievement_to_user(
        self,
        user_id: UUID,
        badge_id: UUID,
        achievement_data: UserAchievementCreate,
        awarded_by_user_id: Optional[UUID] = None
    ) -> UserAchievementResponse:
        log_ctx = f"user ID '{user_id}', badge ID '{badge_id}'"
        # Use achievement_data.group_id if it exists, otherwise it's None
        group_id_from_data = getattr(achievement_data, 'group_id', None)
        if group_id_from_data: log_ctx += f", group ID '{group_id_from_data}'"
        logger.debug(f"Attempting to award achievement: {log_ctx}.")

        user = await self.db_session.get(User, user_id)
        if not user: raise ValueError(f"User with ID '{user_id}' not found.")

        badge = await self.db_session.get(Badge, badge_id)
        if not badge: raise ValueError(f"Badge with ID '{badge_id}' not found.")

        if group_id_from_data and hasattr(UserAchievement, 'group_id'): # Check if model supports group_id
            group = await self.db_session.get(Group, group_id_from_data)
            if not group: raise ValueError(f"Group with ID '{group_id_from_data}' not found.")
        elif group_id_from_data: # group_id provided in data, but model may not support it
             logger.warning(f"group_id '{group_id_from_data}' provided for achievement, but UserAchievement model might not support it. Will proceed without group linkage if so.")


        is_badge_repeatable = getattr(badge, 'is_repeatable', False)
        if not is_badge_repeatable:
            existing_achievement_stmt = select(UserAchievement.id).where( # Select only ID
                UserAchievement.user_id == user_id,
                UserAchievement.badge_id == badge_id
            )
            if hasattr(UserAchievement, 'group_id') and group_id_from_data:
                 existing_achievement_stmt = existing_achievement_stmt.where(UserAchievement.group_id == group_id_from_data)
            elif hasattr(UserAchievement, 'group_id'): # If model supports group_id, but none provided for this achievement, assume it's global
                 existing_achievement_stmt = existing_achievement_stmt.where(UserAchievement.group_id.is_(None)) # type: ignore

            if (await self.db_session.execute(existing_achievement_stmt)).scalar_one_or_none():
                logger.warning(f"User '{user_id}' has already been awarded non-repeatable badge '{badge.name}' (ID: {badge_id}) in this context.")
                raise ValueError(f"Badge '{badge.name}' has already been awarded to this user in this context and is not repeatable.")

        achievement_db_data = achievement_data.dict()

        final_create_data = {
            "user_id": user_id,
            "badge_id": badge_id,
            **achievement_db_data # Includes context and group_id if present in schema
        }
        if hasattr(UserAchievement, 'awarded_by_user_id') and awarded_by_user_id:
            final_create_data['awarded_by_user_id'] = awarded_by_user_id

        # Ensure group_id is only passed if model supports it
        if not hasattr(UserAchievement, 'group_id') and 'group_id' in final_create_data:
            del final_create_data['group_id']


        new_achievement_db = UserAchievement(**final_create_data)

        self.db_session.add(new_achievement_db)
        try:
            await self.commit()
            refresh_attrs = ['user', 'badge']
            if hasattr(UserAchievement, 'group') and new_achievement_db.group_id: refresh_attrs.append('group')
            if hasattr(UserAchievement, 'awarded_by') and new_achievement_db.awarded_by_user_id: refresh_attrs.append('awarded_by')
            await self.db_session.refresh(new_achievement_db, attribute_names=refresh_attrs)
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error awarding achievement ({log_ctx}): {e}", exc_info=True)
            raise ValueError(f"Could not award achievement due to a data conflict: {e}")

        logger.info(f"Achievement (Badge ID: '{badge_id}') awarded successfully to user ID '{user_id}'. Record ID: {new_achievement_db.id}")
        # return UserAchievementResponse.model_validate(new_achievement_db) # Pydantic v2
        return UserAchievementResponse.from_orm(new_achievement_db) # Pydantic v1

    async def get_user_achievement_by_id(self, achievement_id: UUID) -> Optional[UserAchievementResponse]:
        logger.debug(f"Attempting to retrieve user achievement by ID: {achievement_id}")

        stmt = select(UserAchievement).options(
            selectinload(UserAchievement.user).options(selectinload(User.user_type)),
            selectinload(UserAchievement.badge),
            selectinload(UserAchievement.group) if hasattr(UserAchievement, 'group') else None,
            selectinload(UserAchievement.awarded_by).options(selectinload(User.user_type)) if hasattr(UserAchievement, 'awarded_by') else None
        ).where(UserAchievement.id == achievement_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))

        achievement_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if achievement_db:
            logger.info(f"User achievement with ID '{achievement_id}' found.")
            # return UserAchievementResponse.model_validate(achievement_db) # Pydantic v2
            return UserAchievementResponse.from_orm(achievement_db) # Pydantic v1

        logger.info(f"User achievement with ID '{achievement_id}' not found.")
        return None

    async def list_achievements_for_user(
        self,
        user_id: UUID,
        group_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserAchievementResponse]:
        log_ctx = f"user ID '{user_id}'" + (f" in group ID '{group_id}'" if group_id and hasattr(UserAchievement, 'group_id') else "")
        logger.debug(f"Listing achievements for {log_ctx}, skip={skip}, limit={limit}")

        stmt = select(UserAchievement).options(
            selectinload(UserAchievement.user).options(selectinload(User.user_type)),
            selectinload(UserAchievement.badge),
            selectinload(UserAchievement.group) if hasattr(UserAchievement, 'group') else None,
            selectinload(UserAchievement.awarded_by).options(selectinload(User.user_type)) if hasattr(UserAchievement, 'awarded_by') else None
        ).where(UserAchievement.user_id == user_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))


        if hasattr(UserAchievement, 'group_id'):
            if group_id is not None: # Filter by specific group
                stmt = stmt.where(UserAchievement.group_id == group_id)
            # If group_id is None, list all for user (could be global or across all their groups if model is structured that way)
            # To list ONLY global when group_id is None: stmt = stmt.where(UserAchievement.group_id.is_(None))
        elif group_id is not None: # group_id provided but model doesn't support it
             logger.warning(f"group_id '{group_id}' provided for listing achievements, but UserAchievement model does not support it. Ignoring group filter.")


        stmt = stmt.order_by(UserAchievement.achieved_at.desc()).offset(skip).limit(limit)

        achievements_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # response_list = [UserAchievementResponse.model_validate(ach) for ach in achievements_db] # Pydantic v2
        response_list = [UserAchievementResponse.from_orm(ach) for ach in achievements_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} achievements for {log_ctx}.")
        return response_list

    async def list_users_for_badge(
        self,
        badge_id: UUID,
        group_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserAchievementResponse]:
        log_ctx = f"badge ID '{badge_id}'" + (f" in group ID '{group_id}'" if group_id and hasattr(UserAchievement, 'group_id') else "")
        logger.debug(f"Listing users who earned {log_ctx}, skip={skip}, limit={limit}")

        stmt = select(UserAchievement).options(
            selectinload(UserAchievement.user).options(selectinload(User.user_type)),
            selectinload(UserAchievement.badge),
            selectinload(UserAchievement.group) if hasattr(UserAchievement, 'group') else None,
            selectinload(UserAchievement.awarded_by).options(selectinload(User.user_type)) if hasattr(UserAchievement, 'awarded_by') else None
        ).where(UserAchievement.badge_id == badge_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))


        if hasattr(UserAchievement, 'group_id'):
            if group_id is not None:
                stmt = stmt.where(UserAchievement.group_id == group_id)
            # If group_id is None, list all users for this badge across all groups or globally.
            # To list ONLY global achievements for this badge: stmt = stmt.where(UserAchievement.group_id.is_(None))
        elif group_id is not None:
             logger.warning(f"group_id '{group_id}' provided for listing users for badge, but UserAchievement model does not support it. Ignoring group filter.")


        stmt = stmt.order_by(UserAchievement.achieved_at.desc()).offset(skip).limit(limit)
        achievements_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # response_list = [UserAchievementResponse.model_validate(ach) for ach in achievements_db] # Pydantic v2
        response_list = [UserAchievementResponse.from_orm(ach) for ach in achievements_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} users for {log_ctx}.")
        return response_list

logger.info("UserAchievementService class defined.")
