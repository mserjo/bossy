# backend/app/src/models/groups/invitation.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для сутності "Запрошення до Групи" (GroupInvitation).

Цей модуль визначає модель `GroupInvitation`, яка використовується для зберігання
інформації про запрошення користувачів до груп, включаючи унікальний код запрошення,
термін його дії, роль, що призначається, та статус запрошення.
"""
from datetime import datetime, timezone, timedelta  # timedelta для прикладу в __main__
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, func  # func для server_default в TimestampedMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів та Enum
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin
from backend.app.src.core.dicts import GroupRole, InvitationStatus  # Оновлені Enum
from sqlalchemy import Enum as SQLEnum # Імпорт SQLEnum
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.groups.group import Group


class GroupInvitation(Base, TimestampedMixin):
    """
    Модель запрошення до групи.

    Зберігає деталі запрошень, надісланих користувачам для приєднання до групи.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запрошення.
        group_id (Mapped[int]): ID групи, до якої надсилається запрошення.
        email (Mapped[Optional[str]]): Email адреса запрошеного користувача (якщо запрошення по email).
        phone_number (Mapped[Optional[str]]): Номер телефону запрошеного (якщо запрошення по SMS).
        invitation_code (Mapped[str]): Унікальний код запрошення.
        role_to_assign (Mapped[str]): Роль, яка буде призначена користувачу при прийнятті запрошення.
        expires_at (Mapped[datetime]): Дата та час закінчення терміну дії запрошення.
        created_by_user_id (Mapped[Optional[int]]): ID користувача, який створив запрошення.
        status (Mapped[str]): Поточний статус запрошення (наприклад, "pending", "accepted", "expired").

        group (Mapped["Group"]): Зв'язок з моделлю `Group`.
        created_by (Mapped[Optional["User"]]): Зв'язок з моделлю `User` (автор запрошення).
        created_at, updated_at: Успадковано від `TimestampedMixin`.
    """
    __tablename__ = "group_invitations"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор запрошення"
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey('groups.id', name='fk_group_invitation_group_id', ondelete="CASCADE"),
        nullable=False,
        comment="ID групи, до якої створено запрошення"
    )
    # Запрошення може бути на email АБО телефон, або просто кодом
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="Email запрошеного користувача (якщо є)"
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, index=True, comment="Номер телефону запрошеного (якщо є)"
    )
    invitation_code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False, comment="Унікальний код запрошення"
    )
    role_to_assign: Mapped[GroupRole] = mapped_column(
        SQLEnum(GroupRole), default=GroupRole.MEMBER, nullable=False, comment="Роль, що буде призначена при прийнятті"
    )
    expires_at: Mapped[datetime] = mapped_column(
        nullable=False, comment="Час закінчення терміну дії запрошення"
    )
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('users.id', name='fk_group_invitation_creator_id', ondelete="SET NULL"),
        nullable=True,  # Може бути NULL, якщо запрошення системне або автор видалений
        comment="ID користувача, який створив запрошення"
    )
    status: Mapped[InvitationStatus] = mapped_column(
        SQLEnum(InvitationStatus), default=InvitationStatus.PENDING, nullable=False, index=True,
        comment="Статус запрошення (pending, accepted, expired тощо)"
    )

    # --- Зв'язки (Relationships) ---
    group: Mapped["Group"] = relationship(back_populates="invitations", lazy="selectin")
    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_user_id],
                                                        lazy="selectin")  # Немає back_populates, якщо User не має invitations_created

    # Поля для __repr__
    # `id` автоматично додається через Base.__repr__
    # `created_at`, `updated_at` успадковуються з TimestampedMixin._repr_fields
    _repr_fields = ("group_id", "invitation_code", "status", "expires_at")


if __name__ == "__main__":
    # Демонстраційний блок для моделі GroupInvitation.
    logger.info("--- Модель Запрошення до Групи (GroupInvitation) ---")
    logger.info(f"Назва таблиці: {GroupInvitation.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = [
        'id', 'group_id', 'email', 'phone_number', 'invitation_code',
        'role_to_assign', 'expires_at', 'created_by_user_id', 'status',
        'created_at', 'updated_at'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['group', 'created_by']
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_invitation = GroupInvitation(
        id=1,
        group_id=202,
        email="new.user@example.com",
        invitation_code="UNIQUECODE123",
        role_to_assign=GroupRole.MEMBER, # Використання Enum
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_by_user_id=101,
        status=InvitationStatus.PENDING  # Використання Enum
    )
    # Імітуємо часові мітки
    example_invitation.created_at = datetime.now(timezone.utc)
    example_invitation.updated_at = datetime.now(timezone.utc)

    logger.info(f"\nПриклад екземпляра GroupInvitation (без сесії):\n  {example_invitation}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <GroupInvitation(id=1, group_id=202, invitation_code='UNIQUECODE123', status=<InvitationStatus.PENDING: 'pending'>, expires_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
