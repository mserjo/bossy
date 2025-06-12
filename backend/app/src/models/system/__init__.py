# backend/app/src/models/system/__init__.py
# -*- coding: utf-8 -*-
"""Пакет моделей SQLAlchemy для системних сутностей.

Цей пакет об'єднує моделі даних, що стосуються внутрішніх системних аспектів
додатку, таких як:
- Конфігураційні налаштування системи, що зберігаються в базі даних.
- Записи системних логів та подій.
- Метрики продуктивності та моніторингу.
- Статуси працездатності внутрішніх та зовнішніх сервісів.

Моделі з цього пакету експортуються для використання в адміністративних
інтерфейсах, системах моніторингу та для внутрішніх потреб додатку.
"""

# Імпорт централізованого логера
from backend.app.src.config import logger

# Імпорт моделей з відповідних файлів цього пакету, використовуючи нову конвенцію імен
from backend.app.src.models.system.settings import SystemSettingModel
from backend.app.src.models.system.monitoring import SystemLogModel, PerformanceMetricModel
from backend.app.src.models.system.health import ServiceHealthStatusModel

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.models.system import *`.
__all__ = [
    "SystemSettingModel",
    "SystemLogModel",
    "PerformanceMetricModel",
    "ServiceHealthStatusModel",
]

logger.debug("Ініціалізація пакету моделей `system`...")

# Коментар щодо можливого розширення:
# В майбутньому сюди можуть бути додані інші системні моделі,
# наприклад, для управління фоновими завданнями, аудитом дій користувачів
# на системному рівні (AuditLogModel) тощо.
