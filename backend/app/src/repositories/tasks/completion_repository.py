# backend/app/src/repositories/tasks/completion_repository.py

"""
Repository for TaskCompletion entities.
Provides CRUD operations and specific methods for managing task completions.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update # Added update for verification

from backend.app.src.models.tasks.completion import TaskCompletion
from backend.app.src.schemas.tasks.completion import TaskCompletionCreate, TaskCompletionVerify # Using TaskCompletionVerify for updates
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class TaskCompletionRepository(BaseRepository[TaskCompletion, TaskCompletionCreate, TaskCompletionVerify]):
    """
    Repository for managing TaskCompletion records.
    """

    def __init__(self):
        super().__init__(TaskCompletion)

    async def get_completions_for_task(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        user_id: Optional[int] = None,
        is_verified: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskCompletion]:
        """
        Retrieves all completion records for a specific task,
        optionally filtered by user and verification status.

        Args:
            db: The SQLAlchemy asynchronous database session.
            task_id: The ID of the task.
            user_id: Optional. Filter by a specific user who completed the task.
            is_verified: Optional. Filter by verification status.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of TaskCompletion objects.
        """
        conditions = [self.model.task_id == task_id] # type: ignore[attr-defined]
        if user_id is not None:
            conditions.append(self.model.user_id == user_id) # type: ignore[attr-defined]
        if is_verified is not None:
            conditions.append(self.model.is_verified == is_verified) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.completed_at.desc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_completions_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        is_verified: Optional[bool] = None,
        task_id: Optional[int] = None, # Optional filter by task
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskCompletion]:
        """
        Retrieves all task completions submitted by a specific user,
        optionally filtered by verification status and task.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
            is_verified: Optional. Filter by verification status.
            task_id: Optional. Filter by a specific task ID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of TaskCompletion objects.
        """
        conditions = [self.model.user_id == user_id] # type: ignore[attr-defined]
        if is_verified is not None:
            conditions.append(self.model.is_verified == is_verified) # type: ignore[attr-defined]
        if task_id is not None:
            conditions.append(self.model.task_id == task_id) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.completed_at.desc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def verify_completion(
        self,
        db: AsyncSession,
        *,
        completion_id: int,
        verifier_id: int,
        awarded_points: Optional[int] = None,
        verification_notes: Optional[str] = None
    ) -> Optional[TaskCompletion]:
        """
        Marks a task completion as verified.

        Args:
            db: The SQLAlchemy asynchronous database session.
            completion_id: The ID of the TaskCompletion record.
            verifier_id: The ID of the user verifying the completion.
            awarded_points: Optional. Points to award for this completion.
            verification_notes: Optional. Notes from the verifier.

        Returns:
            The updated TaskCompletion object if found, otherwise None.
        """
        db_obj = await self.get(db, id=completion_id)
        if db_obj:
            db_obj.is_verified = True # type: ignore[union-attr]
            db_obj.verified_at = datetime.now(timezone.utc) # type: ignore[union-attr]
            db_obj.verifier_id = verifier_id # type: ignore[union-attr]
            if awarded_points is not None:
                db_obj.awarded_points = awarded_points # type: ignore[union-attr]
            if verification_notes is not None:
                db_obj.verification_notes = verification_notes # type: ignore[union-attr]

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        return None

    async def reject_completion(
        self,
        db: AsyncSession,
        *,
        completion_id: int,
        verifier_id: int,
        verification_notes: Optional[str] = None
    ) -> Optional[TaskCompletion]:
        """
        Marks a task completion as not verified (e.g., rejected).

        Args:
            db: The SQLAlchemy asynchronous database session.
            completion_id: The ID of the TaskCompletion record.
            verifier_id: The ID of the user marking as not verified.
            verification_notes: Optional. Notes explaining the rejection/change.

        Returns:
            The updated TaskCompletion object if found, otherwise None.
        """
        db_obj = await self.get(db, id=completion_id)
        if db_obj:
            db_obj.is_verified = False # type: ignore[union-attr]
            db_obj.verified_at = datetime.now(timezone.utc) # type: ignore[union-attr]
            db_obj.verifier_id = verifier_id # type: ignore[union-attr]
            if verification_notes is not None:
                db_obj.verification_notes = verification_notes # type: ignore[union-attr]

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        return None

    async def get_completion_for_task_and_user(
        self, db: AsyncSession, *, task_id: int, user_id: int
    ) -> Optional[TaskCompletion]:
        """
        Retrieves a specific completion record for a task by a user.
        Returns the most recent one if multiple exist.

        Args:
            db: The SQLAlchemy asynchronous database session.
            task_id: The ID of the task.
            user_id: The ID of the user.

        Returns:
            The TaskCompletion object if found (typically the latest if multiple), otherwise None.
        """
        statement = (
            select(self.model)
            .where(
                self.model.task_id == task_id, # type: ignore[attr-defined]
                self.model.user_id == user_id  # type: ignore[attr-defined]
            )
            .order_by(self.model.completed_at.desc()) # type: ignore[attr-defined]
        )
        result = await db.execute(statement)
        return result.scalars().first() # Use .first() to get one or None

    # BaseRepository methods create, get, update, remove are inherited.
    # `create` uses TaskCompletionCreate. `task_id` and `user_id` set by service.
    # `update` (generic) uses TaskCompletionVerify schema for this repo.
    # `remove` hard deletes a completion record.
