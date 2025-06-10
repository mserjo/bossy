# backend/app/src/schemas/system/__init__.py
"""
Pydantic схеми для системних сутностей.

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються системних
налаштувань, записів моніторингу (логи, метрики) та стану здоров'я
компонентів системи Kudos.
"""

# Схеми для Системних Налаштувань
from .settings import (
    SystemSettingBaseSchema,
    SystemSettingCreateSchema,
    SystemSettingUpdateSchema,
    SystemSettingSchema
)

# Схеми для Моніторингу (Логи та Метрики)
from .monitoring import (
    SystemLogBaseSchema,
    SystemLogCreateSchema,
    SystemLogSchema,
    PerformanceMetricBaseSchema,
    PerformanceMetricCreateSchema,
    PerformanceMetricSchema
)

# Схеми для Стану Здоров'я Системи
from .health import (
    ServiceHealthStatusBaseSchema,
    ServiceHealthStatusSchema,
    OverallHealthStatusSchema
)

__all__ = [
    # SystemSetting schemas
    "SystemSettingBaseSchema",
    "SystemSettingCreateSchema",
    "SystemSettingUpdateSchema",
    "SystemSettingSchema",
    # SystemLog schemas
    "SystemLogBaseSchema",
    "SystemLogCreateSchema",
    "SystemLogSchema",
    # PerformanceMetric schemas
    "PerformanceMetricBaseSchema",
    "PerformanceMetricCreateSchema",
    "PerformanceMetricSchema",
    # Health Status schemas
    "ServiceHealthStatusBaseSchema",
    "ServiceHealthStatusSchema",
    "OverallHealthStatusSchema",
]
