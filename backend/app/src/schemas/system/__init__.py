# backend/app/src/schemas/system/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету системних схем (`system`).

Цей файл робить доступними основні системні схеми для імпорту з пакету
`backend.app.src.schemas.system`.

Приклад імпорту:
from backend.app.src.schemas.system import SystemSettingSchema, CronTaskSchema

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних системних схем
from backend.app.src.schemas.system.settings import (
    SystemSettingSchema,
    SystemSettingCreateSchema,
    SystemSettingUpdateSchema,
)
from backend.app.src.schemas.system.cron_task import (
    CronTaskSchema,
    CronTaskCreateSchema,
    CronTaskUpdateSchema,
)
from backend.app.src.schemas.system.monitoring import (
    SystemEventLogSchema,
    SystemEventLogCreateSchema,
    # PerformanceMetricSchema, # Якщо буде реалізована
    # PerformanceMetricCreateSchema, # Якщо буде реалізована
)
from backend.app.src.schemas.system.health import (
    ServiceHealthStatusSchema,
    ServiceHealthStatusCreateSchema,
    HealthCheckComponentSchema,
    OverallHealthStatusSchema,
)

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    # System Settings Schemas
    "SystemSettingSchema",
    "SystemSettingCreateSchema",
    "SystemSettingUpdateSchema",

    # Cron Task Schemas
    "CronTaskSchema",
    "CronTaskCreateSchema",
    "CronTaskUpdateSchema",

    # Monitoring Schemas
    "SystemEventLogSchema",
    "SystemEventLogCreateSchema",
    # "PerformanceMetricSchema",
    # "PerformanceMetricCreateSchema",

    # Health Check Schemas
    "ServiceHealthStatusSchema", # Для моделі історії, якщо є
    "ServiceHealthStatusCreateSchema", # Для моделі історії, якщо є
    "HealthCheckComponentSchema", # Для відповіді API
    "OverallHealthStatusSchema", # Для відповіді API
]

# TODO: Переконатися, що всі необхідні системні схеми створені та включені до `__all__`.
# На даний момент включені схеми для системних налаштувань, cron-задач,
# логування подій та моніторингу стану.
# Схеми для метрик продуктивності закоментовані, оскільки відповідна модель
# ще не реалізована детально.
# Це забезпечує централізований доступ до системних схем.
