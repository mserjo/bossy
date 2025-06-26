# backend/app/src/repositories/system/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет репозиторіїв для системних сутностей.
Включає репозиторії для cron-задач, стану системи, логів моніторингу
та системних налаштувань.
"""

from .cron import CronTaskRepository, cron_task_repository
from .health import ServiceHealthStatusRepository, service_health_status_repository
from .monitoring import SystemEventLogRepository, system_event_log_repository
from .settings import SystemSettingRepository, system_setting_repository

__all__ = [
    "CronTaskRepository",
    "cron_task_repository",
    "ServiceHealthStatusRepository",
    "service_health_status_repository",
    "SystemEventLogRepository",
    "system_event_log_repository",
    "SystemSettingRepository",
    "system_setting_repository",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'repositories.system' ініціалізовано.")
