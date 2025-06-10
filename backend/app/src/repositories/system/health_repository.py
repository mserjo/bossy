# backend/app/src/repositories/system/health_repository.py

"""
Repository for ServiceHealthStatus entities.
Provides CRUD operations and specific methods for managing the health status
of various internal or external services.
"""

import logging
from typing import Optional, List # Added List
from datetime import datetime # Added datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc # Added desc

from backend.app.src.models.system.health import ServiceHealthStatus, HealthStatusEnum
from backend.app.src.schemas.system.health import ServiceHealthStatusCreate, ServiceHealthStatusUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class ServiceHealthRepository(BaseRepository[ServiceHealthStatus, ServiceHealthStatusCreate, ServiceHealthStatusUpdate]):
    """
    Repository for managing ServiceHealthStatus records.
    """

    def __init__(self):
        super().__init__(ServiceHealthStatus)

    async def get_by_service_name(self, db: AsyncSession, *, service_name: str) -> Optional[ServiceHealthStatus]:
        """
        Retrieves the health status for a specific service by its unique name.

        Args:
            db: The SQLAlchemy asynchronous database session.
            service_name: The unique name of the service.

        Returns:
            The ServiceHealthStatus object if found, otherwise None.
        """
        statement = select(self.model).where(self.model.service_name == service_name) # type: ignore[attr-defined]
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_services_by_status(
        self, db: AsyncSession, *, status: HealthStatusEnum, skip: int = 0, limit: int = 100
    ) -> List[ServiceHealthStatus]:
        """
        Retrieves all services currently matching a specific health status.

        Args:
            db: The SQLAlchemy asynchronous database session.
            status: The HealthStatusEnum value to filter by.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of ServiceHealthStatus objects.
        """
        statement = (
            select(self.model)
            .where(self.model.status == status) # type: ignore[attr-defined]
            .order_by(desc(self.model.last_checked_at)) # type: ignore[attr-defined] # Show most recently checked ones first
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_all_service_statuses(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, sort_by_last_checked: bool = True
    ) -> List[ServiceHealthStatus]:
        """
        Retrieves all recorded service health statuses, optionally sorted by last_checked_at.

        Args:
            db: The SQLAlchemy asynchronous database session.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            sort_by_last_checked: If True, orders by last_checked_at descending. Otherwise, by service_name.

        Returns:
            A list of all ServiceHealthStatus objects.
        """
        statement = select(self.model)
        if sort_by_last_checked:
            statement = statement.order_by(desc(self.model.last_checked_at)) # type: ignore[attr-defined]
        else:
            statement = statement.order_by(self.model.service_name) # type: ignore[attr-defined]

        statement = statement.offset(skip).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())

    # The base `create` and `update` methods from BaseRepository will be used.
    # `create` will take ServiceHealthStatusCreate.
    # `update` will take ServiceHealthStatusUpdate or a Dict.
    # Ensure that `last_checked_at` is properly handled; the schemas define it.
    # The ServiceHealthStatus model has `last_checked_at` as a required field,
    # so create/update schemas should ensure it's provided.
