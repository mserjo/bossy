# backend/app/src/models/groups/group.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для сутності "Група".

Цей модуль визначає модель `Group`, яка представляє групи користувачів у системі Kudos.
Групи є основним контейнером для завдань, бонусів, нагород та членства користувачів.
"""
from datetime import datetime  # Необхідно для TYPE_CHECKING, якщо datetime використовується в типах
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, ForeignKey, Text  # Text може знадобитися для description з міксину
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Абсолютний імпорт базових класів та міксинів
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import (
    TimestampedMixin,
    SoftDeleteMixin,
    NameDescriptionMixin,
    StateMixin,
    NotesMixin
)

# Попереднє оголошення типів для уникнення циклічних імпортів
if TYPE_CHECKING:
    from backend.app.src.models.dictionaries.group_types import GroupType
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.groups.membership import GroupMembership
    from backend.app.src.models.groups.settings import GroupSetting
    from backend.app.src.models.groups.invitation import GroupInvitation
    from backend.app.src.models.tasks.task import Task  # Модель завдання
    from backend.app.src.models.bonuses.reward import Reward  # Модель нагороди


class Group(
    Base,
    TimestampedMixin,
    SoftDeleteMixin,
    NameDescriptionMixin,
    StateMixin,
    NotesMixin
    # GroupAffiliationMixin тут не потрібен, оскільки група не належить іншій групі
):
    """
    Модель Групи.

    Успадковує основні поля (ID, назва, опис, стан, нотатки, часові мітки, м'яке видалення)
    та додає специфічні для групи поля, такі як тип групи та власник.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор групи (успадковано неявно через Base, але тут визначено явно).
        name (Mapped[str]): Назва групи (успадковано).
        description (Mapped[Optional[str]]): Опис групи (успадковано).
        state (Mapped[Optional[str]]): Стан групи (успадковано).
        notes (Mapped[Optional[str]]): Нотатки до групи (успадковано).
        created_at, updated_at: Часові мітки (успадковано).
        deleted_at: Для м'якого видалення (успадковано).

        group_type_id (Mapped[int]): ID типу групи з довідника `dict_group_types`.
        owner_id (Mapped[Optional[int]]): ID користувача-власника групи.

        group_type (Mapped["GroupType"]): Зв'язок з моделлю `GroupType`.
        owner (Mapped[Optional["User"]]): Зв'язок з моделлю `User` (власник).
        memberships (Mapped[List["GroupMembership"]]): Членство в цій групі.
        settings (Mapped[Optional["GroupSetting"]]): Налаштування цієї групи.
        invitations (Mapped[List["GroupInvitation"]]): Запрошення до цієї групи.
        tasks (Mapped[List["Task"]]): Завдання, що належать цій групі.
        rewards (Mapped[List["Reward"]]): Нагороди, доступні в цій групі.
    """
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор групи"
    )

    # --- Специфічні поля для групи ---
    group_type_id: Mapped[int] = mapped_column(
        ForeignKey('dict_group_types.id', name='fk_group_group_type_id', ondelete='RESTRICT'),
        # RESTRICT, щоб не видалити тип, якщо є групи
        nullable=False,
        comment="ID типу групи з довідника dict_group_types"
    )
    owner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('users.id', name='fk_group_owner_id', ondelete='SET NULL'),
        # Якщо власника видалено, група може залишитися без власника або перейти іншому
        nullable=True,  # Може бути системна група без власника, або власник ще не призначений
        index=True,
        comment="ID користувача, який є власником або створив групу"
    )

    # --- Зв'язки (Relationships) ---
    group_type: Mapped["GroupType"] = relationship(foreign_keys=[group_type_id], lazy="selectin")
    owner: Mapped[Optional["User"]] = relationship(foreign_keys=[owner_id],
                                                   lazy="selectin")  # Немає back_populates, якщо User.owned_groups не визначено

    memberships: Mapped[List["GroupMembership"]] = relationship(
        back_populates="group", cascade="all, delete-orphan", lazy="selectin"
    )
    settings: Mapped[Optional["GroupSetting"]] = relationship(
        back_populates="group", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )
    invitations: Mapped[List["GroupInvitation"]] = relationship(
        back_populates="group", cascade="all, delete-orphan", lazy="selectin"
    )
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="group", cascade="all, delete-orphan", lazy="selectin"
    )
    rewards: Mapped[List["Reward"]] = relationship(
        back_populates="group", cascade="all, delete-orphan", lazy="selectin"
    )

    # _repr_fields збираються з Base та міксинів (name, state_id, created_at, updated_at, deleted_at, is_deleted, notes).
    # `id` автоматично обробляється Base.__repr__.
    # Додаємо специфічні для Group поля, які важливі для __repr__.
    _repr_fields = ("owner_id", "group_type_id")


if __name__ == "__main__":
    # Демонстраційний блок для моделі Group.
    logger.info("--- Модель Групи (Group) ---")
    logger.info(f"Назва таблиці: {Group.__tablename__}")

    logger.info("\nОчікувані поля (успадковані та власні):")
    expected_fields = [
        'id', 'name', 'description', 'state', 'notes',
        'created_at', 'updated_at', 'deleted_at',
        'group_type_id', 'owner_id'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['group_type', 'owner', 'memberships', 'settings', 'invitations', 'tasks', 'rewards']
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    # У реальному коді це робиться через сесію SQLAlchemy.
    example_group = Group(
        id=1,
        name="Моя перша група",
        description="Тестова група для демонстрації Kudos.",
        group_type_id=1,  # Припустимо, ID типу "Сім'я"
        owner_id=101,  # Припустимо, ID користувача-власника
        state="active"
    )
    example_group.created_at = datetime.now(tz=timezone.utc)  # Імітація

    logger.info(f"\nПриклад екземпляра Group (без сесії):\n  {example_group}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <Group(id=1, name='Моя перша група', state='active', owner_id=101, group_type_id=1, created_at=...)>

    logger.info(
        "\nПримітка: Для повноцінної роботи з моделлю та її зв'язками потрібна сесія SQLAlchemy та підключення до БД.")
