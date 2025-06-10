# backend/app/src/services/bonuses/calculation.py
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select # Required for _check_rule_conditions example
from sqlalchemy import func # Required for _check_rule_conditions example


from app.src.services.base import BaseService
from app.src.models.bonuses.bonus import BonusRule
from app.src.models.tasks.task import Task
from app.src.models.tasks.completion import TaskCompletion
from app.src.models.auth.user import User
from app.src.models.groups.group import Group # Not directly used but contextually relevant via Task

from app.src.schemas.bonuses.bonus_rule import BonusRuleResponse
# from app.src.services.bonuses.bonus_rule import BonusRuleService

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Constants for completion statuses, if needed for conditions, should match those in completion service
COMPLETION_STATUS_APPROVED = "APPROVED"


class BonusCalculationService(BaseService):
    """
    Service responsible for calculating bonus points based on defined rules and event contexts.
    This service can handle simple fixed-point rules or more complex, conditional logic.
    It's typically called by other services (e.g., TaskCompletionService) when a
    potentially bonus-triggering event occurs.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("BonusCalculationService initialized.")

    async def calculate_bonus_for_task_completion(
        self,
        task: Task,
        user: User,
        task_completion: TaskCompletion
    ) -> Optional[Decimal]:
        logger.info(f"Calculating bonus for task ID '{task.id}' completion by user ID '{user.id}'.")

        if not task.group_id:
            logger.warning(f"Task ID '{task.id}' is missing group context. Cannot accurately calculate group-specific bonuses.")

        from app.src.services.bonuses.bonus_rule import BonusRuleService
        bonus_rule_service = BonusRuleService(self.db_session)

        applicable_rules_schemas: List[BonusRuleResponse] = await bonus_rule_service.get_applicable_bonus_rules(
            group_id=task.group_id,
            task_id=task.id,
            task_type_id=task.task_type_id
        )

        if not applicable_rules_schemas:
            logger.info(f"No applicable bonus rules found for task ID '{task.id}'. No bonus awarded.")
            return None

        final_bonus_amount = Decimal("0.0")
        applied_rule_description: Optional[str] = None

        for rule_schema in applicable_rules_schemas:
            logger.debug(f"Evaluating rule ID '{rule_schema.id}' (Name: '{rule_schema.name}', Points: {rule_schema.points_amount})")

            # Check general rule conditions first
            if await self._check_rule_conditions(rule_schema, task, user, task_completion):
                if rule_schema.points_amount is not None:
                    final_bonus_amount = Decimal(str(rule_schema.points_amount))
                    applied_rule_description = rule_schema.name
                    logger.info(f"Applying bonus rule '{applied_rule_description}': {final_bonus_amount} points.")
                    break

        if applied_rule_description is None:
            logger.info(f"No bonus rule with a specific point value was applied for task ID '{task.id}'.")
            return None

        return final_bonus_amount

    async def _check_rule_conditions(
        self,
        rule: BonusRuleResponse,
        task: Task,
        user: User,
        task_completion: TaskCompletion
    ) -> bool:
        logger.debug(f"Checking conditions for rule '{rule.name}' (ID: {rule.id})... (Placeholder)")

        # Example specific condition from rule data itself (e.g. rule.custom_condition_field == some_value)
        # if rule.custom_condition_field == "SOME_VALUE":
        #     # Evaluate that condition based on task, user, completion context
        #     pass

        # Example condition: Rule applies only if task was completed ahead of due date
        # This assumes `rule` schema might have fields like `condition_type` and `condition_params`
        # For instance, if rule.condition_type == "COMPLETED_EARLY" and rule.condition_params = {"min_hours_early": 2}
        # if getattr(rule, 'condition_type', None) == "COMPLETED_EARLY":
        #     if task.due_date and task_completion.completed_at:
        #         if task_completion.completed_at < task.due_date:
        #             # Check if 'min_hours_early' parameter is met
        #             min_hours_early = getattr(rule, 'condition_params', {}).get('min_hours_early')
        #             if min_hours_early:
        #                 if task.due_date - task_completion.completed_at >= timedelta(hours=min_hours_early):
        #                     logger.info(f"Condition 'COMPLETED_EARLY' (min {min_hours_early}hrs) met for rule '{rule.name}'.")
        #                     return True
        #             else: # No specific hour count, just being early is enough
        #                 logger.info(f"Condition 'COMPLETED_EARLY' met for rule '{rule.name}'.")
        #                 return True
        #     return False

        # Example: Rule applies for first-time completion of THIS specific task by THIS user
        # if getattr(rule, 'condition_type', None) == "FIRST_TIME_COMPLETION_SPECIFIC_TASK":
        #    stmt = select(func.count(TaskCompletion.id)).where(
        #        TaskCompletion.task_id == task.id,
        #        TaskCompletion.user_id == user.id,
        #        TaskCompletion.id != task_completion.id,
        #        TaskCompletion.status == COMPLETION_STATUS_APPROVED
        #    )
        #    prior_completions_count = (await self.db_session.execute(stmt)).scalar_one()
        #    if prior_completions_count == 0:
        #        logger.info(f"Condition 'FIRST_TIME_COMPLETION_SPECIFIC_TASK' met for rule '{rule.name}'.")
        #        return True
        #    return False

        logger.debug(f"Rule '{rule.name}' conditions evaluation (placeholder): Assuming conditions met by default.")
        return True

logger.info("BonusCalculationService class defined.")
