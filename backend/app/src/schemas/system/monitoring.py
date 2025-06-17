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
logger = get_logger(__name__)

# LogLevel Enum імпортовано вище.
# TODO: Замінити Any на UserPublicProfileSchema, коли вона буде доступна/рефакторена.
# from backend.app.src.schemas.auth.user import UserPublicProfileSchema

UserPublicProfileSchema = Any  # Тимчасовий заповнювач


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
        default_factory=datetime.now,  # Клієнт може надати, але сервер може перезаписати
        description="Час виникнення події логу."
    )
    level: LogLevel = Field(
        description="Рівень логу."
    )
    message: str = Field(description="Основне повідомлення логу.")
    source: Optional[str] = Field(
        None,
        max_length=LOG_SOURCE_MAX_LENGTH,
        description="Джерело події (наприклад, назва сервісу, модуля, функції).",
        examples=["auth_service", "task_scheduler"]
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Додаткові структуровані деталі у форматі JSON."
    )
    user_id: Optional[int] = Field(
        None,
        description="ID користувача, пов'язаного з подією логу (якщо є)."
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

    # TODO: Замінити Any на UserPublicProfileSchema.
    user: Optional[UserPublicProfileSchema] = Field(None,
                                                    description="Інформація про користувача, пов'язаного з логом (якщо є).")


# --- Схеми для Метрик Продуктивності (PerformanceMetric) ---

class PerformanceMetricBaseSchema(BaseSchema):
    """
    Базова схема для полів метрики продуктивності.
    """
    # timestamp встановлюється сервером за замовчуванням (default=func.now() в моделі)
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="Час запису метрики."
    )
    metric_name: str = Field(
        ...,
        max_length=METRIC_NAME_MAX_LENGTH,
        description="Назва метрики (наприклад, 'api_response_time', 'db_query_duration')."
    )
    value: float = Field(description="Значення метрики.")
    unit: Optional[str] = Field(
        None,
        max_length=METRIC_UNIT_MAX_LENGTH,
        description="Одиниця виміру метрики (наприклад, 'ms', 's', 'count', 'MB').",
        examples=["ms", "count"]
    )
    tags: Optional[Dict[str, str]] = Field(
        None,
        description="Теги/мітки для групування або фільтрації метрик (у форматі ключ-значення)."
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
        "level": LogLevel.ERROR, # Використовуємо Enum
        "message": "Не вдалося підключитися до зовнішнього сервісу 'X'.",  # TODO i18n
        "source": "integration_module",
        # "user": {"id": 101, "name": "Ініціатор Дії"} # Приклад UserPublicProfileSchema
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
    # logger.info("TODO: Інтегрувати Enum 'LogLevel' з core.dicts для поля 'level' в SystemLog.") # Вирішено
    logger.info("TODO: Замінити Any на UserPublicProfileSchema в SystemLogSchema.")
