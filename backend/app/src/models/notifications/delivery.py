# backend/app/src/models/notifications/delivery.py
"""
Модель SQLAlchemy для сутності "Спроба Доставки Сповіщення" (NotificationDeliveryAttempt).

Цей модуль визначає модель `NotificationDeliveryAttempt`, яка відстежує
спроби доставки конкретного сповіщення через різні канали (наприклад, email, SMS)
та їх результат.
"""
from datetime import datetime, timezone  # timezone для __main__
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Text, func  # func для server_default в TimestampedMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # `created_at` як час спроби доставки
from backend.app.src.config.logging import get_logger # Імпорт логера
from backend.app.src.core.dicts import NotificationChannelType, DeliveryStatusType # Імпорт Enum
from sqlalchemy import Enum as SQLEnum # Імпорт SQLEnum
# Отримання логера для цього модуля
logger = get_logger(__name__)


if TYPE_CHECKING:
    from backend.app.src.models.notifications.notification import Notification


class NotificationDeliveryAttempt(Base, TimestampedMixin):
    """
    Модель Спроби Доставки Сповіщення.

    Зберігає інформацію про кожну спробу доставки сповіщення, канал, статус
    та можливі повідомлення про помилки. Поле `created_at` з `TimestampedMixin`
    використовується як час здійснення спроби (`attempted_at`).

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор спроби доставки.
        notification_id (Mapped[int]): ID сповіщення, яке намагалися доставити.
        channel (Mapped[str]): Канал доставки (наприклад, "email", "sms").
                               TODO: Використовувати Enum `NotificationChannelType`.
        status (Mapped[str]): Статус спроби доставки (наприклад, "sent", "failed").
                              TODO: Використовувати Enum `DeliveryStatusType`.
        error_message (Mapped[Optional[str]]): Повідомлення про помилку, якщо доставка не вдалася.
        external_message_id (Mapped[Optional[str]]): ID повідомлення від зовнішнього провайдера (якщо є).

        notification (Mapped["Notification"]): Зв'язок з моделлю `Notification`.
        created_at, updated_at: Успадковано. `created_at` - час спроби.
    """
    __tablename__ = "notification_delivery_attempts"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор спроби доставки"
    )
    notification_id: Mapped[int] = mapped_column(
        ForeignKey('notifications.id', name='fk_delivery_attempt_notification_id', ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID сповіщення, яке доставлялося"
    )

    channel: Mapped[NotificationChannelType] = mapped_column(
        SQLEnum(NotificationChannelType), nullable=False, index=True, comment="Канал доставки (email, sms, in_app тощо)"
    )

    status: Mapped[DeliveryStatusType] = mapped_column(
        SQLEnum(DeliveryStatusType), nullable=False, index=True, comment="Статус спроби доставки (pending, sent, failed)"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Повідомлення про помилку у випадку невдалої доставки"
    )
    external_message_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True,
        comment="Зовнішній ID повідомлення від провайдера (напр. SES Message ID)"
    )

    # --- Зв'язки (Relationships) ---
    notification: Mapped["Notification"] = relationship(back_populates="delivery_attempts", lazy="selectin")

    # Поля для __repr__
    # `id` автоматично додається через Base.__repr__
    # `created_at`, `updated_at` успадковуються з TimestampedMixin._repr_fields
    _repr_fields = ("notification_id", "channel", "status")


if __name__ == "__main__":
    # Демонстраційний блок для моделі NotificationDeliveryAttempt.
    logger.info("--- Модель Спроби Доставки Сповіщення (NotificationDeliveryAttempt) ---")
    logger.info(f"Назва таблиці: {NotificationDeliveryAttempt.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = [
        'id', 'notification_id', 'channel', 'status',
        'error_message', 'external_message_id', 'created_at', 'updated_at'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['notification']
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_attempt = NotificationDeliveryAttempt(
        id=1,
        notification_id=1,  # ID сповіщення
        channel=NotificationChannelType.EMAIL,  # Використання Enum
        status=DeliveryStatusType.SENT,  # Використання Enum
        external_message_id="ses-message-id-12345"
    )
    # Імітуємо часові мітки (created_at - час спроби)
    example_attempt.created_at = datetime.now(tz=timezone.utc)
    example_attempt.updated_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра NotificationDeliveryAttempt (без сесії):\n  {example_attempt}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <NotificationDeliveryAttempt(id=1, notification_id=1, channel=<NotificationChannelType.EMAIL: 'email'>, status=<DeliveryStatusType.SENT: 'sent'>, created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
