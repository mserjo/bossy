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

# На даний момент, відповідні класи завдань ще не створені в модулях,
# тому імпорти будуть додані або розкоментовані, коли класи будуть реалізовані.

from .cleanup import CleanupTask
from .backup import DatabaseBackupTask
from .monitoring import SystemMetricsCollectorTask

__all__ = [
    'CleanupTask',
    'DatabaseBackupTask',
    'SystemMetricsCollectorTask',
]

import logging

logger = logging.getLogger(__name__)
logger.info("Підпакет 'tasks.system' ініціалізовано.")
