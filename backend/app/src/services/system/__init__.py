# backend/app/src/services/system/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет сервісів для системних сутностей.
"""

from .cron_service import CronTaskService, cron_task_service
from .health_service import HealthService, health_service # Для генерації HealthCheck відповіді
from .system_event_log_service import SystemEventLogService, system_event_log_service
from .system_settings_service import SystemSettingsService, system_settings_service
from .initialization_service import InitializationService, initialization_service # Для початкових даних

__all__ = [
    "CronTaskService",
    "cron_task_service",
    "HealthService",
    "health_service",
    "SystemEventLogService",
    "system_event_log_service",
    "SystemSettingsService",
    "system_settings_service",
    "InitializationService",
    "initialization_service",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'services.system' ініціалізовано.")
