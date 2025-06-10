# backend/app/src/models/system/health.py
"""
Модель SQLAlchemy для сутності "Стан Здоров'я Сервісу" (ServiceHealthStatus).

Цей модуль визначає модель `ServiceHealthStatus`, яка використовується для
відстеження стану здоров'я різних внутрішніх або зовнішніх сервісів,
від яких залежить робота програми Kudos (наприклад, база даних, Redis,
зовнішні API).
"""
from datetime import datetime, timezone  # timezone для __main__
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text, func  # func для server_default в TimestampedMixin
from sqlalchemy.orm import Mapped, mapped_column  # relationship тут не потрібен, якщо немає прямих зв'язків

# Абсолютний імпорт базових класів та міксинів
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # `updated_at` як час останньої перевірки
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


# TODO: Визначити Enum HealthStatusType в core.dicts.py, наприклад:
# class HealthStatusType(str, Enum):
#     HEALTHY = "healthy"      # Сервіс працює нормально
#     UNHEALTHY = "unhealthy"    # Сервіс не працює або не відповідає
#     DEGRADED = "degraded"     # Сервіс працює, але з проблемами (повільно, частково)
#     UNKNOWN = "unknown"      # Стан сервісу невідомий
# Потім імпортувати: from backend.app.src.core.dicts import HealthStatusType

class ServiceHealthStatus(Base, TimestampedMixin):
    """
    Модель Стану Здоров'я Сервісу.

    Зберігає інформацію про останній відомий стан здоров'я певного сервісу.
    Поле `updated_at` з `TimestampedMixin` використовується як час останньої перевірки
    стану (`last_checked_at`).

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису стану.
        service_name (Mapped[str]): Унікальна назва сервісу (наприклад, "database", "redis_cache", "payment_gateway").
        status (Mapped[str]): Поточний статус сервісу (наприклад, "healthy", "unhealthy").
                              TODO: Використовувати Enum `HealthStatusType`.
        details (Mapped[Optional[Text]]): Додаткові деталі про стан (наприклад, повідомлення про помилку).

        created_at, updated_at: Успадковано. `updated_at` - час останньої перевірки.
    """
    __tablename__ = "service_health_status"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор запису стану"
    )
    service_name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True, comment="Унікальна назва сервісу"
    )

    # TODO: Замінити String на Enum HealthStatusType, коли він буде визначений в core.dicts.py
    # status: Mapped[HealthStatusType] = mapped_column(SQLEnum(HealthStatusType), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Статус сервісу (healthy, unhealthy тощо)"
    )

    details: Mapped[Optional[str]] = mapped_column(  # Використовуємо Text для потенційно довгих деталей
        Text, nullable=True, comment="Додаткові деталі про стан сервісу (напр., повідомлення про помилку)"
    )
    # `updated_at` з TimestampedMixin використовується як `last_checked_at`

    # Поля для __repr__
    # `created_at`, `updated_at` успадковуються з TimestampedMixin._repr_fields
    _repr_fields = ["id", "service_name", "status"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі ServiceHealthStatus.
    logger.info("--- Модель Стану Здоров'я Сервісу (ServiceHealthStatus) ---")
    logger.info(f"Назва таблиці: {ServiceHealthStatus.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = ['id', 'service_name', 'status', 'details', 'created_at', 'updated_at']
    for field in expected_fields:
        logger.info(f"  - {field}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_health_status = ServiceHealthStatus(
        id=1,
        service_name="База даних PostgreSQL",  # TODO i18n
        status="healthy",  # TODO: Замінити на HealthStatusType.HEALTHY.value
        details="Успішне підключення та виконання тестового запиту."  # TODO i18n
    )
    # Імітуємо часові мітки (updated_at - час останньої перевірки)
    example_health_status.created_at = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    example_health_status.updated_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра ServiceHealthStatus (без сесії):\n  {example_health_status}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <ServiceHealthStatus(id=1, service_name='База даних PostgreSQL', status='healthy', updated_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
    logger.info("TODO: Не забудьте визначити Enum 'HealthStatusType' в core.dicts.py та оновити поле 'status'.")
