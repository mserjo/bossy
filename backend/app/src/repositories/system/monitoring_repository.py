# backend/app/src/repositories/system/monitoring_repository.py

"""
Repository for SystemLog and PerformanceMetric entities.
Provides CRUD operations and specific methods for managing system monitoring data.
"""

import logging
from typing import Optional, List, Dict, Any # Added List, Dict, Any
from datetime import datetime # Added datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc # Added desc, asc for ordering

from backend.app.src.models.system.monitoring import SystemLog, PerformanceMetric
from backend.app.src.schemas.system.monitoring import (
    SystemLogCreate,
    # Assuming SystemLogUpdate might not be common, or could use SystemLogBase/Dict for partial.
    # If specific update logic is needed, a SystemLogUpdate schema would be imported.
    PerformanceMetricCreate,
    # Similarly for PerformanceMetricUpdate.
)
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

# --- SystemLog Repository ---
class SystemLogRepository(BaseRepository[SystemLog, SystemLogCreate, SystemLogCreate]): # Using SystemLogCreate for Update type for simplicity
    """
    Repository for managing SystemLog records.
    System logs are typically append-only, so updates might be rare or restricted.
    """

    def __init__(self):
        super().__init__(SystemLog)

    async def get_logs_by_level(
        self, db: AsyncSession, *, level: str, skip: int = 0, limit: int = 100, newest_first: bool = True
    ) -> List[SystemLog]:
        """
        Retrieves logs filtered by a specific log level, with pagination and ordering.

        Args:
            db: The SQLAlchemy asynchronous database session.
            level: The log level to filter by (e.g., "INFO", "ERROR").
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            newest_first: If True, orders logs by creation date descending, otherwise ascending.

        Returns:
            A list of SystemLog objects.
        """
        statement = select(self.model).where(self.model.level == level)
        if newest_first:
            statement = statement.order_by(desc(self.model.created_at)) # type: ignore[attr-defined]
        else:
            statement = statement.order_by(asc(self.model.created_at)) # type: ignore[attr-defined]

        statement = statement.offset(skip).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_logs_by_date_range(
        self,
        db: AsyncSession,
        *,
        start_time: datetime,
        end_time: datetime,
        skip: int = 0,
        limit: int = 100,
        newest_first: bool = True
    ) -> List[SystemLog]:
        """
        Retrieves logs within a specific date/time range, with pagination and ordering.

        Args:
            db: The SQLAlchemy asynchronous database session.
            start_time: The beginning of the time range (inclusive).
            end_time: The end of the time range (inclusive).
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            newest_first: If True, orders logs by creation date descending, otherwise ascending.

        Returns:
            A list of SystemLog objects.
        """
        statement = select(self.model).where(
            self.model.created_at >= start_time, # type: ignore[attr-defined]
            self.model.created_at <= end_time    # type: ignore[attr-defined]
        )
        if newest_first:
            statement = statement.order_by(desc(self.model.created_at)) # type: ignore[attr-defined]
        else:
            statement = statement.order_by(asc(self.model.created_at)) # type: ignore[attr-defined]

        statement = statement.offset(skip).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_logs_by_logger_name(
        self, db: AsyncSession, *, logger_name: str, skip: int = 0, limit: int = 100, newest_first: bool = True
    ) -> List[SystemLog]:
        """
        Retrieves logs filtered by a specific logger name, with pagination and ordering.

        Args:
            db: The SQLAlchemy asynchronous database session.
            logger_name: The name of the logger to filter by.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            newest_first: If True, orders logs by creation date descending, otherwise ascending.

        Returns:
            A list of SystemLog objects.
        """
        statement = select(self.model).where(self.model.logger_name == logger_name) # type: ignore[attr-defined]
        if newest_first:
            statement = statement.order_by(desc(self.model.created_at)) # type: ignore[attr-defined]
        else:
            statement = statement.order_by(asc(self.model.created_at)) # type: ignore[attr-defined]

        statement = statement.offset(skip).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())

    # Note: System logs are generally append-only.
    # The base `update` and `remove` methods from BaseRepository are available
    # but might be used sparingly or with caution for logs. Consider if they
    # should be overridden to prevent usage or add specific logic if needed.


# --- PerformanceMetric Repository ---
class PerformanceMetricRepository(BaseRepository[PerformanceMetric, PerformanceMetricCreate, PerformanceMetricCreate]): # Using Create for Update type
    """
    Repository for managing PerformanceMetric records.
    Performance metrics are also typically append-only.
    """

    def __init__(self):
        super().__init__(PerformanceMetric)

    async def get_metrics_by_name(
        self, db: AsyncSession, *, metric_name: str, skip: int = 0, limit: int = 100, newest_first: bool = True
    ) -> List[PerformanceMetric]:
        """
        Retrieves performance metrics filtered by metric name, with pagination and ordering.

        Args:
            db: The SQLAlchemy asynchronous database session.
            metric_name: The name of the metric to filter by.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            newest_first: If True, orders metrics by recording date descending, otherwise ascending.

        Returns:
            A list of PerformanceMetric objects.
        """
        statement = select(self.model).where(self.model.metric_name == metric_name) # type: ignore[attr-defined]
        if newest_first:
            statement = statement.order_by(desc(self.model.created_at)) # type: ignore[attr-defined]
        else:
            statement = statement.order_by(asc(self.model.created_at)) # type: ignore[attr-defined]

        statement = statement.offset(skip).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_metrics_by_date_range(
        self,
        db: AsyncSession,
        *,
        start_time: datetime,
        end_time: datetime,
        metric_name: Optional[str] = None, # Optional filter by metric name
        tags_filter: Optional[Dict[str, Any]] = None, # Optional filter by tags (exact match for now)
        skip: int = 0,
        limit: int = 100,
        newest_first: bool = True
    ) -> List[PerformanceMetric]:
        """
        Retrieves performance metrics within a specific date/time range,
        optionally filtered by metric name and tags, with pagination and ordering.

        Args:
            db: The SQLAlchemy asynchronous database session.
            start_time: The beginning of the time range (inclusive).
            end_time: The end of the time range (inclusive).
            metric_name: Optional. Filter by a specific metric name.
            tags_filter: Optional. A dictionary of tags to filter by (exact match of key-value pairs within the JSONB tags).
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            newest_first: If True, orders metrics by recording date descending, otherwise ascending.

        Returns:
            A list of PerformanceMetric objects.
        """
        conditions = [
            self.model.created_at >= start_time, # type: ignore[attr-defined]
            self.model.created_at <= end_time    # type: ignore[attr-defined]
        ]
        if metric_name:
            conditions.append(self.model.metric_name == metric_name) # type: ignore[attr-defined]

        if tags_filter:
            # This is a basic way to filter JSON. For complex JSON queries,
            # SQLAlchemy offers more specific functions like `jsonb_path_exists`, etc.
            # This example assumes tags_filter provides key-value pairs that should exist at the top level of the 'tags' JSON.
            for key, value in tags_filter.items():
                conditions.append(self.model.tags[key].astext == str(value)) # type: ignore[attr-defined]


        statement = select(self.model).where(*conditions)

        if newest_first:
            statement = statement.order_by(desc(self.model.created_at)) # type: ignore[attr-defined]
        else:
            statement = statement.order_by(asc(self.model.created_at)) # type: ignore[attr-defined]

        statement = statement.offset(skip).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())

    # Note: Performance metrics are generally append-only.
    # The base `update` and `remove` are available but likely not standard use cases.
