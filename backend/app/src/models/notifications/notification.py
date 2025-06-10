# backend/app/src/models/notifications/notification.py
"""
Модель SQLAlchemy для сутності "Сповіщення" (Notification).

Цей модуль визначає модель `Notification`, яка представляє окреме сповіщення,
надіслане користувачеві. Воно може бути створене на основі шаблону
або мати кастомний вміст.
"""
from datetime import datetime, timezone  # timezone для __main__
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, ForeignKey, Text, Boolean, Integer  # Integer для related_entity_id
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів та Enum
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # `created_at` як час створення сповіщення
from backend.app.src.core.dicts import NotificationType as NotificationTypeEnum  # Реальний Enum з core.dicts

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.notifications.template import NotificationTemplate
    from backend.app.src.models.notifications.delivery import NotificationDeliveryAttempt


class Notification(Base, TimestampedMixin):
    """
    Модель Сповіщення.

    Зберігає інформацію про конкретне сповіщення, надіслане користувачеві,
    включаючи його вміст, статус прочитання, тип та зв'язок з іншими сутностями.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор сповіщення.
        user_id (Mapped[int]): ID користувача-отримувача сповіщення.
        template_id (Mapped[Optional[int]]): ID шаблону, на основі якого створено сповіщення (якщо є).
        title (Mapped[str]): Заголовок сповіщення.
        message (Mapped[Text]): Тіло сповіщення (вже відрендерений текст).
        is_read (Mapped[bool]): Прапорець, чи прочитано сповіщення користувачем.
        read_at (Mapped[Optional[datetime]]): Час, коли сповіщення було позначено як прочитане.
        notification_type (Mapped[str]): Тип сповіщення (використовує `core.dicts.NotificationType`).
        related_entity_type (Mapped[Optional[str]]): Тип пов'язаної сутності (наприклад, "task", "group").
        related_entity_id (Mapped[Optional[int]]): ID пов'язаної сутності.

        user (Mapped["User"]): Зв'язок з користувачем-отримувачем.
        template (Mapped[Optional["NotificationTemplate"]]): Зв'язок з використаним шаблоном.
        delivery_attempts (Mapped[List["NotificationDeliveryAttempt"]]): Спроби доставки цього сповіщення.
        created_at, updated_at: Успадковано. `created_at` - час створення.
    """
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор сповіщення"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', name='fk_notification_user_id', ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID користувача-отримувача сповіщення"
    )
    template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('notification_templates.id', name='fk_notification_template_id', ondelete="SET NULL"),
        nullable=True,
        comment="ID шаблону, на основі якого створено сповіщення (якщо є)"
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="Заголовок сповіщення")
    message: Mapped[str] = mapped_column(Text, nullable=False,
                                         comment="Тіло сповіщення (відрендерений текст)")  # Використовуємо Text замість String

    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True, comment="Статус прочитання сповіщення"
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, comment="Час, коли сповіщення було позначено як прочитане"
    )

    # Використовуємо значення з Enum NotificationType
    # TODO: Переконатися, що SQLEnum імпортовано та використовується, якщо тип колонки в БД є Enum.
    # notification_type: Mapped[NotificationTypeEnum] = mapped_column(SQLEnum(NotificationTypeEnum), nullable=False, index=True)
    notification_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Тип сповіщення (з core.dicts.NotificationType)"
    )

    # Поля для зв'язку з конкретною сутністю, до якої відноситься сповіщення
    related_entity_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Тип пов'язаної сутності (наприклад, 'task', 'group', 'bonus')"
    )
    related_entity_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True, comment="ID пов'язаної сутності"
    )

    # --- Зв'язки (Relationships) ---
    user: Mapped["User"] = relationship(lazy="selectin")  # back_populates="notifications" можна додати до User
    template: Mapped[Optional["NotificationTemplate"]] = relationship(
        lazy="selectin")  # back_populates="notifications" можна додати до NotificationTemplate

    delivery_attempts: Mapped[List["NotificationDeliveryAttempt"]] = relationship(
        back_populates="notification", cascade="all, delete-orphan", lazy="selectin"
    )

    # Поля для __repr__
    _repr_fields = ["id", "user_id", "notification_type", "title", "is_read"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі Notification.
    print("--- Модель Сповіщення (Notification) ---")
    print(f"Назва таблиці: {Notification.__tablename__}")

    print("\nОчікувані поля:")
    expected_fields = [
        'id', 'user_id', 'template_id', 'title', 'message', 'is_read', 'read_at',
        'notification_type', 'related_entity_type', 'related_entity_id',
        'created_at', 'updated_at'
    ]
    for field in expected_fields:
        print(f"  - {field}")

    print("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['user', 'template', 'delivery_attempts']
    for rel in expected_relationships:
        print(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_notification = Notification(
        id=1,
        user_id=101,
        title="Нове завдання призначено",  # TODO i18n
        message="Вам було призначено нове завдання 'Розробити API'. Термін виконання: 2023-12-31.",  # TODO i18n
        notification_type=NotificationTypeEnum.TASK_ASSIGNED.value,  # Використання значення Enum
        related_entity_type="task",
        related_entity_id=1
    )
    # Імітуємо часові мітки
    example_notification.created_at = datetime.now(tz=timezone.utc)
    example_notification.updated_at = datetime.now(tz=timezone.utc)

    print(f"\nПриклад екземпляра Notification (без сесії):\n  {example_notification}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <Notification(id=1, user_id=101, notification_type='task_assigned', title='Нове завдання призначено', is_read=False, created_at=...)>

    print("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
    print(
        f"Використовується NotificationType Enum для поля 'notification_type', наприклад: NotificationTypeEnum.BONUS_AWARDED = '{NotificationTypeEnum.BONUS_AWARDED.value}'")
