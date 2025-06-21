# backend/app/src/services/system/monitoring.py
# -*- coding: utf-8 -*-
"""
Сервіс для моніторингу системи.

Відповідає за запис системних подій, логів помилок, метрик продуктивності,
а також за надання доступу до цієї інформації.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

# --- Імпорт компонентів додатку ---
from backend.app.src.services.base import BaseService  # Оновлений шлях до BaseService
from backend.app.src.models.system.monitoring import SystemLog, PerformanceMetric  # Оновлений шлях
from backend.app.src.schemas.system.monitoring import (  # Оновлений шлях
    SystemLogCreateSchema,
    SystemLogResponseSchema,
    PerformanceMetricCreateSchema,
    PerformanceMetricResponseSchema,
    SystemMonitoringSummaryResponseSchema  # Оновлено назву для відповідності
)
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


# Базова функція-заглушка для інтернаціоналізації рядків
def _(text: str) -> str:
    return text


class SystemMonitoringService(BaseService):
    """
    Сервіс для обробки функцій системного моніторингу.

    Включає логування системних подій, запис метрик продуктивності
    та надання зведеної інформації про стан системи.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізація сервісу моніторингу.

        Args:
            db_session: Асинхронна сесія бази даних SQLAlchemy.
        """
        super().__init__(db_session)
        # i18n: Log message - Service initialized
        logger.info(_("Сервіс SystemMonitoringService ініціалізовано."))

    async def create_system_log(self, log_data: SystemLogCreateSchema) -> SystemLogResponseSchema:
        """
        Створює новий запис у системному лозі.

        Args:
            log_data: Дані для нового запису логу (схема Pydantic).

        Returns:
            Створений запис логу у вигляді Pydantic схеми.
        """
        # i18n: Log message - Attempting to create system log
        logger.debug(
            _("Спроба створення нового запису системного логу типу '{log_type}' для компонента '{component}'.").format(
                log_type=log_data.log_type, component=log_data.component
            ))

        new_log_db = SystemLog(**log_data.model_dump())  # Pydantic v2

        self.db_session.add(new_log_db)
        await self.commit_changes()  # Використання методу з BaseService
        await self.db_session.refresh(new_log_db)

        # i18n: Log message - System log entry created successfully
        logger.info(_("Запис системного логу успішно створено з ID: {log_id}").format(log_id=new_log_db.id))
        # Уникайте логування log_data.details, якщо воно може містити чутливу інформацію.
        return SystemLogResponseSchema.model_validate(new_log_db)  # Pydantic v2

    async def get_system_logs(
            self,
            skip: int = 0,
            limit: int = 100,
            log_type: Optional[str] = None,
            component: Optional[str] = None,
            user_id: Optional[UUID] = None,  # Або int, залежно від типу ID користувача
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None
    ) -> List[SystemLogResponseSchema]:
        """
        Отримує список записів системного логу з можливістю фільтрації та пагінації.

        Args:
            skip: Кількість записів для пропуску (для пагінації).
            limit: Максимальна кількість записів для повернення.
            log_type: Фільтр за типом логу (наприклад, 'ERROR', 'INFO', 'AUDIT').
            component: Фільтр за компонентом системи (наприклад, 'AuthService', 'TaskScheduler').
            user_id: Фільтр за ID користувача, пов'язаного з логом.
            start_time: Фільтр для логів, створених після цього часу.
            end_time: Фільтр для логів, створених до цього часу.

        Returns:
            Список записів системного логу.
        """
        # i18n: Log message - Attempting to retrieve system logs with filters
        logger.debug(
            _("Спроба отримання системних логів. Фільтри: тип='{log_type}', компонент='{component}', "
              "user_id='{user_id}', діапазон часу=[{start_time} - {end_time}], пропуск={skip}, ліміт={limit}").format(
                log_type=log_type, component=component, user_id=user_id,
                start_time=start_time, end_time=end_time, skip=skip, limit=limit
            )
        )

        stmt = select(SystemLog)
        if log_type:
            stmt = stmt.where(SystemLog.log_type == log_type)
        if component:
            # Використовуємо ilike для пошуку без урахування регістру (якщо підтримується БД)
            stmt = stmt.where(SystemLog.component.ilike(f"%{component}%"))
        if user_id:
            stmt = stmt.where(SystemLog.user_id == user_id)
        if start_time:
            stmt = stmt.where(SystemLog.created_at >= start_time)
        if end_time:
            stmt = stmt.where(SystemLog.created_at <= end_time)

        stmt = stmt.order_by(SystemLog.created_at.desc()).offset(skip).limit(limit)

        result = await self.db_session.execute(stmt)
        logs_db = result.scalars().all()

        response_list = [SystemLogResponseSchema.model_validate(log_db) for log_db in logs_db]  # Pydantic v2
        # i18n: Log message - Retrieved system log entries count
        logger.info(_("Отримано {count} записів системного логу.").format(count=len(response_list)))
        return response_list

    async def create_performance_metric(self,
                                        metric_data: PerformanceMetricCreateSchema) -> PerformanceMetricResponseSchema:
        """
        Записує нову метрику продуктивності.

        Args:
            metric_data: Дані для нової метрики продуктивності.

        Returns:
            Записана метрика продуктивності.
        """
        # i18n: Log message - Attempting to record performance metric
        logger.debug(_("Спроба запису метрики продуктивності '{metric_name}' для компонента '{component}'.").format(
            metric_name=metric_data.metric_name, component=metric_data.component
        ))

        new_metric_db = PerformanceMetric(**metric_data.model_dump())  # Pydantic v2

        self.db_session.add(new_metric_db)
        await self.commit_changes()
        await self.db_session.refresh(new_metric_db)

        # i18n: Log message - Performance metric recorded successfully
        logger.info(_("Метрику продуктивності '{metric_name}' успішно записано з ID: {metric_id}").format(
            metric_name=new_metric_db.metric_name, metric_id=new_metric_db.id
        ))
        return PerformanceMetricResponseSchema.model_validate(new_metric_db)  # Pydantic v2

    async def get_performance_metrics(
            self,
            skip: int = 0,
            limit: int = 100,
            metric_name: Optional[str] = None,
            component: Optional[str] = None,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None
    ) -> List[PerformanceMetricResponseSchema]:
        """
        Отримує список метрик продуктивності з можливістю фільтрації та пагінації.
        (Детальний опис аргументів аналогічний до `get_system_logs`)

        Returns:
            Список метрик продуктивності.
        """
        # i18n: Log message - Attempting to retrieve performance metrics with filters
        logger.debug(
            _("Спроба отримання метрик продуктивності. Фільтри: назва='{metric_name}', компонент='{component}', "
              "діапазон часу=[{start_time} - {end_time}], пропуск={skip}, ліміт={limit}").format(
                metric_name=metric_name, component=component, start_time=start_time,
                end_time=end_time, skip=skip, limit=limit
            )
        )
        stmt = select(PerformanceMetric)
        if metric_name:
            stmt = stmt.where(PerformanceMetric.metric_name == metric_name)
        if component:
            stmt = stmt.where(PerformanceMetric.component.ilike(f"%{component}%"))
        if start_time:
            # Припускаємо, що модель PerformanceMetric має поле 'timestamp' або 'created_at'
            stmt = stmt.where(PerformanceMetric.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(PerformanceMetric.timestamp <= end_time)

        stmt = stmt.order_by(PerformanceMetric.timestamp.desc()).offset(skip).limit(limit)

        result = await self.db_session.execute(stmt)
        metrics_db = result.scalars().all()

        response_list = [PerformanceMetricResponseSchema.model_validate(metric_db) for metric_db in
                         metrics_db]  # Pydantic v2
        # i18n: Log message - Retrieved performance metrics count
        logger.info(_("Отримано {count} метрик продуктивності.").format(count=len(response_list)))
        return response_list

    async def get_monitoring_summary(self) -> SystemMonitoringSummaryResponseSchema:
        """
        Отримує зведену інформацію про стан системи та моніторинг.
        Наприклад, кількість помилок за останню добу, критичні проблеми продуктивності тощо.
        """
        # i18n: Log message - Generating system monitoring summary
        logger.info(_("Генерація зведеної інформації моніторингу системи."))

        twenty_four_hours_ago = datetime.utcnow() - timedelta(days=1)

        # Кількість помилок за останні 24 години
        error_stmt = select(func.count(SystemLog.id)).where(
            (SystemLog.log_type == 'ERROR') & (SystemLog.created_at >= twenty_four_hours_ago)
        )
        error_count_result = await self.db_session.execute(error_stmt)
        error_count = error_count_result.scalar_one_or_none() or 0

        # TODO: Реалізувати логіку для визначення "критичних проблем продуктивності".
        #       Це може базуватися на певних порогах для метрик або специфічних логах.
        critical_performance_issues = 0  # Заглушка

        # Час останнього запису в лог
        last_log_stmt = select(func.max(SystemLog.created_at))
        last_log_result = await self.db_session.execute(last_log_stmt)
        last_log_entry_at = last_log_result.scalar_one_or_none()

        # Час останнього запису метрики продуктивності
        last_metric_stmt = select(func.max(PerformanceMetric.timestamp))  # Припускаючи поле 'timestamp'
        last_metric_result = await self.db_session.execute(last_metric_stmt)
        last_metric_recorded_at = last_metric_result.scalar_one_or_none()

        status_msg_key = "operational"  # i18n_key
        if not last_log_entry_at and not last_metric_recorded_at:
            status_msg_key = "no_data"  # i18n_key

        # i18n: Status message for monitoring summary
        status_messages = {
            "operational": _("Системи моніторингу працюють."),
            "no_data": _("Дані моніторингу ще не записувалися.")
        }

        summary_data = SystemMonitoringSummaryResponseSchema(
            recent_error_count=error_count,
            critical_performance_issues=critical_performance_issues,  # TODO: implement this
            last_log_entry_at=last_log_entry_at,
            last_metric_recorded_at=last_metric_recorded_at,
            status_message=status_messages[status_msg_key]  # i18n
        )
        # i18n: Log message - Generated monitoring summary
        logger.info(
            _("Згенеровано зведення моніторингу: {summary_data}").format(summary_data=summary_data.model_dump_json()))
        return summary_data

    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        [Placeholder] Отримує основні системні метрики (ОС рівня).
        Наприклад, використання CPU, пам'яті, диска.
        """
        # TODO: Реалізувати збір системних метрик.
        #       - Використати бібліотеку `psutil` (`pip install psutil`).
        #       - Збирати CPU (загальне, по ядрах), пам'ять (загальна, доступна, використана),
        #         дисковий простір (для ключових точок монтування), мережевий трафік.
        #       - Обережно з приватністю та безпекою при виведенні деталей системи.
        logger.info(_("[TODO] Запит системних метрик (ОС). Потребує реалізації з `psutil`."))  # i18n
        return {
            "cpu_usage_percent": 0.0,  # i18n_comment: Відсоток використання CPU
            "memory_usage_percent": 0.0,  # i18n_comment: Відсоток використання пам'яті
            "disk_usage_percent": {"path": "/", "percent": 0.0},  # i18n_comment: Відсоток використання диска
            "status": _("Заглушка. Потребує реалізації з використанням `psutil`.")  # i18n
        }

    async def get_application_logs(self, lines: int = 100, component_filter: Optional[str] = None) -> List[str]:
        """
        [Placeholder] Отримує останні записи з логів додатку.
        Це відрізняється від `get_system_logs`, оскільки може читати безпосередньо файли логів
        або інтегруватися з системою агрегації логів (ELK, Grafana Loki тощо).
        """
        # TODO: Реалізувати отримання логів додатку.
        #       - Визначити джерело логів (файли, syslog, log aggregation system).
        #       - Якщо файли: безпечно читати останні N рядків, можливо з фільтрацією.
        #       - Врахувати ротацію логів.
        #       - Для продакшн систем краще інтегруватися з централізованою системою логування.
        logger.info(
            _("[TODO] Запит логів додатку. Потребує реалізації (читання файлів або інтеграція з системою логування)."))  # i18n
        return [
            _("Заглушка: Лог додатку 1 ({component_filter_info}).").format(
                component_filter_info=component_filter or _("без фільтра")),  # i18n
            _("Заглушка: Лог додатку 2 ({component_filter_info}).").format(
                component_filter_info=component_filter or _("без фільтра"))  # i18n
        ]


logger.info(_("Клас SystemMonitoringService визначено."))  # i18n
