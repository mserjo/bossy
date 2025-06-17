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
from backend.app.src.config.logging import get_logger
from backend.app.src.core.dicts import HealthStatusType # Імпорт Enum
from sqlalchemy import Enum as SQLEnum # Імпорт SQLEnum
logger = get_logger(__name__)


class ServiceHealthStatus(Base, TimestampedMixin):
    """
    Модель Стану Здоров'я Сервісу.

    Зберігає інформацію про останній відомий стан здоров'я певного сервісу.
    Поле `updated_at` з `TimestampedMixin` використовується як час останньої перевірки
    стану (`last_checked_at`).

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису стану.
        service_name (Mapped[str]): Унікальна назва сервісу (наприклад, "database", "redis_cache", "payment_gateway").
        status (Mapped[HealthStatusType]): Поточний статус сервісу (використовує Enum `HealthStatusType`).
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

    status: Mapped[HealthStatusType] = mapped_column(
        SQLEnum(HealthStatusType), nullable=False, index=True, comment="Статус сервісу (healthy, unhealthy тощо)"
    )

    details: Mapped[Optional[str]] = mapped_column(  # Використовуємо Text для потенційно довгих деталей
        Text, nullable=True, comment="Додаткові деталі про стан сервісу (напр., повідомлення про помилку)"
    )
    # `updated_at` з TimestampedMixin використовується як `last_checked_at`

    # Поля для __repr__
    # `id` автоматично додається через Base.__repr__
    # `created_at`, `updated_at` успадковуються з TimestampedMixin._repr_fields
    _repr_fields = ("service_name", "status")


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
        status=HealthStatusType.HEALTHY,  # Використання Enum
        details="Успішне підключення та виконання тестового запиту."  # TODO i18n
    )
    # Імітуємо часові мітки (updated_at - час останньої перевірки)
    example_health_status.created_at = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    example_health_status.updated_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра ServiceHealthStatus (без сесії):\n  {example_health_status}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <ServiceHealthStatus(id=1, service_name='База даних PostgreSQL', status=<HealthStatusType.HEALTHY: 'healthy'>, updated_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
