# backend/app/src/repositories/tasks/task_repository.py

"""
Repository for Task entities.
Provides CRUD operations and specific methods for managing tasks.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone # Added timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_ # Added and_ for combining conditions

from backend.app.src.models.tasks.task import Task
from backend.app.src.schemas.tasks.task import TaskCreate, TaskUpdate
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.core.dicts import EventFrequency # For type hinting

logger = logging.getLogger(__name__)

class TaskRepository(BaseRepository[Task, TaskCreate, TaskUpdate]):
    """
    Repository for managing Task records.
    """

    def __init__(self):
        super().__init__(Task)

    async def get_tasks_for_group(
        self,
        db: AsyncSession,
        *,
        group_id: int,
        status_id: Optional[int] = None,
        task_type_id: Optional[int] = None,
        include_deleted: bool = False, # If soft delete is used
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        Retrieves tasks for a specific group, optionally filtered by status and task type.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            status_id: Optional. Filter by a specific status ID.
            task_type_id: Optional. Filter by a specific task type ID.
            include_deleted: Optional. If True, includes soft-deleted tasks.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of Task objects.
        """
        conditions = [self.model.group_id == group_id] # type: ignore[attr-defined]
        if status_id is not None:
            conditions.append(self.model.status_id == status_id) # type: ignore[attr-defined]
        if task_type_id is not None:
            conditions.append(self.model.task_type_id == task_type_id) # type: ignore[attr-defined]

        if not include_deleted and hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.due_date.asc().nulls_last(), self.model.name.asc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_tasks_by_parent_id(
        self, db: AsyncSession, *, parent_task_id: int, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """
        Retrieves subtasks for a specific parent task.

        Args:
            db: The SQLAlchemy asynchronous database session.
            parent_task_id: The ID of the parent task.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of Task objects (subtasks).
        """
        statement = (
            select(self.model)
            .where(self.model.parent_task_id == parent_task_id) # type: ignore[attr-defined]
            .order_by(self.model.created_at.asc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_tasks_due_soon(
        self, db: AsyncSession, *, due_before: datetime, group_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """
        Retrieves tasks that are due before a specific datetime.
        Optionally filters by group_id. Excludes completed/archived tasks implicitly by status_id logic (not implemented here, assumes active statuses).

        Args:
            db: The SQLAlchemy asynchronous database session.
            due_before: The datetime threshold for due dates.
            group_id: Optional. Filter by a specific group ID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of Task objects due soon.
        """
        now = datetime.now(timezone.utc)
        conditions = [
            self.model.due_date != None, # type: ignore[attr-defined]
            self.model.due_date >= now, # type: ignore[attr-defined] # Due in the future
            self.model.due_date <= due_before # type: ignore[attr-defined]
        ]
        if group_id is not None:
            conditions.append(self.model.group_id == group_id) # type: ignore[attr-defined]

        # Add condition to exclude tasks that are already in a 'final' state (e.g., completed, cancelled)
        # This requires knowledge of status codes or a 'is_final' flag on Status model.
        # Example:
        # from backend.app.src.models.dictionaries.statuses import Status # Assuming Status model can be queried
        # final_status_codes = ["COMPLETED", "CANCELLED", "ARCHIVED"] # Example
        # final_statuses_stmt = select(Status.id).where(Status.code.in_(final_status_codes))
        # final_status_ids = list((await db.execute(final_statuses_stmt)).scalars().all())
        # if final_status_ids:
        #    conditions.append(self.model.status_id.notin_(final_status_ids))


        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.due_date.asc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_recurring_tasks_to_instance(self, db: AsyncSession, *, current_time: Optional[datetime] = None) -> List[Task]:
        """
        Retrieves recurring task templates that may need new instances created.
        Logic for determining if a new instance is needed (based on last_occurrence or similar)
        would typically be in the service layer, but this method provides the raw recurring tasks.

        Args:
            db: The SQLAlchemy asynchronous database session.
            current_time: The current time to evaluate against. Defaults to now(UTC).

        Returns:
            A list of Task objects that are marked as recurring.
        """
        conditions = [self.model.is_recurring == True] # type: ignore[attr-defined]

        statement = select(self.model).where(*conditions)
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def search_tasks(
        self,
        db: AsyncSession,
        *,
        group_id: int,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        Searches for tasks within a specific group by a search term matching name or description.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group to search within.
            search_term: The term to search for.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of Task objects matching the search criteria.
        """
        search_filter = f"%{search_term.lower()}%"
        conditions = [
            self.model.group_id == group_id, # type: ignore[attr-defined]
            or_(
                self.model.name.ilike(search_filter), # type: ignore[attr-defined]
                self.model.description.ilike(search_filter) # type: ignore[attr-defined]
            )
        ]
        if hasattr(self.model, "deleted_at"): # Exclude soft-deleted by default
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.due_date.asc().nulls_last(), self.model.name.asc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    # BaseRepository methods create, get, update, remove are inherited.
    # Task creation will need group_id, task_type_id, status_id, etc., handled by service.
    # Task updates will use TaskUpdate schema.
