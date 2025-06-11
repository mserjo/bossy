# backend/app/src/models/system/monitoring.py
"""
Моделі SQLAlchemy для системного моніторингу.

Цей модуль визначає моделі для запису системних логів (`SystemLog`)
та метрик продуктивності (`PerformanceMetric`), що можуть використовуватися
для аналізу роботи системи, діагностики проблем та моніторингу навантаження.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Dict, Any

from sqlalchemy import String, ForeignKey, Text, JSON, Float, func  # Float для PerformanceMetric.value
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів
from backend.app.src.models.base import Base
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# TODO: Визначити Enum LogLevel в core.dicts.py (може бути схожий на стандартні рівні logging)
# from backend.app.src.core.dicts import LogLevel as LogLevelEnum

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User


class SystemLog(Base):
    """
    Модель Системного Логу.

    Зберігає записи про події в системі, помилки, важливі дії тощо.
    Не замінює файлове логування, а доповнює його для можливості аналізу
    логів через адміністративний інтерфейс або API.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису логу.
        timestamp (Mapped[datetime]): Час виникнення події логу (за замовчуванням - поточний час сервера).
        level (Mapped[str]): Рівень логу (наприклад, "INFO", "ERROR", "DEBUG").
                             TODO: Використовувати Enum `LogLevel`.
        message (Mapped[Text]): Основне повідомлення логу.
        source (Mapped[Optional[str]]): Джерело події (наприклад, назва сервісу, модуля, функції).
        details (Mapped[Optional[Dict[str, Any]]]): Додаткові структуровані деталі у форматі JSON.
        user_id (Mapped[Optional[int]]): ID користувача, пов'язаного з подією (якщо є).

        user (Mapped[Optional["User"]]): Зв'язок з моделлю `User`.
    """
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор запису логу"
    )
    timestamp: Mapped[datetime] = mapped_column(
        default=func.now, nullable=False, index=True, comment="Час виникнення події логу"
    )

    # TODO: Замінити String на Enum LogLevel, коли він буде визначений в core.dicts.py
    # level: Mapped[LogLevelEnum] = mapped_column(SQLEnum(LogLevelEnum), nullable=False, index=True)
    level: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Рівень логу (INFO, ERROR, DEBUG тощо)"
    )

    message: Mapped[str] = mapped_column(Text, nullable=False,
                                         comment="Основне повідомлення логу")  # Використовуємо Text
    source: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="Джерело події (сервіс, модуль, функція)"
    )
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Додаткові структуровані деталі у форматі JSON"
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('users.id', name='fk_system_log_user_id', ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID користувача, пов'язаного з подією (якщо є)"
    )

    # --- Зв'язок (Relationship) ---
    user: Mapped[Optional["User"]] = relationship(lazy="selectin")

    # Поля для __repr__
    _repr_fields = ["id", "timestamp", "level", "source", "user_id"]


class PerformanceMetric(Base):
    """
    Модель Метрики Продуктивності.

    Зберігає записи про різні метрики продуктивності системи,
    такі як час відповіді, використання ресурсів тощо.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису метрики.
        timestamp (Mapped[datetime]): Час запису метрики.
        metric_name (Mapped[str]): Назва метрики (наприклад, "api_response_time", "db_query_duration").
        value (Mapped[float]): Значення метрики.
        unit (Mapped[Optional[str]]): Одиниця виміру метрики (наприклад, "ms", "s", "count", "MB").
        tags (Mapped[Optional[Dict[str, str]]]): Теги/мітки для групування або фільтрації метрик (у форматі JSON).
    """
    __tablename__ = "performance_metrics"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор запису метрики"
    )
    timestamp: Mapped[datetime] = mapped_column(
        default=func.now, nullable=False, index=True, comment="Час запису метрики"
    )
    metric_name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, comment="Назва метрики"
    )
    value: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Значення метрики"
    )
    unit: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Одиниця виміру (ms, count, MB тощо)"
    )
    tags: Mapped[Optional[Dict[str, str]]] = mapped_column(
        JSON, nullable=True, comment="Теги/мітки для метрики (key-value JSON)"
    )

    # Поля для __repr__
    _repr_fields = ["id", "timestamp", "metric_name", "value", "unit"]


if __name__ == "__main__":
    # Демонстраційний блок для моделей моніторингу.
    logger.info("--- Моделі Системного Моніторингу ---")

    logger.info(f"\n--- Модель Системного Логу (SystemLog) ---")
    logger.info(f"Назва таблиці: {SystemLog.__tablename__}")
    logger.info("Очікувані поля: id, timestamp, level, message, source, details, user_id")

    example_log = SystemLog(
        id=1,
        timestamp=datetime.now(timezone.utc),
        level="INFO",  # TODO: Замінити на LogLevelEnum.INFO.value
        message="Користувач успішно увійшов в систему.",  # TODO i18n
        source="auth_service",
        user_id=101
    )
    logger.info(f"Приклад екземпляра SystemLog (без сесії):\n  {example_log}")

    logger.info(f"\n--- Модель Метрики Продуктивності (PerformanceMetric) ---")
    logger.info(f"Назва таблиці: {PerformanceMetric.__tablename__}")
    logger.info("Очікувані поля: id, timestamp, metric_name, value, unit, tags")

    example_metric = PerformanceMetric(
        id=1,
        timestamp=datetime.now(timezone.utc),
        metric_name="api_v1_items_response_time",
        value=25.5,
        unit="ms",
        tags={"endpoint": "/api/v1/items", "method": "GET"}
    )
    logger.info(f"Приклад екземпляра PerformanceMetric (без сесії):\n  {example_metric}")

    logger.info("\nПримітка: Для повноцінної роботи з моделями потрібна сесія SQLAlchemy та підключення до БД.")
    logger.info("TODO: Не забудьте визначити Enum 'LogLevel' в core.dicts.py та оновити поле 'level' в SystemLog.")
