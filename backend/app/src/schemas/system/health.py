# backend/app/src/schemas/system/health.py
"""
Pydantic схеми для сутностей, пов'язаних зі станом здоров'я системи.

Цей модуль визначає схеми для:
- `ServiceHealthStatusSchema`: Представлення стану здоров'я окремого сервісу.
- `OverallHealthStatusSchema`: Представлення загального стану здоров'я системи,
                                включаючи стан залежних сервісів.
"""
from datetime import datetime
from typing import Optional, List, Any  # Any може не знадобитися, якщо всі типи конкретні

from pydantic import Field

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# TODO: Визначити та імпортувати Enum HealthStatusType з core.dicts
# from backend.app.src.core.dicts import HealthStatusType

# Заглушка для HealthStatusType Enum
class TempHealthStatusType:  # TODO: Видалити після імпорту Enum
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


SERVICE_NAME_MAX_LENGTH = 100
HEALTH_STATUS_MAX_LENGTH = 50


class ServiceHealthStatusBaseSchema(BaseSchema):
    """
    Базова схема для полів стану здоров'я окремого сервісу.
    """
    service_name: str = Field(
        ...,
        max_length=SERVICE_NAME_MAX_LENGTH,
        description="Унікальна назва сервісу (наприклад, 'database', 'redis_cache', 'payment_gateway')."
    )
    # TODO: Замінити str на HealthStatusType та додати валідатор.
    status: str = Field(
        max_length=HEALTH_STATUS_MAX_LENGTH,
        description=f"Поточний статус сервісу (наприклад, '{TempHealthStatusType.HEALTHY}', '{TempHealthStatusType.UNHEALTHY}')."
    )
    details: Optional[str] = Field(
        None,
        description="Додаткові деталі про стан сервісу (наприклад, повідомлення про помилку або час відповіді)."
    )
    # model_config успадковується з BaseSchema (from_attributes=True)


class ServiceHealthStatusSchema(ServiceHealthStatusBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про стан здоров'я окремого сервісу у відповідях API.
    Поле `updated_at` (з `TimestampedSchemaMixin`) позначає час останньої перевірки стану.
    """
    # id, created_at, updated_at успадковані.
    # service_name, status, details успадковані.

    # `updated_at` тут інтерпретується як `last_checked_at`


class OverallHealthStatusSchema(BaseSchema):
    """
    Схема для представлення загального стану здоров'я системи.
    Включає загальний статус та список станів окремих залежних сервісів.
    """
    # TODO: Замінити str на HealthStatusType та додати валідатор.
    overall_status: str = Field(
        description=f"Загальний агрегований статус здоров'я системи (наприклад, '{TempHealthStatusType.HEALTHY}')."
    )
    timestamp: datetime = Field(description="Час генерації звіту про стан здоров'я.")
    services: List[ServiceHealthStatusSchema] = Field(
        default_factory=list,
        description="Список станів здоров'я окремих залежних сервісів."
    )


if __name__ == "__main__":
    # Демонстраційний блок для схем стану здоров'я системи.
    logger.info("--- Pydantic Схеми для Стану Здоров'я Системи ---")

    logger.info("\nServiceHealthStatusSchema (приклад відповіді API для окремого сервісу):")
    db_health_data = {
        "id": 1,
        "service_name": "PostgreSQL Database",  # TODO i18n
        "status": TempHealthStatusType.HEALTHY,  # TODO: Замінити на Enum.value
        "details": "Підключення успішне, середній час запиту 15мс.",  # TODO i18n
        "created_at": datetime.now() - timedelta(hours=1),
        "updated_at": datetime.now()  # Час останньої перевірки
    }
    db_health_instance = ServiceHealthStatusSchema(**db_health_data)
    logger.info(db_health_instance.model_dump_json(indent=2, exclude_none=True))

    redis_health_data = {
        "id": 2,
        "service_name": "Redis Cache",  # TODO i18n
        "status": TempHealthStatusType.UNHEALTHY,  # TODO: Замінити на Enum.value
        "details": "Не вдалося підключитися до сервера Redis: Connection refused.",  # TODO i18n
        "created_at": datetime.now() - timedelta(minutes=30),
        "updated_at": datetime.now() - timedelta(minutes=5)
    }
    redis_health_instance = ServiceHealthStatusSchema(**redis_health_data)
    logger.info(redis_health_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nOverallHealthStatusSchema (приклад загального звіту про стан здоров'я):")
    overall_status_data = {
        "overall_status": TempHealthStatusType.DEGRADED,
        # TODO: Замінити на Enum.value (розраховується на основі станів сервісів)
        "timestamp": datetime.now(),
        "services": [
            db_health_instance.model_dump(),  # Використовуємо .model_dump() для отримання dict
            redis_health_instance.model_dump()
        ]
    }
    overall_status_instance = OverallHealthStatusSchema(**overall_status_data)
    logger.info(overall_status_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для представлення стану здоров'я системи та її компонентів.")
    logger.info("TODO: Інтегрувати Enum 'HealthStatusType' з core.dicts для полів 'status' та 'overall_status'.")

# Потрібно для timedelta в __main__
from datetime import timedelta
