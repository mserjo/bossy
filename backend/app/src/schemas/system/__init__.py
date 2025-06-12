# backend/app/src/schemas/system/__init__.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для системних сутностей.

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються таких системних аспектів:
- **Стан здоров'я системи та її компонентів**:
    - `ServiceHealthStatusSchema`: Схема для представлення стану окремого залежного сервісу.
    - `HealthCheckResponseSchema`: Схема для загальної відповіді API перевірки стану здоров'я системи.
- **Системні налаштування**:
    - `SystemSettingBaseSchema`: Базова схема для системного налаштування.
    - `SystemSettingCreateSchema`: Схема для створення нового системного налаштування.
    - `SystemSettingUpdateSchema`: Схема для оновлення існуючого системного налаштування.
    - `SystemSettingResponseSchema`: Схема для представлення системного налаштування у відповідях API.
- **Моніторинг (логи та метрики)**:
    - `SystemLogBaseSchema`: Базова схема для запису системного логу.
    - `SystemLogCreateSchema`: Схема для створення нового запису системного логу.
    - `SystemLogResponseSchema`: Схема для представлення запису системного логу у відповідях API.
    - `PerformanceMetricBaseSchema`: Базова схема для метрики продуктивності.
    - `PerformanceMetricCreateSchema`: Схема для створення нового запису метрики продуктивності.
    - `PerformanceMetricResponseSchema`: Схема для представлення метрики продуктивності у відповідях API.

Всі схеми успадковують `BaseSchema` для забезпечення спільної конфігурації Pydantic.
"""

# Імпорт централізованого логера
from backend.app.src.config import logger

# Схеми для Стану Здоров'я Системи
from backend.app.src.schemas.system.health import (
    ServiceHealthStatusSchema,
    HealthCheckResponseSchema
)

# Схеми для Системних Налаштувань
from backend.app.src.schemas.system.settings import (
    SystemSettingBaseSchema,
    SystemSettingCreateSchema,
    SystemSettingUpdateSchema,
    SystemSettingResponseSchema
)

# Схеми для Моніторингу (Логи та Метрики)
from backend.app.src.schemas.system.monitoring import (
    SystemLogBaseSchema,
    SystemLogCreateSchema,
    SystemLogResponseSchema,
    PerformanceMetricBaseSchema,
    PerformanceMetricCreateSchema,
    PerformanceMetricResponseSchema
)

__all__ = [
    # Health Status schemas
    "ServiceHealthStatusSchema",
    "HealthCheckResponseSchema",
    # SystemSetting schemas
    "SystemSettingBaseSchema",
    "SystemSettingCreateSchema",
    "SystemSettingUpdateSchema",
    "SystemSettingResponseSchema",
    # SystemLog schemas
    "SystemLogBaseSchema",
    "SystemLogCreateSchema",
    "SystemLogResponseSchema",
    # PerformanceMetric schemas
    "PerformanceMetricBaseSchema",
    "PerformanceMetricCreateSchema",
    "PerformanceMetricResponseSchema",
]

logger.debug("Ініціалізація пакету схем Pydantic `system` завершена. Усі системні схеми експортовано.")
