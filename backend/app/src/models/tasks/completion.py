# backend/app/src/models/tasks/completion.py

"""
SQLAlchemy model for Task Completions, recording when a user completes a task
and details about its verification and awarded points.
"""

import logging
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone, timedelta # Added timezone, timedelta for __main__

from sqlalchemy import ForeignKey, DateTime, Text, Integer, Boolean # Added Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func # For server_default on completed_at

from backend.app.src.models.base import BaseModel

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.tasks.task import Task
    # from backend.app.src.models.tasks.assignment import TaskAssignment # If linking completion to a specific assignment record

class TaskCompletion(BaseModel):
    """
    Represents the completion of a Task by a User.

    Attributes:
        task_id (int): Foreign key to the task that was completed.
        user_id (int): Foreign key to the user who completed the task.
        # assignment_id (Optional[int]): FK to a specific TaskAssignment record, if applicable.
        completed_at (datetime): Timestamp when the user marked the task as completed.
        is_verified (bool): Whether the completion has been verified by an admin/owner.
        verified_at (Optional[datetime]): Timestamp when the verification occurred.
        verifier_id (Optional[int]): Foreign key to the user who verified the completion.
        verification_notes (Optional[str]): Notes from the verifier.
        awarded_points (Optional[int]): Points actually awarded for this completion (might differ from task's default points_value).
        # `id`, `created_at`, `updated_at` from BaseModel.
    """
    __tablename__ = "task_completions"

    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False, index=True, comment="FK to the completed task")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="FK to the user who completed the task")

    # If a task can be completed multiple times by the same user (e.g. recurring tasks without distinct assignments for each recurrence),
    # then (task_id, user_id) might not be unique. A UniqueConstraint might be on (task_id, user_id, completed_at) or similar.
    # For now, assuming one primary completion record per user for a given non-recurring task instance.
    # If linking to a specific assignment:
    # assignment_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("task_assignments.id"), nullable=True, index=True, unique=True)

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the user marked the task as completed (UTC)"
    )

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True, comment="Has this completion been verified by an admin/owner?")
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="Timestamp of verification (UTC)")
    verifier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="FK to the user who verified the completion")
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Notes or comments from the verifier")

    awarded_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Actual points awarded for this specific completion instance")

    # --- Relationships ---
    task: Mapped["Task"] = relationship(back_populates="completions")
    user: Mapped["User"] = relationship(foreign_keys=[user_id]) # Assuming User model has a 'completions' backref if needed, or keep one-way
    verifier: Mapped[Optional["User"]] = relationship(foreign_keys=[verifier_id])
    # assignment: Mapped[Optional["TaskAssignment"]] = relationship() # If assignment_id is used

    # Consider a UniqueConstraint if a user can only complete a specific task once.
    # This depends on business logic (e.g., recurring tasks might allow multiple completions).
    # from sqlalchemy import UniqueConstraint # Import if using
    # __table_args__ = (UniqueConstraint('task_id', 'user_id', name='uq_task_user_completion'),)

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<TaskCompletion(id={id_val}, task_id={self.task_id}, user_id={self.user_id}, verified={self.is_verified})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- TaskCompletion Model --- Demonstration")

    # Example TaskCompletion instance
    # Assume Task id=1, User id=1 (completer), User id=2 (verifier) exist
    completion1 = TaskCompletion(
        task_id=1,
        user_id=1,
        # completed_at is auto-set by server_default
        is_verified=True,
        verified_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        verifier_id=2,
        verification_notes="Well done!",
        awarded_points=55 # Task might be 50, but verifier awarded bonus points
    )
    completion1.id = 1 # Simulate ORM-set ID
    completion1.created_at = datetime.now(timezone.utc)
    completion1.updated_at = datetime.now(timezone.utc)
    if not getattr(completion1, 'completed_at', None): # For demo if server_default not active
        completion1.completed_at = datetime.now(timezone.utc)


    logger.info(f"Example TaskCompletion: {completion1!r}")
    logger.info(f"  Task ID: {completion1.task_id}, User ID: {completion1.user_id}")
    logger.info(f"  Completed At: {completion1.completed_at.isoformat() if completion1.completed_at else 'N/A'}")
    logger.info(f"  Is Verified: {completion1.is_verified}, Verified At: {completion1.verified_at.isoformat() if completion1.verified_at else 'N/A'}, Verifier ID: {completion1.verifier_id}")
    logger.info(f"  Awarded Points: {completion1.awarded_points}")
    logger.info(f"  Verification Notes: {completion1.verification_notes}")
    logger.info(f"  Created At: {completion1.created_at.isoformat() if completion1.created_at else 'N/A'}")


    completion2_pending = TaskCompletion(
        task_id=2, # Assuming task 2 exists
        user_id=3, # Assuming user 3 exists
        is_verified=False,
        awarded_points=20 # Points might be pre-set but not confirmed until verification
    )
    completion2_pending.id = 2
    logger.info(f"Example Pending TaskCompletion: {completion2_pending!r}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"TaskCompletion attributes (conceptual table columns): {[c.name for c in TaskCompletion.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
