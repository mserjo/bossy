# backend/app/src/models/tasks/assignment.py

"""
SQLAlchemy model for Task Assignments, linking Users to Tasks (or potentially Events).
"""

import logging
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone # Added timezone for __main__
from enum import Enum as PythonEnum # For AssignmentStatusEnum

from sqlalchemy import ForeignKey, DateTime, String, Enum as SQLAlchemyEnum, UniqueConstraint, Integer # Added Integer for FKs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func # For server_default on assigned_at

from backend.app.src.models.base import BaseModel # Assignments are simpler entities

# Configure logger for this module
logger = logging.getLogger(__name__)

class AssignmentStatusEnum(PythonEnum): # Changed to inherit from PythonEnum
    """ Defines the status of a task/event assignment to a user. """
    PENDING = "pending"       # Assignment made, awaiting user acknowledgement or start.
    ACCEPTED = "accepted"     # User has accepted or acknowledged the assignment.
    IN_PROGRESS = "in_progress" # User has started working on the assigned item.
    DECLINED = "declined"     # User has declined the assignment.
    # COMPLETED/CANCELLED statuses are usually on the Task/Event itself or TaskCompletion.

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.tasks.task import Task
    # from backend.app.src.models.tasks.event import Event # If events can also be assigned

class TaskAssignment(BaseModel):
    """
    Represents the assignment of a Task to a User.
    Can also be adapted to assign Events if needed by making task_id nullable and adding event_id.

    Attributes:
        task_id (int): Foreign key to the task being assigned.
        user_id (int): Foreign key to the user to whom the task is assigned.
        assigned_by_user_id (Optional[int]): Foreign key to the user who made the assignment (if applicable).
        status (AssignmentStatusEnum): Current status of this assignment (e.g., pending, accepted).
        assigned_at (datetime): Timestamp when the assignment was made.
        # `id`, `created_at`, `updated_at` from BaseModel.
    """
    __tablename__ = "task_assignments"

    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False, index=True, comment="FK to the task being assigned")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="FK to the user the task is assigned to")

    assigned_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="FK to the user who made the assignment (null if system-assigned or self-assigned)")

    status: Mapped[AssignmentStatusEnum] = mapped_column(
        SQLAlchemyEnum(AssignmentStatusEnum, name="assignmentstatusenum", create_constraint=True, native_enum=False), # native_enum=False for string storage
        nullable=False,
        default=AssignmentStatusEnum.PENDING,
        index=True,
        comment="Current status of the assignment (e.g., pending, accepted)"
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the assignment was made (UTC)"
    )

    # If TaskAssignments can link to Events too (polymorphic-like or just another FK):
    # event_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("events.id"), nullable=True, index=True)
    # from sqlalchemy import CheckConstraint # Would need this import
    # __table_args__ = (
    #     CheckConstraint('(task_id IS NOT NULL AND event_id IS NULL) OR (task_id IS NULL AND event_id IS NOT NULL)', name='chk_assignment_target_exclusive'),
    #     UniqueConstraint('task_id', 'user_id', name='uq_task_user_assignment'), # Keep this if task_id is main target
    #     UniqueConstraint('event_id', 'user_id', name='uq_event_user_assignment'), # Add this if event_id is also possible
    # )
    # If supporting both, the single UniqueConstraint on (task_id, user_id) might need to be part of the CheckConstraint logic
    # or handled differently, e.g., by having separate assignment tables or allowing NULLs in the unique constraint components if DB supports it.

    # --- Relationships ---
    task: Mapped["Task"] = relationship(back_populates="assignments")
    user: Mapped["User"] = relationship(back_populates="task_assignments", foreign_keys=[user_id])
    assigned_by: Mapped[Optional["User"]] = relationship(foreign_keys=[assigned_by_user_id]) # One-way, or add back_populates to User if needed
    # event: Mapped[Optional["Event"]] = relationship() # If event_id is added

    # --- Table Arguments ---
    # Ensure a user can only be assigned to a specific task once directly.
    # If multiple assignments are possible (e.g., re-assignment after decline), this might need adjustment
    # or rely on status changes of a single assignment record.
    __table_args__ = (
        UniqueConstraint('task_id', 'user_id', name='uq_task_user_assignment'),
    )

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<TaskAssignment(id={id_val}, task_id={self.task_id}, user_id={self.user_id}, status='{self.status.value}')>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- TaskAssignment Model --- Demonstration")

    # Example TaskAssignment instance
    # Assume Task id=1, User id=1 (assignee), User id=2 (assigner) exist
    assignment1 = TaskAssignment(
        task_id=1,
        user_id=1,
        assigned_by_user_id=2,
        status=AssignmentStatusEnum.PENDING
        # assigned_at is auto-set by server_default
    )
    assignment1.id = 1 # Simulate ORM-set ID
    assignment1.created_at = datetime.now(timezone.utc) # Simulate BaseModel field
    assignment1.updated_at = datetime.now(timezone.utc) # Simulate BaseModel field
    # For demo, we'll set assigned_at manually if server_default not active in this context
    if not getattr(assignment1, 'assigned_at', None): # Check if assigned_at was set (SQLAlchemy might not run server_default without a session)
        assignment1.assigned_at = datetime.now(timezone.utc)


    logger.info(f"Example TaskAssignment: {assignment1!r}")
    logger.info(f"  Task ID: {assignment1.task_id}, User ID (Assignee): {assignment1.user_id}")
    logger.info(f"  Assigned By User ID: {assignment1.assigned_by_user_id}")
    logger.info(f"  Status: {assignment1.status.value}")
    logger.info(f"  Assigned At: {assignment1.assigned_at.isoformat() if assignment1.assigned_at else 'N/A'}")
    logger.info(f"  Created At: {assignment1.created_at.isoformat() if assignment1.created_at else 'N/A'}")


    assignment2 = TaskAssignment(
        task_id=2, # Assuming task with id=2 exists
        user_id=3, # Assuming user with id=3 exists
        status=AssignmentStatusEnum.ACCEPTED
    )
    assignment2.id = 2
    logger.info(f"Example TaskAssignment 2 (self/system assigned): {assignment2!r}")
    logger.info(f"  Assigned By (should be None): {assignment2.assigned_by_user_id}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"TaskAssignment attributes (conceptual table columns): {[c.name for c in TaskAssignment.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
