# backend/app/src/services/bonuses/bonus_rule.py
import logging
from typing import List, Optional, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_ # Added for get_applicable_bonus_rules

from app.src.services.base import BaseService
from app.src.models.bonuses.bonus import BonusRule # SQLAlchemy BonusRule model
from app.src.models.groups.group import Group # For group-specific rules
from app.src.models.dictionaries.task_types import TaskType # For rules linked to task types
from app.src.models.tasks.task import Task # For rules linked to specific tasks
# from app.src.models.tasks.event import Event # If rules can be linked to specific events
from app.src.models.auth.user import User # For created_by_user, updated_by_user

from app.src.schemas.bonuses.bonus_rule import ( # Pydantic Schemas
    BonusRuleCreate,
    BonusRuleUpdate,
    BonusRuleResponse
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class BonusRuleService(BaseService):
    """
    Service for managing bonus rules.
    Bonus rules define conditions under which points are awarded or deducted.
    They can be linked to task types, specific tasks/events, or be general.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("BonusRuleService initialized.")

    async def get_bonus_rule_by_id(self, rule_id: UUID) -> Optional[BonusRuleResponse]:
        """Retrieves a bonus rule by its ID, with related entities loaded."""
        logger.debug(f"Attempting to retrieve bonus rule by ID: {rule_id}")

        stmt = select(BonusRule).options(
            selectinload(BonusRule.group),
            selectinload(BonusRule.task_type),
            selectinload(BonusRule.task),
            # selectinload(BonusRule.event),
            selectinload(BonusRule.created_by_user).options(selectinload(User.user_type)) if hasattr(BonusRule, 'created_by_user') else None,
            selectinload(BonusRule.updated_by_user).options(selectinload(User.user_type)) if hasattr(BonusRule, 'updated_by_user') else None
        ).where(BonusRule.id == rule_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))

        rule_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if rule_db:
            logger.info(f"Bonus rule with ID '{rule_id}' found.")
            # return BonusRuleResponse.model_validate(rule_db) # Pydantic v2
            return BonusRuleResponse.from_orm(rule_db) # Pydantic v1
        logger.info(f"Bonus rule with ID '{rule_id}' not found.")
        return None

    async def create_bonus_rule(self, rule_data: BonusRuleCreate, creator_user_id: UUID) -> Optional[BonusRuleResponse]: # Return Optional
        logger.debug(f"Attempting to create new bonus rule '{rule_data.name}' by user ID: {creator_user_id}")

        if rule_data.group_id:
            if not await self.db_session.get(Group, rule_data.group_id):
                raise ValueError(f"Group with ID '{rule_data.group_id}' not found.")

        if rule_data.task_type_id:
            if not await self.db_session.get(TaskType, rule_data.task_type_id):
                raise ValueError(f"TaskType with ID '{rule_data.task_type_id}' not found.")

        if rule_data.task_id:
            if not await self.db_session.get(Task, rule_data.task_id):
                raise ValueError(f"Task with ID '{rule_data.task_id}' not found.")

        stmt_name_check = select(BonusRule.id).where(BonusRule.name == rule_data.name) # Select only ID
        if rule_data.group_id:
            stmt_name_check = stmt_name_check.where(BonusRule.group_id == rule_data.group_id)
        else:
            stmt_name_check = stmt_name_check.where(BonusRule.group_id == None)

        if (await self.db_session.execute(stmt_name_check)).scalar_one_or_none():
            scope = f"group ID {rule_data.group_id}" if rule_data.group_id else "global scope"
            logger.warning(f"Bonus rule with name '{rule_data.name}' already exists in {scope}.")
            raise ValueError(f"Bonus rule with name '{rule_data.name}' already exists in {scope}.")

        rule_db_data = rule_data.dict()

        create_final_data = rule_db_data.copy()
        if hasattr(BonusRule, 'created_by_user_id'):
             create_final_data['created_by_user_id'] = creator_user_id
        if hasattr(BonusRule, 'updated_by_user_id'): # Also set updated_by on creation
             create_final_data['updated_by_user_id'] = creator_user_id

        new_rule_db = BonusRule(**create_final_data)

        self.db_session.add(new_rule_db)
        try:
            await self.commit()
            # Return fully populated response by calling get_bonus_rule_by_id
            created_rule = await self.get_bonus_rule_by_id(new_rule_db.id)
            if created_rule:
                logger.info(f"Bonus rule '{new_rule_db.name}' (ID: {new_rule_db.id}) created successfully.")
                return created_rule
            else: # Should not happen if commit was successful
                logger.error(f"Failed to retrieve newly created bonus rule ID {new_rule_db.id} after commit.")
                return None
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error creating bonus rule '{rule_data.name}': {e}", exc_info=True)
            raise ValueError(f"Could not create bonus rule due to a data conflict: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Unexpected error creating bonus rule '{rule_data.name}': {e}", exc_info=True)
            raise


    async def update_bonus_rule(
        self, rule_id: UUID, rule_update_data: BonusRuleUpdate, current_user_id: UUID
    ) -> Optional[BonusRuleResponse]:
        logger.debug(f"Attempting to update bonus rule ID: {rule_id} by user ID: {current_user_id}")

        rule_db = await self.db_session.get(BonusRule, rule_id)
        if not rule_db:
            logger.warning(f"Bonus rule ID '{rule_id}' not found for update.")
            return None

        update_data = rule_update_data.dict(exclude_unset=True)

        if 'group_id' in update_data and rule_db.group_id != update_data['group_id']:
            if update_data['group_id'] and not await self.db_session.get(Group, update_data['group_id']):
                raise ValueError(f"New Group ID '{update_data['group_id']}' not found.")
        if 'task_type_id' in update_data and rule_db.task_type_id != update_data['task_type_id']:
            if update_data['task_type_id'] and not await self.db_session.get(TaskType, update_data['task_type_id']):
                raise ValueError(f"New TaskType ID '{update_data['task_type_id']}' not found.")

        new_name = update_data.get('name', rule_db.name)
        new_group_id = update_data.get('group_id', rule_db.group_id) # Handles if group_id becomes None (global)

        if ('name' in update_data and new_name != rule_db.name) or \
           ('group_id' in update_data and new_group_id != rule_db.group_id): # Check if group_id itself changed
            stmt_name_check = select(BonusRule.id).where(
                BonusRule.name == new_name,
                BonusRule.id != rule_id
            )
            if new_group_id is not None: # Rule is being set to group-specific or changing groups
                stmt_name_check = stmt_name_check.where(BonusRule.group_id == new_group_id)
            else: # Rule is being set to global (or was global and name changes)
                stmt_name_check = stmt_name_check.where(BonusRule.group_id.is_(None)) # type: ignore

            if (await self.db_session.execute(stmt_name_check)).scalar_one_or_none():
                scope = f"group ID {new_group_id}" if new_group_id is not None else "global scope"
                raise ValueError(f"Another bonus rule with name '{new_name}' already exists in {scope}.")

        for field, value in update_data.items():
            if hasattr(rule_db, field):
                setattr(rule_db, field, value)
            else:
                logger.warning(f"Field '{field}' not found on BonusRule model for update of rule ID '{rule_id}'.")

        if hasattr(rule_db, 'updated_by_user_id'):
            rule_db.updated_by_user_id = current_user_id
        if hasattr(rule_db, 'updated_at'):
            rule_db.updated_at = datetime.now(timezone.utc)

        self.db_session.add(rule_db)
        try:
            await self.commit()
            logger.info(f"Bonus rule ID '{rule_id}' updated successfully by user ID '{current_user_id}'.")
            return await self.get_bonus_rule_by_id(rule_id)
        except Exception as e:
            await self.rollback()
            logger.error(f"Error updating bonus rule ID '{rule_id}': {e}", exc_info=True)
            raise


    async def delete_bonus_rule(self, rule_id: UUID, current_user_id: UUID) -> bool:
        logger.debug(f"Attempting to delete bonus rule ID: {rule_id} by user ID: {current_user_id}")

        rule_db = await self.db_session.get(BonusRule, rule_id)
        if not rule_db:
            logger.warning(f"Bonus rule ID '{rule_id}' not found for deletion.")
            return False

        await self.db_session.delete(rule_db)
        await self.commit()
        logger.info(f"Bonus rule ID '{rule_id}' deleted successfully by user ID '{current_user_id}'.")
        return True

    async def list_bonus_rules(
        self,
        group_id: Optional[UUID] = None,
        task_type_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100,
        include_global_rules_for_group: bool = False # If true and group_id is given, also include global rules
    ) -> List[BonusRuleResponse]:
        logger.debug(f"Listing bonus rules: group={group_id}, task_type={task_type_id}, task={task_id}, active={is_active}, global_for_group={include_global_rules_for_group}")

        stmt = select(BonusRule).options(
            selectinload(BonusRule.group), selectinload(BonusRule.task_type),
            selectinload(BonusRule.task),
            selectinload(BonusRule.created_by_user).options(selectinload(User.user_type)) if hasattr(BonusRule, 'created_by_user') else None
        )
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))


        conditions = []
        if group_id is not None:
            if include_global_rules_for_group:
                conditions.append(or_(BonusRule.group_id == group_id, BonusRule.group_id.is_(None))) # type: ignore
            else:
                conditions.append(BonusRule.group_id == group_id)
        # else: # No group_id specified, could list only global rules or all rules depending on desired behavior
        #     conditions.append(BonusRule.group_id.is_(None)) # Example: only global if no group_id

        if task_type_id:
            conditions.append(BonusRule.task_type_id == task_type_id)
        if task_id:
            conditions.append(BonusRule.task_id == task_id)

        if hasattr(BonusRule, 'is_active') and is_active is not None:
            conditions.append(BonusRule.is_active == is_active) # type: ignore

        if conditions:
            stmt = stmt.where(*conditions)

        stmt = stmt.order_by(BonusRule.group_id.nullsfirst(), BonusRule.name).offset(skip).limit(limit) # Show global rules first

        rules_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # response_list = [BonusRuleResponse.model_validate(r) for r in rules_db] # Pydantic v2
        response_list = [BonusRuleResponse.from_orm(r) for r in rules_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} bonus rules.")
        return response_list

    async def get_applicable_bonus_rules(
        self,
        group_id: UUID, # Context: Current group
        task_id: Optional[UUID] = None, # Context: Specific task, if any
        task_type_id: Optional[UUID] = None, # Context: Type of task, if task_id not specific enough or not given
        # action_type: str # Context: e.g., "TASK_COMPLETION", "STREAK_ACHIEVED" - for more complex rule conditions
    ) -> List[BonusRuleResponse]:
        logger.debug(f"Getting applicable bonus rules for group {group_id}, task {task_id}, task_type {task_type_id}")

        # This builds a query that finds rules matching:
        # 1. Specific task ID (most specific)
        # 2. Specific task_type_id AND (group_id OR global)
        # 3. Specific group_id general rules (not task/type specific)
        # 4. Global general rules (not task/type/group specific)

        # All rules must be active
        base_conditions = [BonusRule.is_active == True] if hasattr(BonusRule, 'is_active') else []

        rule_clauses = []

        # Rule for specific task (task_id takes precedence, group_id is implicit if task belongs to group)
        if task_id:
            rule_clauses.append(BonusRule.task_id == task_id)

        # Rule for task_type within the specific group OR globally for that task_type
        if task_type_id:
            rule_clauses.append(
                (BonusRule.task_type_id == task_type_id) &
                (BonusRule.task_id == None) & # Not task-specific
                (or_(BonusRule.group_id == group_id, BonusRule.group_id == None))
            )

        # General rule for the specific group (not task/type specific)
        rule_clauses.append(
            (BonusRule.group_id == group_id) &
            (BonusRule.task_id == None) &
            (BonusRule.task_type_id == None)
        )

        # Global general rule
        rule_clauses.append(
            (BonusRule.group_id == None) &
            (BonusRule.task_id == None) &
            (BonusRule.task_type_id == None)
        )

        stmt = select(BonusRule).options(
            selectinload(BonusRule.group), selectinload(BonusRule.task_type),
            selectinload(BonusRule.task)
        ).where(or_(*rule_clauses), *base_conditions) # Apply base conditions (like is_active) to all clauses

        # Order to determine precedence: more specific rules first.
        # Task-specific > Task_Type_Group > Task_Type_Global > Group_General > Global_General
        stmt = stmt.order_by(
            BonusRule.task_id.desc().nullslast(),      # Task-specific first
            BonusRule.task_type_id.desc().nullslast(), # Then type-specific
            BonusRule.group_id.desc().nullslast()      # Then group-specific (global has group_id=NULL)
        )

        rules_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # response_list = [BonusRuleResponse.model_validate(r) for r in rules_db] # Pydantic v2
        response_list = [BonusRuleResponse.from_orm(r) for r in rules_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} potentially applicable bonus rules, ordered by specificity.")
        return response_list

logger.info("BonusRuleService class defined.")
