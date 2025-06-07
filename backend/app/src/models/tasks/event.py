# backend/app/src/models/tasks/event.py

"""
SQLAlchemy model for Events.
Events can be similar to tasks but might represent appointments, milestones, or informational items.
"""

import logging
from typing import Optional, List, TYPE_CHECKING # List and TYPE_CHECKING might not be needed if no new relationships
from datetime import datetime, timezone, timedelta # Added timezone, timedelta for __main__

from sqlalchemy import String, DateTime, ForeignKey, Integer # Added Integer for FKs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseGroupAffiliatedMainModel # Events are also group-affiliated main entities
# from backend.app.src.core.dicts import EventFrequency # If events also have recurrence

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    # from backend.app.src.models.dictionaries.task_types import TaskType # If using task_types for event_type
    # Or define a new dict_event_types table and model
    # from backend.app.src.models.auth.user import User # For created_by_user_id if added
    # from backend.app.src.models.tasks.assignment import TaskAssignment # If events can be assigned like tasks
    pass # Add other forward references if needed

class Event(BaseGroupAffiliatedMainModel): # Inherits id, name, description, state, notes, group_id, created_at, updated_at, deleted_at
    """
    Represents an event within a group (e.g., meeting, appointment, milestone, holiday).
    Similar to a Task, but might have different emphasis on fields like start/end times and location.
    """
    __tablename__ = "events"

    # 'name', 'description', 'state', 'notes', 'group_id' are inherited.
    # 'state' could represent 'upcoming', 'ongoing', 'past', 'cancelled'.

    # It's possible that an 'event_type_id' (FK to dict_task_types or a new dict_event_types) could be useful.
    # For now, we'll assume the distinction from Task is mainly semantic or through fewer specific Task fields.
    # event_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("dict_event_types.id"), index=True, comment="FK to event_types dictionary")

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True, comment="Start date and time of the event (UTC)")
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True, comment="Optional end date and time of the event (UTC)")
    location: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="Physical or virtual location of the event")

    # If events can be recurring, similar fields to Task model would be needed:
    # is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # recurrence_frequency: Mapped[Optional[EventFrequency]] = mapped_column(SQLAlchemyEnum(EventFrequency), nullable=True)
    # recurrence_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # If events can be assigned or have completions/reviews, relationships similar to Task would be needed.
    # For now, keeping Event simpler. Relationships can be added if requirements evolve.
    # assignments: Mapped[List["TaskAssignment"]] = relationship(back_populates="event") # Requires TaskAssignment to also link to Event

    # created_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, comment="User who created the event")
    # created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_user_id])

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        group_id_val = getattr(self, 'group_id', 'N/A')
        start_time_val = self.start_time.isoformat() if self.start_time else 'N/A'
        return f"<Event(id={id_val}, name='{self.name}', group_id={group_id_val}, start_time='{start_time_val}')>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Event Model --- Demonstration")

    # Example Event instance
    # Assume Group with id=1 exists
    team_meeting = Event(
        name="Weekly Team Sync",
        description="Discuss progress, blockers, and plan for the upcoming week.",
        group_id=1,
        start_time=datetime.now(timezone.utc) + timedelta(days=3, hours=10), # Starts in 3 days at 10 AM UTC
        end_time=datetime.now(timezone.utc) + timedelta(days=3, hours=11),   # Ends one hour later
        location="Virtual - Zoom Link in Description",
        state="upcoming" # Example use of inherited 'state' field
    )
    team_meeting.id = 1 # Simulate ORM-set ID
    team_meeting.created_at = datetime.now(timezone.utc)
    team_meeting.updated_at = datetime.now(timezone.utc)

    logger.info(f"Example Event: {team_meeting!r}")
    logger.info(f"  Name: {team_meeting.name}")
    logger.info(f"  Start Time: {team_meeting.start_time.isoformat() if team_meeting.start_time else 'N/A'}")
    logger.info(f"  End Time: {team_meeting.end_time.isoformat() if team_meeting.end_time else 'N/A'}")
    logger.info(f"  Location: {team_meeting.location}")
    logger.info(f"  State: {team_meeting.state}")
    logger.info(f"  Created At: {team_meeting.created_at.isoformat() if team_meeting.created_at else 'N/A'}")


    birthday_event = Event(
        name="Alice's Birthday Party",
        group_id=1,
        start_time=datetime(2024, 12, 15, 18, 0, 0, tzinfo=timezone.utc),
        location="Community Hall"
    )
    birthday_event.id = 2
    logger.info(f"Another Event: {birthday_event!r}")

    # To view relationships, a DB session and related objects would be needed.
    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"Event attributes (conceptual table columns): {[c.name for c in Event.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
