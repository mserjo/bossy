# backend/app/src/repositories/tasks/assignment_repository.py

"""
Repository for TaskAssignment entities.
Provides CRUD operations and specific methods for managing task assignments.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone # Added timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update # Added update

from backend.app.src.models.tasks.assignment import TaskAssignment, AssignmentStatusEnum
from backend.app.src.schemas.tasks.assignment import TaskAssignmentCreate, TaskAssignmentUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class TaskAssignmentRepository(BaseRepository[TaskAssignment, TaskAssignmentCreate, TaskAssignmentUpdate]):
    """
    Repository for managing TaskAssignment records.
    """

    def __init__(self):
        super().__init__(TaskAssignment)

    async def get_assignments_for_task(
        self, db: AsyncSession, *, task_id: int, status: Optional[AssignmentStatusEnum] = None, skip: int = 0, limit: int = 100
    ) -> List[TaskAssignment]:
        """
        Retrieves all assignments for a specific task, optionally filtered by status.

        Args:
            db: The SQLAlchemy asynchronous database session.
            task_id: The ID of the task.
            status: Optional. Filter by a specific assignment status.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of TaskAssignment objects.
        """
        conditions = [self.model.task_id == task_id] # type: ignore[attr-defined]
        if status:
            conditions.append(self.model.status == status) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.assigned_at.desc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_assignments_for_user(
        self, db: AsyncSession, *, user_id: int, status: Optional[AssignmentStatusEnum] = None, skip: int = 0, limit: int = 100
    ) -> List[TaskAssignment]:
        """
        Retrieves all assignments for a specific user, optionally filtered by status.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
            status: Optional. Filter by a specific assignment status.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of TaskAssignment objects.
        """
        conditions = [self.model.user_id == user_id] # type: ignore[attr-defined]
        if status:
            conditions.append(self.model.status == status) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.assigned_at.desc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_assignment_for_task_and_user(
        self, db: AsyncSession, *, task_id: int, user_id: int
    ) -> Optional[TaskAssignment]:
        """
        Retrieves a specific assignment for a task and user.
        Relies on the UniqueConstraint('task_id', 'user_id') on the model.

        Args:
            db: The SQLAlchemy asynchronous database session.
            task_id: The ID of the task.
            user_id: The ID of the user.

        Returns:
            The TaskAssignment object if found, otherwise None.
        """
        statement = select(self.model).where(
            self.model.task_id == task_id, # type: ignore[attr-defined]
            self.model.user_id == user_id # type: ignore[attr-defined]
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def update_assignment_status(
        self, db: AsyncSession, *, assignment_id: int, new_status: AssignmentStatusEnum
    ) -> Optional[TaskAssignment]:
        """
        Updates the status of a specific task assignment.

        Args:
            db: The SQLAlchemy asynchronous database session.
            assignment_id: The ID of the TaskAssignment record to update.
            new_status: The new AssignmentStatusEnum value.

        Returns:
            The updated TaskAssignment object if found and updated, otherwise None.
        """
        db_obj = await self.get(db, id=assignment_id)
        if db_obj:
            if db_obj.status == new_status: # type: ignore[union-attr]
                return db_obj # No change needed

            db_obj.status = new_status # type: ignore[union-attr]
            db_obj.updated_at = datetime.now(timezone.utc) # type: ignore[union-attr] # Manually update if not relying on super().update
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        return None

    # BaseRepository methods create, get, update, remove are inherited.
    # `create` uses TaskAssignmentCreate. `assigned_by_user_id` and `task_id` are expected to be set by service.
    # `update` uses TaskAssignmentUpdate (mainly for status).
    # `remove` hard deletes an assignment.
