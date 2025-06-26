# backend/app/src/models/notifications/notification.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `NotificationModel` для зберігання сповіщень,
які надсилаються користувачам системи. Сповіщення можуть бути внутрішніми (в додатку)
або зовнішніми (email, SMS, месенджери - через DeliveryModel).
"""
from typing import Optional, Dict, Any, List

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Index  # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column  # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

# Використовуємо BaseModel, оскільки сповіщення - це запис про подію.
# Якщо сповіщення мають заголовок/тіло, які можна вважати name/description,
# то BaseMainModel може бути варіантом, але title/body тут більш специфічні.
from backend.app.src.models.base import BaseModel

class NotificationModel(BaseModel):
    """
    Модель для зберігання сповіщень.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор сповіщення (успадковано).
        recipient_user_id (uuid.UUID): Ідентифікатор користувача-отримувача сповіщення.
        group_id (uuid.UUID | None): Ідентифікатор групи, в контексті якої створено сповіщення.
                                      NULL, якщо сповіщення системне або не стосується групи.

        title (str | None): Заголовок сповіщення.
        body (Text): Основний текст (вміст) сповіщення. Може містити HTML або Markdown.
        notification_type_code (str): Код типу сповіщення (наприклад, "TASK_STATUS_CHANGE", "NEW_REWARD", "GROUP_INVITATION").
                                      TODO: Визначити Enum або довідник для типів сповіщень.

        # Посилання на сутність, що спричинила сповіщення
        source_entity_type (str | None): Тип сутності ('task', 'reward', 'user', 'group_invitation').
        source_entity_id (uuid.UUID | None): ID сутності-джерела.

        # Статус прочитання
        is_read (bool): Чи прочитане сповіщення користувачем.
        read_at (datetime | None): Час, коли сповіщення було прочитане.

        # Параметри для відображення та дій
        # url_link (str | None): URL, на який переходить користувач при кліку на сповіщення.
        # action_buttons (JSONB | None): Визначення кнопок дій для сповіщення (наприклад, {"label": "Прийняти", "action": "accept_invite"}).
        metadata (JSONB | None): Додаткові дані для сповіщення.

        created_at (datetime): Дата та час створення сповіщення (успадковано).
        updated_at (datetime): Дата та час останнього оновлення (наприклад, при зміні is_read) (успадковано).

    Зв'язки:
        recipient (relationship): Зв'язок з UserModel (отримувач).
        group (relationship): Зв'язок з GroupModel (контекст групи).
        deliveries (relationship): Список спроб доставки цього сповіщення через різні канали (NotificationDeliveryModel).
    """
    __tablename__ = "notifications"

    recipient_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_notifications_recipient_id", ondelete="CASCADE"), nullable=False, index=True)
    group_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id", name="fk_notifications_group_id", ondelete="CASCADE"), nullable=True, index=True)

    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    source_entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    source_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    # Коментар для Alembic:
    # Додати в міграцію:
    # op.create_index('ix_notifications_source_entity', 'notifications', ['source_entity_type', 'source_entity_id'], unique=False)


    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)


    # --- Зв'язки (Relationships) ---
    # TODO: Узгодити back_populates="notifications_received" з UserModel
    recipient: Mapped["UserModel"] = relationship(foreign_keys=[recipient_user_id], back_populates="notifications_received")
    # TODO: Узгодити back_populates="notifications" з GroupModel
    group: Mapped[Optional["GroupModel"]] = relationship(foreign_keys=[group_id], back_populates="notifications")

    deliveries: Mapped[List["NotificationDeliveryModel"]] = relationship(back_populates="notification", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_notifications_source_entity', 'source_entity_type', 'source_entity_id'),
    )


    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі NotificationModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', user_id='{self.recipient_user_id}', type='{self.notification_type_code}', is_read='{self.is_read}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "Нотифікації - внутрішні в додатку" - ця модель для зберігання таких сповіщень.
# - "коли користувач позначає, що він виконав завдання ... адміну групи приходить сповіщення"
# - "коли адміністратор групи підтверджує/відхиляє ... користувачу приходить сповіщення"
# - "користувачу приходять сповіщення про всі рухи по рахунку"
# - "користувачу приходять сповіщення коли закінчується строк завдання"
#   - Усі ці сценарії будуть генерувати записи в цій таблиці з відповідними `notification_type_code`,
#     `recipient_user_id`, `source_entity_type`, `source_entity_id`.

# TODO: Узгодити назву таблиці `notifications` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля: `recipient_user_id`, `body`, `notification_type_code`.
# Додаткові поля: `group_id`, `title`, `source_entity_type`, `source_entity_id`, `is_read`, `read_at`, `metadata`.
# `ondelete="CASCADE"` для `recipient_user_id` та `group_id`.
# Зв'язки визначені, включаючи `NotificationDeliveryModel` для відстеження доставки.
# `JSONB` для `metadata` для гнучкості.
# Все виглядає логічно.
# Ця таблиця зберігає саме сповіщення, які бачить користувач.
# `NotificationTemplateModel` буде зберігати шаблони для генерації `title` та `body`.
# `NotificationDeliveryModel` буде відстежувати спроби доставки через різні канали (email, push).
# `is_read` та `read_at` важливі для UI.
# `source_entity_type` та `source_entity_id` дозволяють зв'язати сповіщення з об'єктом,
# який його спричинив, для можливості переходу або отримання деталей.
# `metadata` може містити, наприклад, URL для навігації або параметри для побудови сповіщення на клієнті.
# `group_id` вказує на контекст групи, якщо сповіщення стосується подій у групі.
# `updated_at` буде оновлюватися при зміні `is_read`.
# `created_at` - час створення сповіщення.
# Поле `title` може бути опціональним, якщо тип сповіщення не передбачає заголовка.
# Поле `body` - основний вміст.
# `notification_type_code` - важливий для класифікації та можливої кастомної обробки/іконок на клієнті.
