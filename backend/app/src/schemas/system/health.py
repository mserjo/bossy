# backend/app/src/schemas/system/health.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделей, пов'язаних з моніторингом стану ("здоров'я") системи,
зокрема для `ServiceHealthStatusModel` (якщо використовується для зберігання історії)
та для відповіді API ендпоінта Health Check.
"""

from pydantic import Field, field_validator
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema, IdentifiedSchema, TimestampedSchema

# --- Схема для відображення запису історії стану сервісу (для читання) ---
class ServiceHealthStatusSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення запису історії стану "здоров'я" компонента системи.
    `created_at` використовується як `checked_at`.
    """
    component_name: str = Field(..., description="Назва компонента, що перевіряється")
    status: str = Field(..., description="Статус компонента ('healthy', 'unhealthy', 'degraded', 'unknown')")
    # `checked_at` - це `created_at` з AuditDatesSchema
    details: Optional[Dict[str, Any]] = Field(None, description="Додаткові деталі про стан (JSON)")

# --- Схема для створення запису історії стану сервісу (внутрішнє використання) ---
class ServiceHealthStatusCreateSchema(BaseSchema):
    """
    Схема для створення нового запису історії стану компонента.
    Зазвичай використовується фоновою задачею моніторингу.
    """
    component_name: str = Field(..., description="Назва компонента")
    status: str = Field(..., description="Статус компонента")
    details: Optional[Dict[str, Any]] = Field(None, description="Додаткові деталі (JSON)")
    # `checked_at` (тобто `created_at`) буде встановлено автоматично.

    @field_validator('status')
    @classmethod
    def status_must_be_known(cls, value: str) -> str:
        known_statuses = ['healthy', 'unhealthy', 'degraded', 'unknown']
        if value not in known_statuses:
            raise ValueError(f"Невідомий статус: '{value}'. Дозволені: {', '.join(known_statuses)}.")
        return value

# --- Схеми для відповіді API Health Check (/health) ---

class HealthCheckComponentSchema(BaseSchema):
    """
    Схема для представлення стану окремого компонента в Health Check API.
    """
    component_name: str = Field(..., description="Назва компонента")
    status: str = Field(..., description="Статус компонента ('healthy', 'unhealthy', 'degraded')")
    message: Optional[str] = Field(None, description="Додаткове повідомлення або деталі помилки")
    # response_time_ms: Optional[float] = Field(None, description="Час відповіді компонента в мілісекундах") # Якщо вимірюється

class OverallHealthStatusSchema(BaseSchema):
    """
    Схема для загального стану системи в Health Check API.
    """
    overall_status: str = Field(..., description="Загальний стан системи ('healthy', 'unhealthy', 'degraded')")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Час перевірки стану")
    # version: Optional[str] = Field(None, description="Версія додатку") # Можна додати
    # environment: Optional[str] = Field(None, description="Поточне середовище (dev, prod)") # Можна додати
    components: List[HealthCheckComponentSchema] = Field(..., description="Список станів окремих компонентів")


# TODO: Переконатися, що схеми відповідають моделі `ServiceHealthStatusModel` (якщо вона використовується).
# `ServiceHealthStatusModel` успадковує від `BaseModel` (id, created_at, updated_at).
# `ServiceHealthStatusSchema` успадковує від `AuditDatesSchema` і додає `component_name, status, details`.
# Це узгоджено.
#
# `HealthCheckComponentSchema` та `OverallHealthStatusSchema` призначені для відповіді
# динамічного Health Check API і можуть не мати прямого відображення в моделях БД,
# якщо історія не зберігається або зберігається лише агреговано.
# Якщо `ServiceHealthStatusModel` використовується для зберігання останнього стану кожного компонента,
# то `HealthCheckComponentSchema` може бути побудована на її основі.
#
# Валідатор для `status` в `ServiceHealthStatusCreateSchema` (закоментований) корисний.
# `timestamp` в `OverallHealthStatusSchema` генерується автоматично при створенні схеми.
# `overall_status` розраховується на основі станів компонентів (наприклад, 'unhealthy', якщо хоча б один компонент 'unhealthy').
# Все виглядає логічно.
# Поля `version` та `environment` в `OverallHealthStatusSchema` (закоментовані)
# можуть бути корисними для додаткової інформації.
# `response_time_ms` в `HealthCheckComponentSchema` (закоментоване) - для деталізації продуктивності.
# Ці схеми готові для використання в Health Check ендпоінті.

ServiceHealthStatusSchema.model_rebuild()
ServiceHealthStatusCreateSchema.model_rebuild()
HealthCheckComponentSchema.model_rebuild()
OverallHealthStatusSchema.model_rebuild()
