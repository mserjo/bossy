# backend/app/src/services/system/monitoring.py
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta # Added timedelta for summary example

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func # Added for summary example

from app.src.services.base import BaseService
# Assuming models and schemas exist as per structure:
from app.src.models.system.monitoring import SystemLog, PerformanceMetric # SQLAlchemy models
from app.src.schemas.system.monitoring import ( # Pydantic schemas
    SystemLogCreate,
    SystemLogResponse,
    PerformanceMetricCreate,
    PerformanceMetricResponse,
    SystemMonitoringSummaryResponse # A new schema for a summary
)
# from app.src.repositories.system.monitoring_repository import SystemMonitoringRepository # Placeholder

# Initialize logger for this module
logger = logging.getLogger(__name__)

class SystemMonitoringService(BaseService): # If using repo: BaseService[SystemMonitoringRepository]
    """
    Service for handling system monitoring, including logging events/errors
    and recording performance metrics.
    """

    # If using repository pattern:
    # def __init__(self, db_session: AsyncSession, monitoring_repo: SystemMonitoringRepository):
    #     super().__init__(db_session, repo=monitoring_repo)
    #     logger.info("SystemMonitoringService initialized with SystemMonitoringRepository.")

    # If not using repository pattern (direct DB interaction via session):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("SystemMonitoringService initialized.")

    async def create_system_log(self, log_data: SystemLogCreate) -> SystemLogResponse:
        """
        Creates a new system log entry.

        Args:
            log_data (SystemLogCreate): Data for the new system log.

        Returns:
            SystemLogResponse: The created system log entry.
        """
        logger.debug(f"Attempting to create new system log of type '{log_data.log_type}' for component '{log_data.component}'.")

        # new_log_db = SystemLog(**log_data.model_dump()) # Pydantic v2
        new_log_db = SystemLog(**log_data.dict()) # Pydantic v1

        self.db_session.add(new_log_db)
        await self.commit()
        await self.db_session.refresh(new_log_db)

        logger.info(f"System log entry created successfully with ID: {new_log_db.id}")
        # Avoid logging sensitive details from log_data.details if it can contain PII or secrets
        # return SystemLogResponse.model_validate(new_log_db) # Pydantic v2
        return SystemLogResponse.from_orm(new_log_db) # Pydantic v1

    async def get_system_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        log_type: Optional[str] = None,
        component: Optional[str] = None,
        user_id: Optional[UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[SystemLogResponse]:
        """
        Retrieves a list of system log entries, with optional filtering and pagination.

        Args:
            skip (int): Number of log entries to skip.
            limit (int): Maximum number of log entries to return.
            log_type (Optional[str]): Filter by log type (e.g., 'ERROR', 'INFO', 'AUDIT').
            component (Optional[str]): Filter by system component (e.g., 'AuthService', 'TaskScheduler').
            user_id (Optional[UUID]): Filter by user ID associated with the log.
            start_time (Optional[datetime]): Filter logs created after this time.
            end_time (Optional[datetime]): Filter logs created before this time.

        Returns:
            List[SystemLogResponse]: A list of system log entries.
        """
        logger.debug(f"Attempting to retrieve system logs with filters: type={log_type}, comp={component}, user={user_id}, time_range=[{start_time}-{end_time}] skip={skip}, limit={limit}")

        stmt = select(SystemLog)
        if log_type:
            stmt = stmt.where(SystemLog.log_type == log_type)
        if component:
            stmt = stmt.where(SystemLog.component.ilike(f"%{component}%")) # Case-insensitive search
        if user_id:
            stmt = stmt.where(SystemLog.user_id == user_id)
        if start_time:
            stmt = stmt.where(SystemLog.created_at >= start_time)
        if end_time:
            stmt = stmt.where(SystemLog.created_at <= end_time)

        stmt = stmt.order_by(SystemLog.created_at.desc()).offset(skip).limit(limit)

        result = await self.db_session.execute(stmt)
        logs_db = result.scalars().all()

        # response_list = [SystemLogResponse.model_validate(log) for log in logs_db] # Pydantic v2
        response_list = [SystemLogResponse.from_orm(log) for log in logs_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} system log entries.")
        return response_list

    async def create_performance_metric(self, metric_data: PerformanceMetricCreate) -> PerformanceMetricResponse:
        """
        Records a new performance metric.

        Args:
            metric_data (PerformanceMetricCreate): Data for the new performance metric.

        Returns:
            PerformanceMetricResponse: The recorded performance metric.
        """
        logger.debug(f"Attempting to record performance metric '{metric_data.metric_name}' for component '{metric_data.component}'.")

        # new_metric_db = PerformanceMetric(**metric_data.model_dump()) # Pydantic v2
        new_metric_db = PerformanceMetric(**metric_data.dict()) # Pydantic v1

        self.db_session.add(new_metric_db)
        await self.commit()
        await self.db_session.refresh(new_metric_db)

        logger.info(f"Performance metric '{new_metric_db.metric_name}' recorded successfully with ID: {new_metric_db.id}")
        # return PerformanceMetricResponse.model_validate(new_metric_db) # Pydantic v2
        return PerformanceMetricResponse.from_orm(new_metric_db) # Pydantic v1

    async def get_performance_metrics(
        self,
        skip: int = 0,
        limit: int = 100,
        metric_name: Optional[str] = None,
        component: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[PerformanceMetricResponse]:
        """
        Retrieves a list of performance metrics, with optional filtering and pagination.

        Args:
            skip (int): Number of metrics to skip.
            limit (int): Maximum number of metrics to return.
            metric_name (Optional[str]): Filter by metric name.
            component (Optional[str]): Filter by system component.
            start_time (Optional[datetime]): Filter metrics recorded after this time.
            end_time (Optional[datetime]): Filter metrics recorded before this time.

        Returns:
            List[PerformanceMetricResponse]: A list of performance metrics.
        """
        logger.debug(f"Attempting to retrieve performance metrics with filters: name={metric_name}, comp={component}, time_range=[{start_time}-{end_time}], skip={skip}, limit={limit}")

        stmt = select(PerformanceMetric)
        if metric_name:
            stmt = stmt.where(PerformanceMetric.metric_name == metric_name)
        if component:
            stmt = stmt.where(PerformanceMetric.component.ilike(f"%{component}%"))
        if start_time:
            stmt = stmt.where(PerformanceMetric.timestamp >= start_time) # Assuming 'timestamp' field in model
        if end_time:
            stmt = stmt.where(PerformanceMetric.timestamp <= end_time)

        stmt = stmt.order_by(PerformanceMetric.timestamp.desc()).offset(skip).limit(limit)

        result = await self.db_session.execute(stmt)
        metrics_db = result.scalars().all()

        # response_list = [PerformanceMetricResponse.model_validate(metric) for metric in metrics_db] # Pydantic v2
        response_list = [PerformanceMetricResponse.from_orm(metric) for metric in metrics_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} performance metrics.")
        return response_list

    async def get_monitoring_summary(self) -> SystemMonitoringSummaryResponse:
        """
        Retrieves a summary of system monitoring data, e.g., count of errors in the last 24h.
        This is a placeholder and would require more specific aggregation queries.
        """
        logger.info("Attempting to generate system monitoring summary.")

        twenty_four_hours_ago = datetime.utcnow() - timedelta(days=1)

        error_stmt = select(func.count(SystemLog.id)).where(
            (SystemLog.log_type == 'ERROR') & (SystemLog.created_at >= twenty_four_hours_ago)
        )
        error_count_result = await self.db_session.execute(error_stmt)
        error_count = error_count_result.scalar_one_or_none() or 0

        # Example: Count critical performance metrics (simplified)
        # This is highly dependent on how 'critical' is defined for performance metrics.
        # For this example, let's assume there isn't a simple query for it yet.
        critical_performance_issues = 0 # Placeholder for a more complex query

        last_log_stmt = select(func.max(SystemLog.created_at))
        last_log_result = await self.db_session.execute(last_log_stmt)
        last_log_entry_at = last_log_result.scalar_one_or_none()

        last_metric_stmt = select(func.max(PerformanceMetric.timestamp))
        last_metric_result = await self.db_session.execute(last_metric_stmt)
        last_metric_recorded_at = last_metric_result.scalar_one_or_none()

        summary_data = {
            "recent_error_count": error_count,
            "critical_performance_issues": critical_performance_issues,
            "last_log_entry_at": last_log_entry_at,
            "last_metric_recorded_at": last_metric_recorded_at,
            "status_message": "Monitoring systems operational."
        }
        if not last_log_entry_at and not last_metric_recorded_at:
             summary_data["status_message"] = "No monitoring data recorded yet."

        logger.info(f"Generated monitoring summary: {summary_data}")
        return SystemMonitoringSummaryResponse(**summary_data)

logger.info("SystemMonitoringService class defined.")
