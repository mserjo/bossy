# backend/app/src/services/tasks/assignment.py
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.tasks.assignment import TaskAssignment # SQLAlchemy TaskAssignment model
from app.src.models.tasks.task import Task # For task context
from app.src.models.tasks.event import Event # For event context (if assignments can be to events too)
from app.src.models.auth.user import User # For user context

from app.src.schemas.tasks.assignment import ( # Pydantic Schemas
    TaskAssignmentCreate, # Although not directly used as input to assign_task_to_user, good for consistency
    # TaskAssignmentUpdate, # Assignments are often immutable; changes = new assignment or unassign/reassign
    TaskAssignmentResponse
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class TaskAssignmentService(BaseService):
    """
    Service for managing assignments of tasks (or events) to users.
    Handles creating, retrieving, and removing assignments.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("TaskAssignmentService initialized.")

    async def assign_task_to_user(
        self,
        task_id: UUID,
        user_id: UUID,
        assigned_by_user_id: Optional[UUID] = None,
        # Assuming TaskAssignment model has only task_id FK for simplicity now.
        # If it can also link to events (e.g. event_id FK), item_type parameter would be needed.
    ) -> TaskAssignmentResponse:
        """
        Assigns a task to a user.
        Prevents duplicate active assignments. Reactivates inactive assignments.
        """
        logger.debug(f"Attempting to assign task ID '{task_id}' to user ID '{user_id}'.")

        item_to_assign = await self.db_session.get(Task, task_id)
        if not item_to_assign: raise ValueError(f"Task with ID '{task_id}' not found.")

        user = await self.db_session.get(User, user_id)
        if not user: raise ValueError(f"User with ID '{user_id}' not found.")

        existing_assignment_stmt = select(TaskAssignment).where(
            TaskAssignment.task_id == task_id,
            TaskAssignment.user_id == user_id
        ) # Fetch regardless of active status first
        assignment_db = (await self.db_session.execute(existing_assignment_stmt)).scalar_one_or_none()

        if assignment_db:
            if assignment_db.is_active:
                logger.warning(f"User ID '{user_id}' is already actively assigned to task ID '{task_id}'.")
                # Return existing active assignment rather than raising error
                await self.db_session.refresh(assignment_db, attribute_names=['user', 'task']) # Ensure fresh for response
                return TaskAssignmentResponse.from_orm(assignment_db) # Pydantic v1
                # For Pydantic v2: return TaskAssignmentResponse.model_validate(assignment_db)
            else: # Is inactive, reactivate
                logger.info(f"Reactivating existing assignment for user ID '{user_id}' to task ID '{task_id}'.")
                assignment_db.is_active = True
                assignment_db.assigned_at = datetime.now(timezone.utc)
                if hasattr(assignment_db, 'assigned_by_user_id') and assigned_by_user_id: # Check model attribute
                    assignment_db.assigned_by_user_id = assigned_by_user_id
        else: # No existing assignment, create new
            create_data = {
                "task_id": task_id,
                "user_id": user_id,
                "is_active": True
            }
            if hasattr(TaskAssignment, 'assigned_by_user_id') and assigned_by_user_id:
                create_data['assigned_by_user_id'] = assigned_by_user_id

            assignment_db = TaskAssignment(**create_data)
            self.db_session.add(assignment_db)

        try:
            await self.commit()
            await self.db_session.refresh(assignment_db, attribute_names=['user', 'task'])
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error assigning task ID '{task_id}' to user ID '{user_id}': {e}", exc_info=True)
            # This might happen if a unique constraint on (task_id, user_id) exists and an inactive record was missed
            # by initial checks (e.g. race condition, or if logic changes).
            raise ValueError(f"Could not assign task due to a data conflict: {e}")

        logger.info(f"Successfully assigned task ID '{task_id}' to user ID '{user_id}'. Assignment ID: {assignment_db.id}")
        # return TaskAssignmentResponse.model_validate(assignment_db) # Pydantic v2
        return TaskAssignmentResponse.from_orm(assignment_db) # Pydantic v1

    async def unassign_task_from_user(
        self,
        task_id: UUID,
        user_id: UUID,
        unassigned_by_user_id: Optional[UUID] = None # For audit
    ) -> bool:
        """
        Unassigns a user from a task by deactivating the assignment.
        """
        logger.debug(f"Attempting to unassign user ID '{user_id}' from task ID '{task_id}'.")

        assignment_stmt = select(TaskAssignment).where(
            TaskAssignment.task_id == task_id,
            TaskAssignment.user_id == user_id,
            TaskAssignment.is_active == True
        )
        assignment_db = (await self.db_session.execute(assignment_stmt)).scalar_one_or_none()

        if not assignment_db:
            logger.warning(f"No active assignment found for user ID '{user_id}' on task ID '{task_id}'. Cannot unassign.")
            return False

        assignment_db.is_active = False
        if hasattr(assignment_db, 'unassigned_at'): # Check model attribute
            assignment_db.unassigned_at = datetime.now(timezone.utc)
        if hasattr(assignment_db, 'unassigned_by_user_id') and unassigned_by_user_id: # Check model attribute
            assignment_db.unassigned_by_user_id = unassigned_by_user_id

        self.db_session.add(assignment_db)
        await self.commit()

        logger.info(f"User ID '{user_id}' successfully unassigned (deactivated) from task ID '{task_id}'.")
        return True

    async def list_assignments_for_task(
        self,
        task_id: UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = True
    ) -> List[TaskAssignmentResponse]:
        logger.debug(f"Listing assignments for task ID '{task_id}', is_active: {is_active}, skip={skip}, limit={limit}")

        stmt = select(TaskAssignment).options(
            selectinload(TaskAssignment.user).options(selectinload(User.user_type)),
            selectinload(TaskAssignment.task)
        ).where(TaskAssignment.task_id == task_id)

        if is_active is not None:
            stmt = stmt.where(TaskAssignment.is_active == is_active)

        stmt = stmt.join(User, TaskAssignment.user_id == User.id).               order_by(User.username).               offset(skip).               limit(limit)

        result = await self.db_session.execute(stmt)
        assignments_db = result.scalars().unique().all()

        # response_list = [TaskAssignmentResponse.model_validate(a) for a in assignments_db] # Pydantic v2
        response_list = [TaskAssignmentResponse.from_orm(a) for a in assignments_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} assignments for task ID '{task_id}'.")
        return response_list

    async def list_tasks_for_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        is_active_assignment: Optional[bool] = True,
    ) -> List[TaskAssignmentResponse]:
        logger.debug(f"Listing tasks assigned to user ID: {user_id}, active_assignment: {is_active_assignment}, skip={skip}, limit={limit}")

        stmt = select(TaskAssignment).options(
            selectinload(TaskAssignment.user).options(selectinload(User.user_type)), # Load user type for context
            selectinload(TaskAssignment.task).options(
                selectinload(Task.task_type),
                selectinload(Task.status),
                selectinload(Task.group)
            )
        ).where(TaskAssignment.user_id == user_id)

        if is_active_assignment is not None:
            stmt = stmt.where(TaskAssignment.is_active == is_active_assignment)

        # Order by task's due_date or created_at. Need to join Task to access these.
        # isouter=True in case an assignment somehow exists for a deleted task (though FKs should prevent)
        stmt = stmt.join(Task, TaskAssignment.task_id == Task.id, isouter=True).order_by(
            getattr(Task, 'due_date', Task.created_at).desc() if Task is not None else TaskAssignment.assigned_at.desc() # type: ignore
        ).offset(skip).limit(limit)

        result = await self.db_session.execute(stmt)
        assignments_db = result.scalars().unique().all()

        # response_list = [TaskAssignmentResponse.model_validate(a) for a in assignments_db] # Pydantic v2
        response_list = [TaskAssignmentResponse.from_orm(a) for a in assignments_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} assigned items for user ID '{user_id}'.")
        return response_list

    async def get_assignment_details(self, assignment_id: UUID) -> Optional[TaskAssignmentResponse]:
        logger.debug(f"Getting assignment details for assignment ID {assignment_id}")
        stmt = select(TaskAssignment).options(
            selectinload(TaskAssignment.user).options(selectinload(User.user_type)),
            selectinload(TaskAssignment.task).options(
                selectinload(Task.task_type),
                selectinload(Task.status),
                selectinload(Task.group) # Added group for completeness
            ),
            selectinload(TaskAssignment.assigned_by).options(selectinload(User.user_type)) if hasattr(TaskAssignment, 'assigned_by') else None # Conditionally load if field exists
        ).where(TaskAssignment.id == assignment_id)

        # Filter out None options if any were conditionally added
        stmt = stmt.options(*(opt for opt in stmt.get_options() if opt is not None))

        assignment_db = (await self.db_session.execute(stmt)).scalar_one_or_none()
        if not assignment_db:
            logger.info(f"No assignment found for ID {assignment_id}")
            return None

        # return TaskAssignmentResponse.model_validate(assignment_db) # Pydantic v2
        return TaskAssignmentResponse.from_orm(assignment_db) # Pydantic v1

logger.info("TaskAssignmentService class defined.")
