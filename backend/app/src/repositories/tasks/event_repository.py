# backend/app/src/repositories/tasks/event_repository.py

"""
Repository for Event entities.
Provides CRUD operations and specific methods for managing events.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone # Added timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_ # Added or_, and_

from backend.app.src.models.tasks.event import Event
from backend.app.src.schemas.tasks.event import EventCreate, EventUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class EventRepository(BaseRepository[Event, EventCreate, EventUpdate]):
    """
    Repository for managing Event records.
    """

    def __init__(self):
        super().__init__(Event)

    async def get_events_for_group(
        self,
        db: AsyncSession,
        *,
        group_id: int,
        start_after: Optional[datetime] = None, # Events starting after this time
        end_before: Optional[datetime] = None,   # Events ending before this time
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        """
        Retrieves events for a specific group, optionally filtered by start/end times.

        Args:
            db: The SQLAlchemy asynchronous database session.
            group_id: The ID of the group.
            start_after: Optional. Filter for events starting after this datetime.
            end_before: Optional. Filter for events ending before this datetime (or starting before if no end_time).
            include_deleted: Optional. If True, includes soft-deleted events.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of Event objects.
        """
        conditions = [self.model.group_id == group_id] # type: ignore[attr-defined]
        if start_after:
            conditions.append(self.model.start_time > start_after) # type: ignore[attr-defined]
        if end_before:
            conditions.append(
                or_(
                    self.model.end_time < end_before, # type: ignore[attr-defined]
                    and_(self.model.end_time.is_(None), self.model.start_time < end_before) # type: ignore[attr-defined]
                )
            )

        if not include_deleted and hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.start_time.asc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_events_in_date_range(
        self,
        db: AsyncSession,
        *,
        range_start: datetime,
        range_end: datetime,
        group_id: Optional[int] = None,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        """
        Retrieves events that are active (start_time before range_end AND (end_time after range_start OR end_time is NULL))
        within the given date range [range_start, range_end].
        Optionally filters by group_id.

        Args:
            db: The SQLAlchemy asynchronous database session.
            range_start: The start of the date range.
            range_end: The end of the date range.
            group_id: Optional. Filter by a specific group ID.
            include_deleted: Optional. If True, includes soft-deleted events.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of Event objects active within the range.
        """
        conditions = [
            self.model.start_time < range_end, # type: ignore[attr-defined]
            or_(
                self.model.end_time > range_start, # type: ignore[attr-defined]
                self.model.end_time.is_(None)    # type: ignore[attr-defined]
            )
        ]
        if group_id is not None:
            conditions.append(self.model.group_id == group_id) # type: ignore[attr-defined]

        if not include_deleted and hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.start_time.asc()) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    # BaseRepository methods create, get, update, remove are inherited.
    # Event creation will need group_id, start_time, etc., handled by service.
    # Event updates will use EventUpdate schema.
