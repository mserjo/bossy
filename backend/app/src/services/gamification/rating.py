# backend/app/src/services/gamification/rating.py
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, date # Added date for potential period calculations
from decimal import Decimal # For scores

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func # For aggregations like sum, rank

from app.src.services.base import BaseService
from app.src.models.gamification.rating import UserGroupRating # SQLAlchemy UserGroupRating model
from app.src.models.auth.user import User
from app.src.models.groups.group import Group
# from app.src.models.bonuses.account import UserAccount # To get user's total points for rating

from app.src.schemas.gamification.rating import ( # Pydantic Schemas
    UserGroupRatingResponse,
    GroupLeaderboardResponse # For returning leaderboard data
    # UserGroupRatingCreate, UserGroupRatingUpdate - ratings are usually calculated, not directly CRUDed
)
# from app.src.services.bonuses.account import UserAccountService # For fetching user points

# Initialize logger for this module
logger = logging.getLogger(__name__)

class UserRatingService(BaseService):
    """
    Service for managing user ratings and leaderboards within groups.
    Handles calculation and updates of UserGroupRating records.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("UserRatingService initialized.")

    async def get_user_group_rating(
        self,
        user_id: UUID,
        group_id: UUID,
        period_identifier: Optional[str] = None
    ) -> Optional[UserGroupRatingResponse]:
        log_ctx = f"user ID '{user_id}', group ID '{group_id}'"
        if period_identifier: log_ctx += f", period '{period_identifier}'"
        logger.debug(f"Attempting to retrieve UserGroupRating for {log_ctx}.")

        stmt = select(UserGroupRating).options(
            selectinload(UserGroupRating.user).options(selectinload(User.user_type)),
            selectinload(UserGroupRating.group) if hasattr(UserGroupRating, 'group') else None
        ).where(
            UserGroupRating.user_id == user_id,
            UserGroupRating.group_id == group_id
        )
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))


        if hasattr(UserGroupRating, 'period_identifier'):
            stmt = stmt.where(UserGroupRating.period_identifier == period_identifier)
        elif period_identifier and period_identifier.lower() == "all_time":
             if hasattr(UserGroupRating, 'period_start_date') and hasattr(UserGroupRating, 'period_end_date'):
                stmt = stmt.where(UserGroupRating.period_start_date.is_(None), UserGroupRating.period_end_date.is_(None)) # type: ignore

        rating_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if rating_db:
            logger.info(f"UserGroupRating record found for {log_ctx}.")
            # return UserGroupRatingResponse.model_validate(rating_db) # Pydantic v2
            return UserGroupRatingResponse.from_orm(rating_db) # Pydantic v1

        logger.info(f"No UserGroupRating record found for {log_ctx}.")
        return None

    async def update_user_group_rating(
        self,
        user_id: UUID,
        group_id: UUID,
        period_identifier: Optional[str] = None
    ) -> Optional[UserGroupRatingResponse]:
        log_ctx = f"user ID '{user_id}', group ID '{group_id}'"
        if period_identifier: log_ctx += f", period '{period_identifier}'"
        logger.info(f"Attempting to update rating for {log_ctx}.")

        from app.src.services.bonuses.account import UserAccountService
        account_service = UserAccountService(self.db_session)

        user_account = await account_service.get_user_account(user_id, group_id=group_id)
        if not user_account:
            logger.warning(f"No bonus account found for {log_ctx}. Assuming 0 score for rating update.")
            new_score = Decimal("0.0")
        else:
            new_score = Decimal(user_account.balance)

        logger.info(f"Calculated new score for {log_ctx}: {new_score}")

        stmt_existing = select(UserGroupRating).where(
            UserGroupRating.user_id == user_id,
            UserGroupRating.group_id == group_id
        )
        if hasattr(UserGroupRating, 'period_identifier'):
            stmt_existing = stmt_existing.where(UserGroupRating.period_identifier == period_identifier)

        rating_db = (await self.db_session.execute(stmt_existing)).scalar_one_or_none()

        if rating_db:
            if rating_db.rating_score == new_score:
                logger.info(f"Rating for {log_ctx} is already {new_score}. No update needed.")
                if hasattr(rating_db, 'last_calculated_at'): # Optionally update timestamp even if score is same
                     rating_db.last_calculated_at = datetime.now(timezone.utc)
                     self.db_session.add(rating_db)
                     await self.commit() # Commit this minor timestamp update
                # Refresh for consistent response object structure
                await self.db_session.refresh(rating_db, attribute_names=['user', 'group'])
                return UserGroupRatingResponse.from_orm(rating_db)
            else:
                logger.info(f"Updating rating for {log_ctx} from {rating_db.rating_score} to {new_score}.")
                rating_db.rating_score = new_score
                if hasattr(rating_db, 'last_calculated_at'):
                    rating_db.last_calculated_at = datetime.now(timezone.utc)
        else:
            logger.info(f"Creating new UserGroupRating record for {log_ctx} with score {new_score}.")
            rating_data = {
                "user_id": user_id,
                "group_id": group_id,
                "rating_score": new_score,
            }
            if hasattr(UserGroupRating, 'last_calculated_at'):
                rating_data['last_calculated_at'] = datetime.now(timezone.utc)
            if hasattr(UserGroupRating, 'period_identifier'):
                rating_data['period_identifier'] = period_identifier

            rating_db = UserGroupRating(**rating_data)
            self.db_session.add(rating_db)

        try:
            await self.commit()
            refresh_attrs = ['user']
            if hasattr(UserGroupRating, 'group'):
                refresh_attrs.append('group')
            await self.db_session.refresh(rating_db, attribute_names=refresh_attrs)
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error updating/creating UserGroupRating for {log_ctx}: {e}", exc_info=True)
            raise ValueError(f"Could not update/create UserGroupRating due to data conflict: {e}")

        logger.info(f"UserGroupRating for {log_ctx} successfully set to score {new_score}.")
        # return UserGroupRatingResponse.model_validate(rating_db) # Pydantic v2
        return UserGroupRatingResponse.from_orm(rating_db) # Pydantic v1

    async def get_group_leaderboard(
        self,
        group_id: UUID,
        period_identifier: Optional[str] = None,
        limit: int = 100
    ) -> GroupLeaderboardResponse:
        log_ctx = f"group ID '{group_id}'"
        if period_identifier: log_ctx += f", period '{period_identifier}'"
        logger.info(f"Generating leaderboard for {log_ctx}, limit {limit}.")

        stmt = select(UserGroupRating).options(
            selectinload(UserGroupRating.user).options(selectinload(User.user_type)),
        ).where(UserGroupRating.group_id == group_id)

        if hasattr(UserGroupRating, 'period_identifier'):
            stmt = stmt.where(UserGroupRating.period_identifier == period_identifier)

        # Order by score, then by when the score was last calculated (earlier is better for ties), then by user ID for deterministic tie-breaking.
        order_by_clauses = [UserGroupRating.rating_score.desc()]
        if hasattr(UserGroupRating, 'last_calculated_at'):
            order_by_clauses.append(UserGroupRating.last_calculated_at.asc()) # type: ignore
        order_by_clauses.append(UserGroupRating.user_id.asc()) # Final deterministic tie-breaker

        stmt = stmt.order_by(*order_by_clauses).limit(limit)

        ratings_db = (await self.db_session.execute(stmt)).scalars().all()

        leaderboard_entries = [UserGroupRatingResponse.from_orm(r) for r in ratings_db] # Pydantic v1

        count_stmt = select(func.count(UserGroupRating.id)).where(UserGroupRating.group_id == group_id)
        if hasattr(UserGroupRating, 'period_identifier'):
             count_stmt = count_stmt.where(UserGroupRating.period_identifier == period_identifier)
        total_participants = (await self.db_session.execute(count_stmt)).scalar_one_or_none() or 0

        # Fetch group name for the response
        group_name = "N/A"
        group_obj = await self.db_session.get(Group, group_id)
        if group_obj:
            group_name = group_obj.name

        logger.info(f"Retrieved {len(leaderboard_entries)} entries for leaderboard of {log_ctx}.")

        return GroupLeaderboardResponse(
            group_id=group_id,
            group_name=group_name,
            period_identifier=period_identifier,
            ratings=leaderboard_entries,
            total_participants=total_participants,
            generated_at=datetime.now(timezone.utc)
        )

logger.info("UserRatingService class defined.")
