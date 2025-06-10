# backend/app/src/services/tasks/completion.py
import logging
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.tasks.completion import TaskCompletion # SQLAlchemy TaskCompletion model
from app.src.models.tasks.task import Task # For task context
# from app.src.models.tasks.event import Event # If completions can be for events too
from app.src.models.auth.user import User # For user context (completer, approver)
from app.src.models.tasks.assignment import TaskAssignment # To check if user was assigned

from app.src.schemas.tasks.completion import ( # Pydantic Schemas
    TaskCompletionCreateRequest, # User marking task as done
    TaskCompletionAdminUpdateRequest, # Admin approving/rejecting
    TaskCompletionResponse
)
# from app.src.services.bonuses.account import UserAccountService # For awarding points - potential circularity
# from app.src.services.notifications.notification import InternalNotificationService # For sending notifications

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Define completion statuses (could be an Enum or from a Status dictionary model)
COMPLETION_STATUS_PENDING_APPROVAL = "PENDING_APPROVAL"
COMPLETION_STATUS_APPROVED = "APPROVED"
COMPLETION_STATUS_REJECTED = "REJECTED"
COMPLETION_STATUS_COMPLETED = "COMPLETED" # For tasks not requiring approval

class TaskCompletionService(BaseService):
    """
    Service for managing the lifecycle of task (or event) completions.
    Handles users marking tasks as done, admin approvals/rejections,
    and potentially triggering point allocations.
    """

    def __init__(self, db_session: AsyncSession): # Add other services like UserAccountService if needed
        super().__init__(db_session)
        # self.user_account_service = UserAccountService(db_session) # Example
        # self.notification_service = InternalNotificationService(db_session) # Example
        logger.info("TaskCompletionService initialized.")

    async def mark_task_as_completed_by_user(
        self,
        task_id: UUID,
        user_id: UUID,
        completion_data: TaskCompletionCreateRequest
    ) -> TaskCompletionResponse:
        logger.debug(f"User ID '{user_id}' attempting to mark task ID '{task_id}' as completed.")

        task = await self.db_session.get(Task, task_id, options=[selectinload(Task.task_type)])
        if not task: raise ValueError(f"Task with ID '{task_id}' not found.")

        user = await self.db_session.get(User, user_id)
        if not user: raise ValueError(f"User with ID '{user_id}' not found.")

        # Optional: Check if user is assigned (if assignments are enforced for completion)
        # assignment_stmt = select(TaskAssignment.id).where(
        #     TaskAssignment.task_id == task_id,
        #     TaskAssignment.user_id == user_id,
        #     TaskAssignment.is_active == True
        # )
        # if not (await self.db_session.execute(assignment_stmt)).scalar_one_or_none():
        #     raise ValueError(f"User ID '{user_id}' is not actively assigned to task ID '{task_id}'.")

        existing_completion_stmt = select(TaskCompletion.id).where(
            TaskCompletion.task_id == task_id,
            TaskCompletion.user_id == user_id,
            TaskCompletion.status != COMPLETION_STATUS_REJECTED
        )
        existing_completion_id = (await self.db_session.execute(existing_completion_stmt)).scalar_one_or_none()

        is_task_repeatable = getattr(task, 'is_repeatable', False)
        if existing_completion_id and not is_task_repeatable:
            logger.warning(f"Task ID '{task_id}' already completed by user ID '{user_id}' and is not repeatable.")
            raise ValueError(f"Task ID '{task_id}' already completed by you and is not repeatable.")

        requires_approval = getattr(task.task_type, 'requires_approval', True) if task.task_type else True

        initial_status = COMPLETION_STATUS_PENDING_APPROVAL if requires_approval else COMPLETION_STATUS_COMPLETED

        completion_db_data = completion_data.dict()

        new_completion_db = TaskCompletion(
            task_id=task_id,
            user_id=user_id,
            status=initial_status,
            completed_at=datetime.now(timezone.utc),
            **completion_db_data
        )

        self.db_session.add(new_completion_db)
        try:
            await self.commit()
            await self.db_session.refresh(new_completion_db, attribute_names=['user', 'task', 'reviewed_by_user']) # Add reviewed_by_user
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error marking task ID '{task_id}' as completed by user ID '{user_id}': {e}", exc_info=True)
            raise ValueError(f"Could not mark task as completed due to a data conflict: {e}")

        logger.info(f"Task ID '{task_id}' marked as '{initial_status}' by user ID '{user_id}'. Completion ID: {new_completion_db.id}")

        # TODO: Trigger notifications and point allocations based on initial_status and task.points_value

        # return TaskCompletionResponse.model_validate(new_completion_db) # Pydantic v2
        return TaskCompletionResponse.from_orm(new_completion_db) # Pydantic v1


    async def update_task_completion_status(
        self,
        completion_id: UUID,
        admin_update_data: TaskCompletionAdminUpdateRequest,
        admin_user_id: UUID
    ) -> Optional[TaskCompletionResponse]:
        logger.debug(f"Admin ID '{admin_user_id}' attempting to update status of completion ID '{completion_id}' to '{admin_update_data.status}'.")

        completion_db = await self.db_session.get(TaskCompletion, completion_id, options=[
            selectinload(TaskCompletion.task).options(selectinload(Task.task_type)),
            selectinload(TaskCompletion.user)
        ])
        if not completion_db:
            logger.warning(f"TaskCompletion record with ID '{completion_id}' not found.")
            return None

        if completion_db.status != COMPLETION_STATUS_PENDING_APPROVAL:
            logger.warning(f"TaskCompletion ID '{completion_id}' is not pending approval (current status: {completion_db.status}). Cannot update.")
            raise ValueError(f"Completion is not pending approval. Current status: {completion_db.status}")

        original_status = completion_db.status
        new_status = admin_update_data.status

        completion_db.status = new_status
        completion_db.admin_notes = admin_update_data.admin_notes
        completion_db.reviewed_by_user_id = admin_user_id
        completion_db.reviewed_at = datetime.now(timezone.utc)

        self.db_session.add(completion_db)
        await self.commit()
        await self.db_session.refresh(completion_db, attribute_names=['user', 'task', 'reviewed_by_user'])

        logger.info(f"Status of completion ID '{completion_id}' updated from '{original_status}' to '{new_status}' by admin ID '{admin_user_id}'.")

        # TODO: Trigger notifications and point allocations based on new_status and completion_db.task.points_value

        # return TaskCompletionResponse.model_validate(completion_db) # Pydantic v2
        return TaskCompletionResponse.from_orm(completion_db) # Pydantic v1

    async def list_completions_for_task(
        self, task_id: UUID, skip: int = 0, limit: int = 100,
        status: Optional[str] = None
    ) -> List[TaskCompletionResponse]:
        logger.debug(f"Listing completions for task ID: {task_id}, status: {status}, skip={skip}, limit={limit}")

        stmt = select(TaskCompletion).options(
            selectinload(TaskCompletion.user).options(selectinload(User.user_type)),
            selectinload(TaskCompletion.task),
            selectinload(TaskCompletion.reviewed_by_user).options(selectinload(User.user_type)) if hasattr(TaskCompletion, 'reviewed_by_user') else None
        ).where(TaskCompletion.task_id == task_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))


        if status:
            stmt = stmt.where(TaskCompletion.status == status)

        stmt = stmt.order_by(TaskCompletion.completed_at.desc()).offset(skip).limit(limit)

        completions_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # response_list = [TaskCompletionResponse.model_validate(c) for c in completions_db] # Pydantic v2
        response_list = [TaskCompletionResponse.from_orm(c) for c in completions_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} completions for task ID '{task_id}'.")
        return response_list

    async def list_completions_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100,
        status: Optional[str] = None,
        group_id: Optional[UUID] = None
    ) -> List[TaskCompletionResponse]:
        logger.debug(f"Listing completions by user ID: {user_id}, status: {status}, group: {group_id}, skip={skip}, limit={limit}")

        stmt = select(TaskCompletion).options(
            selectinload(TaskCompletion.user).options(selectinload(User.user_type)),
            selectinload(TaskCompletion.task).options(
                selectinload(Task.task_type),
                selectinload(Task.group)
            ),
            selectinload(TaskCompletion.reviewed_by_user).options(selectinload(User.user_type)) if hasattr(TaskCompletion, 'reviewed_by_user') else None
        ).where(TaskCompletion.user_id == user_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))


        if status:
            stmt = stmt.where(TaskCompletion.status == status)
        if group_id:
            stmt = stmt.join(Task, TaskCompletion.task_id == Task.id).where(Task.group_id == group_id)

        stmt = stmt.order_by(TaskCompletion.completed_at.desc()).offset(skip).limit(limit)

        completions_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # response_list = [TaskCompletionResponse.model_validate(c) for c in completions_db] # Pydantic v2
        response_list = [TaskCompletionResponse.from_orm(c) for c in completions_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} completions by user ID '{user_id}'.")
        return response_list

    async def get_completion_details(self, completion_id: UUID) -> Optional[TaskCompletionResponse]:
        logger.debug(f"Getting completion details for ID {completion_id}")
        stmt = select(TaskCompletion).options(
            selectinload(TaskCompletion.user).options(selectinload(User.user_type)),
            selectinload(TaskCompletion.task).options(
                selectinload(Task.task_type),
                selectinload(Task.status),
                selectinload(Task.group)
            ),
            selectinload(TaskCompletion.reviewed_by_user).options(selectinload(User.user_type)) if hasattr(TaskCompletion, 'reviewed_by_user') else None
        ).where(TaskCompletion.id == completion_id)
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))

        completion_db = (await self.db_session.execute(stmt)).scalar_one_or_none()
        if not completion_db:
            logger.info(f"No task completion found for ID {completion_id}")
            return None

        # return TaskCompletionResponse.model_validate(completion_db) # Pydantic v2
        return TaskCompletionResponse.from_orm(completion_db) # Pydantic v1

logger.info("TaskCompletionService class defined.")
