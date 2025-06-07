# backend/app/src/services/bonuses/reward.py
import logging
from typing import List, Optional, Any
from uuid import UUID
from decimal import Decimal # For points_cost

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_ # For list_rewards query

from app.src.services.base import BaseService
from app.src.models.bonuses.reward import Reward # SQLAlchemy Reward model
from app.src.models.bonuses.user_reward_redemption import UserRewardRedemption # Model for tracking redemptions
from app.src.models.groups.group import Group # If rewards are group-specific
from app.src.models.auth.user import User # For user redeeming, and created_by/updated_by

from app.src.schemas.bonuses.reward import ( # Pydantic Schemas
    RewardCreate,
    RewardUpdate,
    RewardResponse,
    RedeemRewardRequest # For user to request redemption
)
# For deducting points and creating transactions
# from app.src.services.bonuses.account import UserAccountService
# from app.src.services.bonuses.transaction import AccountTransactionService
# from app.src.schemas.bonuses.transaction import AccountTransactionCreate # For creating debit transaction

# Initialize logger for this module
logger = logging.getLogger(__name__)

class RewardService(BaseService):
    """
    Service for managing rewards that users can redeem with their bonus points.
    Handles CRUD for rewards and the redemption process.
    """

    def __init__(self, db_session: AsyncSession): # Potentially pass UserAccountService, AccountTransactionService
        super().__init__(db_session)
        # self.account_service = UserAccountService(db_session) # Example for DI
        # self.transaction_service = AccountTransactionService(db_session) # Example for DI
        logger.info("RewardService initialized.")

    async def get_reward_by_id(self, reward_id: UUID) -> Optional[RewardResponse]:
        """Retrieves a reward by its ID, with related entities loaded."""
        logger.debug(f"Attempting to retrieve reward by ID: {reward_id}")

        stmt = select(Reward).options(
            selectinload(Reward.group) if hasattr(Reward, 'group') else None,
            selectinload(Reward.created_by_user).options(selectinload(User.user_type)) if hasattr(Reward, 'created_by_user') else None,
            selectinload(Reward.updated_by_user).options(selectinload(User.user_type)) if hasattr(Reward, 'updated_by_user') else None
        ).where(Reward.id == reward_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))

        reward_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if reward_db:
            logger.info(f"Reward with ID '{reward_id}' found.")
            # return RewardResponse.model_validate(reward_db) # Pydantic v2
            return RewardResponse.from_orm(reward_db) # Pydantic v1
        logger.info(f"Reward with ID '{reward_id}' not found.")
        return None

    async def create_reward(self, reward_data: RewardCreate, creator_user_id: UUID) -> Optional[RewardResponse]: # Return Optional
        logger.debug(f"Attempting to create new reward '{reward_data.name}' by user ID: {creator_user_id}")

        if reward_data.group_id:
            if not await self.db_session.get(Group, reward_data.group_id):
                raise ValueError(f"Group with ID '{reward_data.group_id}' not found.")

        stmt_name_check = select(Reward.id).where(Reward.name == reward_data.name)
        if reward_data.group_id:
            stmt_name_check = stmt_name_check.where(Reward.group_id == reward_data.group_id)
        else:
            stmt_name_check = stmt_name_check.where(Reward.group_id.is_(None)) # type: ignore

        if (await self.db_session.execute(stmt_name_check)).scalar_one_or_none():
            scope = f"group ID {reward_data.group_id}" if reward_data.group_id else "global scope"
            raise ValueError(f"Reward with name '{reward_data.name}' already exists in {scope}.")

        reward_db_data = reward_data.dict()

        create_final_data = reward_db_data.copy()
        if hasattr(Reward, 'created_by_user_id'):
            create_final_data['created_by_user_id'] = creator_user_id
        if hasattr(Reward, 'updated_by_user_id'):
            create_final_data['updated_by_user_id'] = creator_user_id


        new_reward_db = Reward(**create_final_data)

        self.db_session.add(new_reward_db)
        try:
            await self.commit()
            # Refresh to load relationships for the response
            created_reward = await self.get_reward_by_id(new_reward_db.id)
            if created_reward:
                logger.info(f"Reward '{new_reward_db.name}' (ID: {new_reward_db.id}) created successfully.")
                return created_reward
            else: # Should not happen
                logger.error(f"Failed to retrieve newly created reward ID {new_reward_db.id} after commit.")
                return None
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error creating reward '{reward_data.name}': {e}", exc_info=True)
            raise ValueError(f"Could not create reward due to a data conflict: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Unexpected error creating reward '{reward_data.name}': {e}", exc_info=True)
            raise


    async def update_reward(
        self, reward_id: UUID, reward_update_data: RewardUpdate, current_user_id: UUID
    ) -> Optional[RewardResponse]:
        logger.debug(f"Attempting to update reward ID: {reward_id} by user ID: {current_user_id}")

        reward_db = await self.db_session.get(Reward, reward_id)
        if not reward_db:
            logger.warning(f"Reward ID '{reward_id}' not found for update.")
            return None

        update_data = reward_update_data.dict(exclude_unset=True)

        if 'group_id' in update_data and reward_db.group_id != update_data['group_id']:
            if update_data['group_id'] and not await self.db_session.get(Group, update_data['group_id']):
                raise ValueError(f"New Group ID '{update_data['group_id']}' not found.")

        new_name = update_data.get('name', reward_db.name)
        new_group_id = update_data.get('group_id', reward_db.group_id)
        if ('name' in update_data and new_name != reward_db.name) or \
           ('group_id' in update_data and new_group_id != reward_db.group_id):
            stmt_name_check = select(Reward.id).where(Reward.name == new_name, Reward.id != reward_id)
            if new_group_id is not None:
                stmt_name_check = stmt_name_check.where(Reward.group_id == new_group_id)
            else:
                stmt_name_check = stmt_name_check.where(Reward.group_id.is_(None)) # type: ignore
            if (await self.db_session.execute(stmt_name_check)).scalar_one_or_none():
                scope = f"group ID {new_group_id}" if new_group_id is not None else "global scope"
                raise ValueError(f"Another reward with name '{new_name}' already exists in {scope}.")

        for field, value in update_data.items():
            if hasattr(reward_db, field): setattr(reward_db, field, value)

        if hasattr(reward_db, 'updated_by_user_id'):
            reward_db.updated_by_user_id = current_user_id
        if hasattr(reward_db, 'updated_at'):
            reward_db.updated_at = datetime.now(timezone.utc)

        self.db_session.add(reward_db)
        try:
            await self.commit()
            logger.info(f"Reward ID '{reward_id}' updated successfully.")
            return await self.get_reward_by_id(reward_id)
        except Exception as e:
            await self.rollback()
            logger.error(f"Error updating reward ID '{reward_id}': {e}", exc_info=True)
            raise


    async def delete_reward(self, reward_id: UUID, current_user_id: UUID) -> bool:
        logger.debug(f"Attempting to delete reward ID: {reward_id} by user: {current_user_id}")
        reward_db = await self.db_session.get(Reward, reward_id)
        if not reward_db:
            logger.warning(f"Reward ID '{reward_id}' not found for deletion.")
            return False

        await self.db_session.delete(reward_db)
        await self.commit()
        logger.info(f"Reward ID '{reward_id}' deleted by user {current_user_id}.")
        return True

    async def list_rewards(
        self, group_id: Optional[UUID] = None, is_active: Optional[bool] = True,
        min_stock: Optional[int] = None, max_points_cost: Optional[Decimal] = None,
        skip: int = 0, limit: int = 100,
        include_global: bool = True # If group_id is provided, also include global rewards
    ) -> List[RewardResponse]:
        logger.debug(f"Listing rewards: group={group_id}, active={is_active}, stock>={min_stock}, cost<={max_points_cost}, global={include_global}")

        stmt = select(Reward).options(
            selectinload(Reward.group) if hasattr(Reward, 'group') else None,
            selectinload(Reward.created_by_user).options(selectinload(User.user_type)) if hasattr(Reward, 'created_by_user') else None
        )
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))

        conditions = []
        if group_id is not None:
            if include_global and hasattr(Reward, 'group_id'):
                 conditions.append(or_(Reward.group_id == group_id, Reward.group_id.is_(None))) # type: ignore
            else:
                 conditions.append(Reward.group_id == group_id)
        # If group_id is None, and include_global is True (default or explicit), it lists all.
        # If group_id is None, and include_global is False, it should list only global if that's the intent.
        # This might need a more explicit filter e.g. list_type: "all", "global_only", "group_specific"
        elif not include_global: # Only global if group_id is None and include_global is False
            conditions.append(Reward.group_id.is_(None)) # type: ignore


        if hasattr(Reward, 'is_active') and is_active is not None:
            conditions.append(Reward.is_active == is_active) # type: ignore
        if hasattr(Reward, 'stock_available') and min_stock is not None:
            conditions.append(Reward.stock_available >= min_stock) # type: ignore
        if hasattr(Reward, 'points_cost') and max_points_cost is not None:
            conditions.append(Reward.points_cost <= max_points_cost) # type: ignore

        if conditions:
            stmt = stmt.where(*conditions)

        order_by_attr = getattr(Reward, 'points_cost', Reward.name)
        stmt = stmt.order_by(order_by_attr).offset(skip).limit(limit) # type: ignore
        rewards_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # response_list = [RewardResponse.model_validate(r) for r in rewards_db] # Pydantic v2
        response_list = [RewardResponse.from_orm(r) for r in rewards_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} rewards.")
        return response_list

    async def redeem_reward(
        self,
        user_id: UUID,
        reward_id: UUID,
        redeem_data: RedeemRewardRequest,
        group_id_context: Optional[UUID] = None
    ) -> Dict[str, Any]: # Placeholder for UserRewardRedemptionResponse
        logger.info(f"User ID '{user_id}' attempting to redeem reward ID '{reward_id}'. Quantity: {redeem_data.quantity}")

        reward_db = await self.db_session.get(Reward, reward_id)
        if not reward_db or not getattr(reward_db, 'is_active', True):
            raise ValueError("Reward not found or is not active.")

        if hasattr(reward_db, 'group_id') and reward_db.group_id is not None and reward_db.group_id != group_id_context:
             raise ValueError("This reward is not available in your current group context.")

        quantity_to_redeem = redeem_data.quantity
        if quantity_to_redeem <= 0: raise ValueError("Quantity to redeem must be positive.")

        if hasattr(reward_db, 'stock_available') and reward_db.stock_available is not None:
            if reward_db.stock_available < quantity_to_redeem:
                raise ValueError(f"Not enough stock for reward '{reward_db.name}'. Available: {reward_db.stock_available}")

        total_cost = Decimal(reward_db.points_cost) * quantity_to_redeem

        from app.src.services.bonuses.account import UserAccountService
        from app.src.services.bonuses.transaction import AccountTransactionService, AccountTransactionCreate

        account_service = UserAccountService(self.db_session)
        # Determine which account to use (user's global or group-specific account for this group_id_context)
        user_account_response = await account_service.get_or_create_user_account(user_id, group_id=group_id_context)
        if Decimal(user_account_response.balance) < total_cost:
            raise ValueError(f"Insufficient points. Required: {total_cost}, Available: {user_account_response.balance}")

        try:
            transaction_service = AccountTransactionService(self.db_session)
            transaction_create = AccountTransactionCreate(
                user_account_id=user_account_response.id,
                transaction_type="REWARD_REDEMPTION",
                amount= -total_cost,
                description=f"Redeemed {quantity_to_redeem}x '{reward_db.name}'",
                related_entity_id=reward_id
            )
            _updated_account_resp, _transaction_resp = await transaction_service.create_transaction(
                transaction_data=transaction_create,
                commit_session=False
            )

            if hasattr(reward_db, 'stock_available') and reward_db.stock_available is not None:
                reward_db.stock_available -= quantity_to_redeem
                self.db_session.add(reward_db)

            redemption_record = UserRewardRedemption(
                user_id=user_id,
                reward_id=reward_id,
                user_account_id=user_account_response.id,
                transaction_id=_transaction_resp.id,
                quantity=quantity_to_redeem,
                points_spent=total_cost,
                status="COMPLETED",
                notes=redeem_data.notes
            )
            self.db_session.add(redemption_record)

            await self.commit()

            await self.db_session.refresh(redemption_record, attribute_names=['user', 'reward', 'account', 'transaction'])

            logger.info(f"User ID '{user_id}' successfully redeemed {quantity_to_redeem} of reward ID '{reward_id}'.")

            # from app.src.schemas.bonuses.reward import UserRewardRedemptionResponse # Placeholder
            # return UserRewardRedemptionResponse.model_validate(redemption_record) # Pydantic v2
            # return UserRewardRedemptionResponse.from_orm(redemption_record) # Pydantic v1
            return {"redemption_id": redemption_record.id, "status": redemption_record.status, "points_spent": str(redemption_record.points_spent), "reward_name": reward_db.name}


        except ValueError as ve:
            await self.rollback()
            logger.warning(f"Redemption failed for user ID '{user_id}', reward ID '{reward_id}': {ve}")
            raise
        except Exception as e:
            await self.rollback()
            logger.error(f"Unexpected error during reward redemption for user ID '{user_id}', reward ID '{reward_id}': {e}", exc_info=True)
            raise

logger.info("RewardService class defined.")
