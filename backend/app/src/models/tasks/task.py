# backend/app/src/models/tasks/task.py

"""
SQLAlchemy model for Tasks.
"""

import logging
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone, timedelta # Added timezone, timedelta for __main__

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Enum as SQLAlchemyEnum # Added Text, SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseGroupAffiliatedMainModel # Tasks are group-affiliated main entities
from backend.app.src.core.dicts import EventFrequency # Using Enum from core.dicts for recurrence_frequency

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.tasks.assignment import TaskAssignment
    from backend.app.src.models.tasks.completion import TaskCompletion
    from backend.app.src.models.tasks.review import TaskReview
    from backend.app.src.models.dictionaries.task_types import TaskType # For task_type relationship (optional)
    from backend.app.src.models.dictionaries.statuses import Status # For status relationship (optional)
    from backend.app.src.models.groups.group import Group # For group relationship if not via BaseGroupAffiliatedMainModel
    from backend.app.src.models.auth.user import User # For created_by_user_id relationship (optional)

class Task(BaseGroupAffiliatedMainModel): # Inherits id, name, description, state, notes, group_id, created_at, updated_at, deleted_at
    """
    Represents a task within a group.
    Tasks can be assigned, have points, due dates, recurrence, and subtasks.
    """
    __tablename__ = "tasks"

    # 'name', 'description', 'state', 'notes', 'group_id' are inherited from BaseGroupAffiliatedMainModel.
    # 'state' can be used for overall task status if not using status_id, or for a different aspect of state.
    # For specific workflow statuses, status_id is preferred.

    task_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("dict_task_types.id"), nullable=False, index=True, comment="FK to task_types dictionary")
    status_id: Mapped[int] = mapped_column(Integer, ForeignKey("dict_statuses.id"), nullable=False, index=True, comment="FK to statuses dictionary (e.g., Open, In Progress, Completed)")

    points_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="Points awarded or deducted upon completion/non-completion of this task")
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True, comment="Optional due date and time for the task (UTC)")

    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="Is this a recurring task?")
    # recurrence_frequency and recurrence_interval are only relevant if is_recurring is True.
    recurrence_frequency: Mapped[Optional[EventFrequency]] = mapped_column(
        SQLAlchemyEnum(EventFrequency, name="taskeventfrequencyenum", create_constraint=True, native_enum=False), # native_enum=False for string storage
        nullable=True,
        comment="Frequency of recurrence if is_recurring is True (e.g., daily, weekly)"
    )
    recurrence_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Interval for recurrence (e.g., every 2 weeks if frequency is weekly and interval is 2)")
    # next_occurrence_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True, comment="Timestamp of the next scheduled occurrence for recurring tasks")

    parent_task_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=True, index=True, comment="FK to another task, if this is a subtask")

    # 'assignee_type' from plan might be better handled by the nature of TaskAssignment (direct user or role-based assignment there)
    # For simplicity, direct assignment to a user is primarily via TaskAssignment.
    # If a task can be 'unassigned' or 'assigned to anyone in role X', that's more complex.
    # created_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, comment="User who created the task")

    # --- Relationships ---
    task_type: Mapped["TaskType"] = relationship(foreign_keys=[task_type_id]) # Optional: if you need to access TaskType object
    status: Mapped["Status"] = relationship(foreign_keys=[status_id])       # Optional: if you need to access Status object
    # created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_user_id]) # If created_by_user_id is added

    parent_task: Mapped[Optional["Task"]] = relationship(remote_side=[id], back_populates="sub_tasks") # Relationship to parent task
    sub_tasks: Mapped[List["Task"]] = relationship(back_populates="parent_task", cascade="all, delete-orphan") # Relationship to subtasks

    assignments: Mapped[List["TaskAssignment"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    completions: Mapped[List["TaskCompletion"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    reviews: Mapped[List["TaskReview"]] = relationship(back_populates="task", cascade="all, delete-orphan")

    # Group relationship is inherited from BaseGroupAffiliatedMainModel if that base includes it.
    # If BaseGroupAffiliatedMainModel does not define the 'group' relationship object, and group_id is just an FK from mixin:
    # from backend.app.src.models.groups.group import Group # Ensure Group is imported
    # group: Mapped["Group"] = relationship(foreign_keys=[group_id]) # Assuming group_id is the column name from GroupAffiliationMixin

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        group_id_val = getattr(self, 'group_id', 'N/A')
        return f"<Task(id={id_val}, name='{self.name}', group_id={group_id_val}, status_id={self.status_id})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Task Model --- Demonstration")

    # Example Task instance
    # Assume Group with id=1, TaskType with id=1, Status with id=1 exist
    task1 = Task(
        name="Weekly Kitchen Cleaning",
        description="Clean the kitchen thoroughly: surfaces, floor, microwave.",
        group_id=1,
        task_type_id=1, # e.g., 'CHORE'
        status_id=1,    # e.g., 'OPEN'
        points_value=50,
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        is_recurring=True,
        recurrence_frequency=EventFrequency.WEEKLY,
        recurrence_interval=1,
        state="active" # from BaseMainModel
    )
    task1.id = 1 # Simulate ORM-set ID
    task1.created_at = datetime.now(timezone.utc)
    task1.updated_at = datetime.now(timezone.utc)

    logger.info(f"Example Task: {task1!r}")
    logger.info(f"  Name: {task1.name}")
    logger.info(f"  Points: {task1.points_value}")
    logger.info(f"  Due Date: {task1.due_date.isoformat() if task1.due_date else 'N/A'}")
    logger.info(f"  Is Recurring: {task1.is_recurring}, Frequency: {task1.recurrence_frequency.value if task1.recurrence_frequency else 'N/A'}")
    logger.info(f"  Created At: {task1.created_at.isoformat() if task1.created_at else 'N/A'}")


    subtask = Task(
        name="Clean Microwave",
        description="Part of weekly kitchen cleaning.",
        group_id=1,
        task_type_id=1,
        status_id=1,
        points_value=10,
        parent_task_id=task1.id # Link to task1
    )
    subtask.id = 2
    logger.info(f"Example Subtask: {subtask!r} (parent_id: {subtask.parent_task_id})")

    # To view relationships, a DB session and related objects would be needed.
    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"Task attributes (conceptual table columns): {[c.name for c in Task.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
