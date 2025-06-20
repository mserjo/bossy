# backend/app/src/tasks/system/__init__.py
# -*- coding: utf-8 -*-
"""
Підпакет для системних фонових завдань.

Цей пакет об'єднує фонові завдання, пов'язані з обслуговуванням,
моніторингом та іншими системними операціями.

Модулі:
    cleanup.py: Завдання для періодичного очищення системи.
    backup.py: Завдання для створення резервних копій.
    monitoring.py: Завдання для збору метрик системи.

Імпорт основних класів завдань:
    З .cleanup імпортується CleanupTask.
    З .backup імпортується DatabaseBackupTask.
    З .monitoring імпортується SystemMetricsCollectorTask.
"""

from backend.app.src.tasks.system.cleanup import CleanupTask
from backend.app.src.tasks.system.backup import DatabaseBackupTask
from backend.app.src.tasks.system.monitoring import SystemMetricsCollectorTask
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

__all__ = [
    'CleanupTask',
    'DatabaseBackupTask',
    'SystemMetricsCollectorTask',
]

logger.info("Підпакет 'tasks.system' ініціалізовано.")
