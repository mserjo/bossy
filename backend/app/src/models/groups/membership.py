# backend/app/src/models/groups/membership.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для сутності "Членство в Групі" (GroupMembership).

Цей модуль визначає модель `GroupMembership`, яка представляє зв'язок
багато-до-багатьох між користувачами (`User`) та групами (`Group`).
Вона також зберігає роль користувача в конкретній групі.
"""
from datetime import datetime  # Необхідно для TYPE_CHECKING
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів та Enum
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # Для відстеження часу приєднання
from backend.app.src.core.dicts import GroupRole  # Enum для ролей в групі
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.groups.group import Group


class GroupMembership(Base, TimestampedMixin):
    """
    Модель членства користувача в групі.

    Ця модель реалізує зв'язок багато-до-багатьох між користувачами та групами,
    дозволяючи користувачам бути членами кількох груп з різними ролями в кожній.
    Поле `created_at` з `TimestampedMixin` може використовуватися як час приєднання до групи.

    Атрибути:
        user_id (Mapped[int]): ID користувача (частина складеного первинного ключа, зовнішній ключ до `users.id`).
        group_id (Mapped[int]): ID групи (частина складеного первинного ключа, зовнішній ключ до `groups.id`).
        role (Mapped[str]): Роль користувача в цій групі (наприклад, "admin", "member").
                            Значення беруться з `GroupRole` Enum.
        user (Mapped["User"]): Зв'язок з моделлю `User`.
        group (Mapped["Group"]): Зв'язок з моделлю `Group`.
        created_at, updated_at: Часові мітки (успадковано). `created_at` позначає час приєднання.
    """
    __tablename__ = "group_memberships"

    # Складений первинний ключ (user_id, group_id)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', name='fk_group_membership_user_id', ondelete="CASCADE"),
        primary_key=True,
        comment="ID користувача, що є членом групи"
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey('groups.id', name='fk_group_membership_group_id', ondelete="CASCADE"),
        primary_key=True,
        comment="ID групи, до якої належить користувач"
    )

    # Роль користувача в групі
    # TODO: Розглянути використання SQLEnum(GroupRole) для поля 'role' для кращої цілісності на рівні БД.
    role: Mapped[str] = mapped_column(
        String(50),  # Довжина відповідає можливим значенням з GroupRole
        nullable=False,
        default=GroupRole.MEMBER.value,  # Роль за замовчуванням - "учасник"
        comment="Роль користувача в цій групі (напр., admin, member)"
    )

    # Обмеження унікальності для пари user_id та group_id, щоб користувач не міг бути
    # членом однієї групи двічі (хоча це вже забезпечується складеним первинним ключем).
    # Явне визначення `UniqueConstraint` тут може бути зайвим, якщо `primary_key=True`
    # вже встановлено для обох колонок, оскільки це автоматично створює унікальний індекс.
    # Однак, для ясності та можливості надання імені обмеженню, його можна залишити.
    # __table_args__ = (
    #     UniqueConstraint('user_id', 'group_id', name='uq_user_group_membership'),
    # )
    # Примітка: SQLAlchemy автоматично створює індекс для первинних ключів.
    # Якщо user_id та group_id є складеним первинним ключем, вони вже унікальні разом.

    # --- Зв'язки (Relationships) ---
    user: Mapped["User"] = relationship(back_populates="memberships", lazy="selectin")
    group: Mapped["Group"] = relationship(back_populates="memberships", lazy="selectin")

    # Поля для __repr__
    # `created_at`, `updated_at` успадковуються з TimestampedMixin._repr_fields
    _repr_fields = ["user_id", "group_id", "role"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі GroupMembership.
    logger.info("--- Модель Членства в Групі (GroupMembership) ---")
    logger.info(f"Назва таблиці: {GroupMembership.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = ['user_id', 'group_id', 'role', 'created_at', 'updated_at']
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['user', 'group']
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    # У реальному коді це робиться через сесію SQLAlchemy.

    # Для демонстрації __repr__ потрібні фіктивні User та Group, якщо __repr__ їх використовує.
    # Наш __repr__ з Base використовує лише mapped_column поля.

    example_membership = GroupMembership(
        user_id=101,
        group_id=202,
        role=GroupRole.ADMIN.value  # Використання значення Enum
    )
    # Імітуємо часові мітки
    example_membership.created_at = datetime.now(tz=timezone.utc)
    example_membership.updated_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра GroupMembership (без сесії):\n  {example_membership}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <GroupMembership(user_id=101, group_id=202, role='admin', created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
