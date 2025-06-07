# backend/app/src/services/tasks/task.py
import logging
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.tasks.task import Task # SQLAlchemy Task model
from app.src.models.auth.user import User
from app.src.models.groups.group import Group
from app.src.models.dictionaries.task_types import TaskType
from app.src.models.dictionaries.statuses import Status # For task status
# Assuming these models exist for relationships mentioned in get_task_by_id
from app.src.models.tasks.assignment import TaskAssignment
from app.src.models.tasks.completion import TaskCompletion
from app.src.models.tasks.review import TaskReview


from app.src.schemas.tasks.task import ( # Pydantic Task schemas
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskDetailedResponse # Assuming a more detailed response schema
)
# For recurring task creation logic, if complex, might involve TaskSchedulingService or utilities
# from .scheduler import TaskSchedulingService # Avoid direct import for now if possible

# Initialize logger for this module
logger = logging.getLogger(__name__)

class TaskService(BaseService):
    """
    Service for managing tasks, including CRUD operations, and handling
    task-specific logic like recurrence (though actual instance creation for
    recurrence might be delegated to a scheduling service).
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("TaskService initialized.")

    async def get_task_by_id(self, task_id: UUID, include_details: bool = False) -> Optional[TaskResponse]: # Or TaskDetailedResponse
        """
        Retrieves a task by its ID.
        Can optionally include more details like assignees, completions, type, status, etc.
        """
        logger.debug(f"Attempting to retrieve task by ID: {task_id}, include_details: {include_details}")

        query = select(Task).where(Task.id == task_id)
        if include_details:
            query = query.options(
                selectinload(Task.task_type),
                selectinload(Task.status),
                selectinload(Task.group),
                selectinload(Task.created_by_user).options(selectinload(User.user_type)), # Load user's type
                selectinload(Task.updated_by_user).options(selectinload(User.user_type)) if hasattr(Task, 'updated_by_user') else None,
                selectinload(Task.assignments).joinedload(TaskAssignment.user).options(selectinload(User.user_type)),
                selectinload(Task.completions).joinedload(TaskCompletion.user).options(selectinload(User.user_type)),
                selectinload(Task.reviews).joinedload(TaskReview.reviewer_user).options(selectinload(User.user_type))
                # selectinload(Task.bonus_rules) # If bonus rules are linked
            )
            # Filter out None options from query.options if they occur (e.g. conditional updated_by_user)
            query = query.options(*(opt for opt in query.get_options() if opt is not None))

        result = await self.db_session.execute(query)
        task_db = result.scalar_one_or_none()

        if task_db:
            logger.info(f"Task with ID '{task_id}' found.")
            if include_details:
                # return TaskDetailedResponse.model_validate(task_db) # Pydantic v2
                return TaskDetailedResponse.from_orm(task_db) # Pydantic v1
            # return TaskResponse.model_validate(task_db) # Pydantic v2
            return TaskResponse.from_orm(task_db) # Pydantic v1

        logger.info(f"Task with ID '{task_id}' not found.")
        return None

    async def create_task(self, task_create_data: TaskCreate, creator_user_id: UUID) -> Optional[TaskDetailedResponse]: # Return Optional for consistency
        """
        Creates a new task.

        Args:
            task_create_data (TaskCreate): Data for the new task.
            creator_user_id (UUID): ID of the user creating the task.

        Returns:
            Optional[TaskDetailedResponse]: The created task with details, or None if creation failed.

        Raises:
            ValueError: If referenced entities (group, task type, status) are not found.
        """
        logger.debug(f"Attempting to create new task '{task_create_data.title}' by user ID: {creator_user_id}")

        group = await self.db_session.get(Group, task_create_data.group_id)
        if not group: raise ValueError(f"Group with ID '{task_create_data.group_id}' not found.")

        task_type = await self.db_session.get(TaskType, task_create_data.task_type_id)
        if not task_type: raise ValueError(f"TaskType with ID '{task_create_data.task_type_id}' not found.")

        status_id_to_set = task_create_data.status_id
        if not status_id_to_set:
            default_status_stmt = select(Status.id).where(Status.code == "OPEN")
            default_status_id = (await self.db_session.execute(default_status_stmt)).scalar_one_or_none()
            if not default_status_id:
                # If status is mandatory for a Task (model has status_id as non-nullable without DB default)
                # and no default "OPEN" status is found, this is a configuration issue.
                logger.error("Default status 'OPEN' not found and no status_id provided. Task creation failed.")
                raise ValueError("Task status is required, but default 'OPEN' status not found in system.")
            status_id_to_set = default_status_id
            logger.info(f"No status_id provided for new task, using default 'OPEN' status ID: {status_id_to_set}")
        else: # status_id was provided, validate it
            status = await self.db_session.get(Status, status_id_to_set)
            if not status: raise ValueError(f"Status with ID '{status_id_to_set}' not found.")

        task_db_data = task_create_data.dict()
        task_db_data['status_id'] = status_id_to_set # Ensure status_id is correctly set

        new_task_db = Task(**task_db_data, created_by_user_id=creator_user_id)

        self.db_session.add(new_task_db)
        try:
            await self.commit()
            # Refresh to get all relationships loaded as defined in get_task_by_id for detailed response
            # This ensures consistency in the response object.
            created_task_detailed = await self.get_task_by_id(new_task_db.id, include_details=True)
            if created_task_detailed:
                logger.info(f"Task '{new_task_db.title}' (ID: {new_task_db.id}) created successfully by user ID '{creator_user_id}'.")
                return created_task_detailed
            else: # Should not happen if commit was successful
                logger.error(f"Failed to retrieve newly created task ID {new_task_db.id} after commit.")
                return None
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error creating task '{task_create_data.title}': {e}", exc_info=True)
            raise ValueError(f"Could not create task due to a data conflict: {e}")
        except Exception as e: # Catch any other errors during commit or re-fetch
            await self.rollback()
            logger.error(f"Unexpected error creating task '{task_create_data.title}': {e}", exc_info=True)
            raise


    async def update_task(self, task_id: UUID, task_update_data: TaskUpdate, current_user_id: UUID) -> Optional[TaskDetailedResponse]:
        logger.debug(f"Attempting to update task ID: {task_id} by user ID: {current_user_id}")

        task_db = await self.db_session.get(Task, task_id)

        if not task_db:
            logger.warning(f"Task ID '{task_id}' not found for update.")
            return None

        update_data = task_update_data.dict(exclude_unset=True)

        if 'task_type_id' in update_data and task_db.task_type_id != update_data['task_type_id']:
            if not await self.db_session.get(TaskType, update_data['task_type_id']):
                raise ValueError(f"New TaskType ID '{update_data['task_type_id']}' not found.")
        if 'status_id' in update_data and task_db.status_id != update_data['status_id']:
            if not await self.db_session.get(Status, update_data['status_id']):
                raise ValueError(f"New Status ID '{update_data['status_id']}' not found.")

        for field, value in update_data.items():
            if hasattr(task_db, field):
                setattr(task_db, field, value)
            else:
                logger.warning(f"Field '{field}' not found on Task model for update of task ID '{task_id}'.")

        if hasattr(task_db, 'updated_by_user_id'):
            task_db.updated_by_user_id = current_user_id
        if hasattr(task_db, 'updated_at'): # Some models might not have this if using DB defaults only
            task_db.updated_at = datetime.now(timezone.utc)

        self.db_session.add(task_db)
        try:
            await self.commit()
            logger.info(f"Task ID '{task_id}' updated successfully by user ID '{current_user_id}'.")
            return await self.get_task_by_id(task_id, include_details=True)
        except Exception as e:
            await self.rollback()
            logger.error(f"Error during task update commit for task ID '{task_id}': {e}", exc_info=True)
            raise

    async def delete_task(self, task_id: UUID, current_user_id: UUID) -> bool:
        logger.debug(f"Attempting to delete task ID: {task_id} by user ID: {current_user_id}")

        task_db = await self.db_session.get(Task, task_id)
        if not task_db:
            logger.warning(f"Task ID '{task_id}' not found for deletion.")
            return False

        await self.db_session.delete(task_db)
        await self.commit()
        logger.info(f"Task ID '{task_id}' deleted successfully by user ID '{current_user_id}'.")
        return True

    async def list_tasks_for_group(
        self, group_id: UUID, skip: int = 0, limit: int = 100,
        status_code: Optional[str] = None, task_type_code: Optional[str] = None,
        include_details: bool = False
    ) -> List[TaskResponse]:
        logger.debug(f"Listing tasks for group ID: {group_id}, status: {status_code}, type: {task_type_code}, details: {include_details}")

        query = select(Task).where(Task.group_id == group_id)
        if include_details:
            query = query.options(
                selectinload(Task.task_type), selectinload(Task.status),
                selectinload(Task.created_by_user).options(selectinload(User.user_type)),
                selectinload(Task.assignments).joinedload(TaskAssignment.user).options(selectinload(User.user_type))
            )
        else:
             query = query.options(selectinload(Task.task_type), selectinload(Task.status))

        if status_code:
            query = query.join(Status, Task.status_id == Status.id).where(Status.code == status_code) # Ensure join is on correct condition
        if task_type_code:
            query = query.join(TaskType, Task.task_type_id == TaskType.id).where(TaskType.code == task_type_code) # Ensure join is on correct condition

        query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)

        result = await self.db_session.execute(query)
        tasks_db = result.scalars().unique().all()

        response_model = TaskDetailedResponse if include_details else TaskResponse
        # response_list = [response_model.model_validate(t) for t in tasks_db] # Pydantic v2
        response_list = [response_model.from_orm(t) for t in tasks_db] # Pydantic v1

        logger.info(f"Retrieved {len(response_list)} tasks for group ID '{group_id}'.")
        return response_list

logger.info("TaskService class defined.")
