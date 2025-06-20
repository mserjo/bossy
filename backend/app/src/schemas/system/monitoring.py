# backend/app/src/schemas/system/monitoring.py
"""
Pydantic схеми для сутностей системного моніторингу.

Цей модуль визначає схеми для:
- `SystemLogSchema`, `SystemLogCreateSchema`: для записів системного логу.
- `PerformanceMetricSchema`, `PerformanceMetricCreateSchema`: для метрик продуктивності.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List  # List може знадобитися для відповідей зі списками

from pydantic import Field

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin  # TimestampedSchemaMixin тут не потрібен, бо timestamp є власним полем
from backend.app.src.core.dicts import LogLevel # Імпортовано LogLevel Enum
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)

# LogLevel Enum імпортовано вище.
from backend.app.src.schemas.auth.user import UserPublicProfileSchema


# Placeholder UserPublicProfileSchema = Any removed

# LOG_LEVEL_MAX_LENGTH = 50 # Не потрібен для Enum
LOG_MESSAGE_MAX_LENGTH_DISPLAY = 1000  # Для відображення, Text в моделі може бути довшим
LOG_SOURCE_MAX_LENGTH = 255
METRIC_NAME_MAX_LENGTH = 255
METRIC_UNIT_MAX_LENGTH = 50


# --- Схеми для Системного Логу (SystemLog) ---

class SystemLogBaseSchema(BaseSchema):
    """
    Базова схема для полів запису системного логу.
    """
    # timestamp встановлюється сервером за замовчуванням (default=func.now() в моделі)
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.now,
        description=_("system.monitoring.log.fields.timestamp.description")
    )
    level: LogLevel = Field(
        description=_("system.monitoring.log.fields.level.description")
    )
    message: str = Field(description=_("system.monitoring.log.fields.message.description"))
    source: Optional[str] = Field(
        None,
        max_length=LOG_SOURCE_MAX_LENGTH,
        description=_("system.monitoring.log.fields.source.description"),
        examples=["auth_service", "task_scheduler"]
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description=_("system.monitoring.log.fields.details.description")
    )
    user_id: Optional[int] = Field(
        None,
        description=_("system.monitoring.log.fields.user_id.description")
    )
    # model_config успадковується з BaseSchema (from_attributes=True)


class SystemLogCreateSchema(SystemLogBaseSchema):
    """
    Схема для створення нового запису системного логу.
    Зазвичай використовується внутрішніми сервісами для запису подій.
    """
    # Успадковує всі поля від SystemLogBaseSchema.
    # `timestamp` може бути встановлено автоматично сервером, якщо не надано.
    pass


class SystemLogSchema(SystemLogBaseSchema, IDSchemaMixin):
    """
    Схема для представлення даних запису системного логу у відповідях API.
    Успадковує `id` від `IDSchemaMixin`.
    """
    # id успадковано.
    # timestamp, level, message, source, details, user_id успадковані.

    user: Optional[UserPublicProfileSchema] = Field(None,
                                                    description=_("system.monitoring.log.response.fields.user.description"))


# --- Схеми для Метрик Продуктивності (PerformanceMetric) ---

class PerformanceMetricBaseSchema(BaseSchema):
    """
    Базова схема для полів метрики продуктивності.
    """
    # timestamp встановлюється сервером за замовчуванням (default=func.now() в моделі)
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.now,
        description=_("system.monitoring.metric.fields.timestamp.description")
    )
    metric_name: str = Field(
        ...,
        max_length=METRIC_NAME_MAX_LENGTH,
        description=_("system.monitoring.metric.fields.metric_name.description")
    )
    value: float = Field(description=_("system.monitoring.metric.fields.value.description"))
    unit: Optional[str] = Field(
        None,
        max_length=METRIC_UNIT_MAX_LENGTH,
        description=_("system.monitoring.metric.fields.unit.description"),
        examples=["ms", "count"]
    )
    tags: Optional[Dict[str, str]] = Field(
        None,
        description=_("system.monitoring.metric.fields.tags.description")
    )
    # model_config успадковується з BaseSchema (from_attributes=True)


class PerformanceMetricCreateSchema(PerformanceMetricBaseSchema):
    """
    Схема для створення нового запису метрики продуктивності.
    """
    # Успадковує всі поля від PerformanceMetricBaseSchema.
    pass


class PerformanceMetricSchema(PerformanceMetricBaseSchema, IDSchemaMixin):
    """
    Схема для представлення даних метрики продуктивності у відповідях API.
    Успадковує `id` від `IDSchemaMixin`.
    """
    # id успадковано.
    # timestamp, metric_name, value, unit, tags успадковані.
    pass


if __name__ == "__main__":
    # Демонстраційний блок для схем моніторингу.
    logger.info("--- Pydantic Схеми для Моніторингу (SystemLog, PerformanceMetric) ---")

    logger.info("\nSystemLogCreateSchema (приклад для створення логу):")
    create_log_data = {
        "level": LogLevel.INFO, # Використовуємо Enum
        "message": "Користувач user@example.com успішно оновив профіль.",  # TODO i18n
        "source": "user_profile_service",
        "user_id": 101,
        "details": {"profile_fields_updated": ["last_name", "phone_number"]}
    }
    create_log_instance = SystemLogCreateSchema(**create_log_data)
    # timestamp буде додано автоматично default_factory, якщо не передано
    logger.info(create_log_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nSystemLogSchema (приклад відповіді API):")
    log_response_data = {
        "id": 1,
        "timestamp": datetime.now(),
        "level": LogLevel.ERROR,
        "message": "Не вдалося підключитися до зовнішнього сервісу 'X'.",
        "source": "integration_module",
        "user_id": 101, # Додамо user_id для консистентності з прикладом user
        "user": { # Приклад UserPublicProfileSchema
            "id": 101,
            "username": "logger_user",
            "name": "Ініціатор Логування", # TODO i18n
            "avatar_url": "https://example.com/avatars/logger.png"
        }
    }
    log_response_instance = SystemLogSchema(**log_response_data)
    logger.info(log_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nPerformanceMetricCreateSchema (приклад для створення метрики):")
    create_metric_data = {
        "metric_name": "login_api_response_time",
        "value": 125.5,
        "unit": "ms",
        "tags": {"endpoint": "/api/v1/auth/login", "method": "POST"}
    }
    create_metric_instance = PerformanceMetricCreateSchema(**create_metric_data)
    logger.info(create_metric_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nPerformanceMetricSchema (приклад відповіді API):")
    metric_response_data = {
        "id": 1,
        "timestamp": datetime.now(),
        "metric_name": "active_users_count",
        "value": 1500.0,
        "unit": "count"
    }
    metric_response_instance = PerformanceMetricSchema(**metric_response_data)
    logger.info(metric_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації та серіалізації даних системного моніторингу.")
    logger.info("UserPublicProfileSchema тепер використовується в SystemLogSchema.")
