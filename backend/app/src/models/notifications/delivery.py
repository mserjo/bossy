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

# TODO: Визначити Enums NotificationChannelType та DeliveryStatusType в core.dicts.py
# Наприклад:
# class NotificationChannelType(str, Enum):
#     EMAIL = "email"
#     SMS = "sms"
#     IN_APP = "in_app" # Внутрішнє сповіщення в додатку
#     PUSH_NOTIFICATION = "push_notification" # Мобільний пуш
#     WEBHOOK = "webhook" # Виклик зовнішнього вебхука
#
# class DeliveryStatusType(str, Enum):
#     PENDING = "pending"    # Очікує на відправку
#     SENT = "sent"        # Успішно надіслано провайдеру/сервісу
#     FAILED = "failed"      # Не вдалося надіслати (помилка на нашому боці або у провайдера)
#     DELIVERED = "delivered"  # Підтверджено доставку (якщо провайдер це підтримує)
#     READ = "read"          # Прочитано (для деяких каналів, як email, якщо є трекінг)
#     ERROR = "error"        # Загальна помилка під час спроби
# Потім імпортувати їх.

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

    # TODO: Замінити String на Enum NotificationChannelType, коли він буде визначений в core.dicts.py
    # channel: Mapped[NotificationChannelType] = mapped_column(SQLEnum(NotificationChannelType), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Канал доставки (email, sms, in_app тощо)"
    )

    # TODO: Замінити String на Enum DeliveryStatusType, коли він буде визначений в core.dicts.py
    # status: Mapped[DeliveryStatusType] = mapped_column(SQLEnum(DeliveryStatusType), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Статус спроби доставки (pending, sent, failed)"
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
    _repr_fields = ["id", "notification_id", "channel", "status"]  # created_at з TimestampedMixin


if __name__ == "__main__":
    # Демонстраційний блок для моделі NotificationDeliveryAttempt.
    print("--- Модель Спроби Доставки Сповіщення (NotificationDeliveryAttempt) ---")
    print(f"Назва таблиці: {NotificationDeliveryAttempt.__tablename__}")

    print("\nОчікувані поля:")
    expected_fields = [
        'id', 'notification_id', 'channel', 'status',
        'error_message', 'external_message_id', 'created_at', 'updated_at'
    ]
    for field in expected_fields:
        print(f"  - {field}")

    print("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['notification']
    for rel in expected_relationships:
        print(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_attempt = NotificationDeliveryAttempt(
        id=1,
        notification_id=1,  # ID сповіщення
        channel="email",  # TODO: Замінити на NotificationChannelType.EMAIL.value
        status="sent",  # TODO: Замінити на DeliveryStatusType.SENT.value
        external_message_id="ses-message-id-12345"
    )
    # Імітуємо часові мітки (created_at - час спроби)
    example_attempt.created_at = datetime.now(tz=timezone.utc)
    example_attempt.updated_at = datetime.now(tz=timezone.utc)

    print(f"\nПриклад екземпляра NotificationDeliveryAttempt (без сесії):\n  {example_attempt}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <NotificationDeliveryAttempt(id=1, notification_id=1, channel='email', status='sent', created_at=...)>

    print("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
    print(
        "TODO: Не забудьте визначити Enum 'NotificationChannelType' та 'DeliveryStatusType' в core.dicts.py та оновити відповідні поля.")
