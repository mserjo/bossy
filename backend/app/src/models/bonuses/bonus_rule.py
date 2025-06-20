# backend/app/src/models/bonuses/bonus_rule.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для сутності "Правило Нарахування Бонусів" (BonusRule).

Цей модуль визначає модель `BonusRule`, яка описує умови та розміри
нарахування або списання бонусів за виконання завдань, участь у подіях
або інші дії в системі Kudos.
"""
from datetime import datetime  # Необхідно для TYPE_CHECKING
from typing import TYPE_CHECKING, Optional
from decimal import Decimal

from sqlalchemy import String, ForeignKey, Text, Numeric, func  # func для server_default в TimestampedMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Абсолютний імпорт базових класів та міксинів
from backend.app.src.models.base import Base  # Правила можуть не мати всіх полів BaseMainModel
from backend.app.src.models.mixins import (
    TimestampedMixin,
    NameDescriptionMixin,  # Правило може мати назву та опис
    StateMixin  # Для активації/деактивації правила
)

# Попереднє оголошення типів для уникнення циклічних імпортів
if TYPE_CHECKING:
    from backend.app.src.models.tasks.task import Task
    from backend.app.src.models.tasks.event import Event
    from backend.app.src.models.dictionaries.bonus_types import BonusType


class BonusRule(Base, TimestampedMixin, NameDescriptionMixin, StateMixin):
    """
    Модель Правила Нарахування Бонусів.

    Зберігає інформацію про правила, за якими нараховуються або списуються бонуси.
    Правило може бути пов'язане з конкретним завданням/подією або бути загальним.
    Поле `state` з `StateMixin` може використовуватися для позначення активності правила.
    Поля `name` та `description` з `NameDescriptionMixin` описують правило.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор правила.
        task_id (Mapped[Optional[int]]): ID завдання, до якого застосовується правило (якщо є).
        event_id (Mapped[Optional[int]]): ID події, до якої застосовується правило (якщо є).
        bonus_type_id (Mapped[int]): ID типу бонусу (наприклад, "нагорода", "штраф") з довідника `dict_bonus_types`.
        amount (Mapped[Decimal]): Розмір бонусу/штрафу.
        condition_description (Mapped[Optional[str]]): Текстовий опис умови, за якої спрацьовує правило.

        task (Mapped[Optional["Task"]]): Зв'язок з завданням.
        event (Mapped[Optional["Event"]]): Зв'язок з подією.
        bonus_type (Mapped["BonusType"]): Зв'язок з типом бонусу.
        created_at, updated_at: Успадковано.
        name, description: Успадковано.
        state: Успадковано (для статусу правила, наприклад, "active", "inactive").
    """
    __tablename__ = "bonus_rules"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор правила нарахування бонусів"
    )

    # Зв'язок із завданням або подією (події також є завданнями з відповідним типом)
    task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('tasks.id', name='fk_bonus_rule_task_id', ondelete="SET NULL"),
        # Якщо завдання видалено, правило може залишитися (або CASCADE)
        nullable=True,
        index=True,
        comment="ID завдання, до якого застосовується правило (якщо є)"
    )
    # Поле event_id тепер посилається на таблицю 'events', що розрізняє Події від Завдань.
    # Попереднє TODO щодо цього питання було вирішено.
    event_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('events.id', name='fk_bonus_rule_event_id', ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID події, до якої застосовується правило (якщо є, FK до events.id)"
    )

    bonus_type_id: Mapped[int] = mapped_column(
        ForeignKey('dict_bonus_types.id', name='fk_bonus_rule_bonus_type_id', ondelete='RESTRICT'),
        nullable=False,
        comment="ID типу бонусу з довідника dict_bonus_types"
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False,
        comment="Сума бонусу або штрафу (позитивна для нагороди, може бути негативна для штрафу або визначатися типом)"
    )
    condition_description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Опис умови, за якої спрацьовує правило (наприклад, 'за кожні 5 виконаних завдань')"
    )
    # Поле state (is_active) успадковане з StateMixin

    # --- Зв'язки (Relationships) ---
    task: Mapped[Optional["Task"]] = relationship(foreign_keys=[task_id], back_populates="bonus_rules", lazy="selectin")
    event: Mapped[Optional["Event"]] = relationship(foreign_keys=[event_id], lazy="selectin")

    bonus_type: Mapped["BonusType"] = relationship(foreign_keys=[bonus_type_id], lazy="selectin")

    # _repr_fields збираються з Base та міксинів (name, state_id, created_at, updated_at).
    # `id` автоматично додається через Base.__repr__.
    # Додаємо специфічні для BonusRule поля.
    _repr_fields = ("task_id", "event_id", "bonus_type_id", "amount")


if __name__ == "__main__":
    # Демонстраційний блок для моделі BonusRule.
    logger.info("--- Модель Правила Нарахування Бонусів (BonusRule) ---")
    logger.info(f"Назва таблиці: {BonusRule.__tablename__}")

    logger.info("\nОчікувані поля (успадковані та власні):")
    expected_fields = [
        'id', 'name', 'description', 'state', 'created_at', 'updated_at',
        # З Base, NameDescriptionMixin, StateMixin, TimestampedMixin
        'task_id', 'event_id', 'bonus_type_id', 'amount', 'condition_description'
    ]
    # SoftDeleteMixin не додано до BonusRule за замовчуванням, але може бути доданий за потреби.
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['task', 'event', 'bonus_type']
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_rule = BonusRule(
        id=1,
        name="Бонус за перше завдання",
        description="Одноразовий бонус за виконання першого завдання в системі.",
        task_id=None,  # Може бути загальним правилом, не прив'язаним до конкретного завдання
        bonus_type_id=1,  # Припустимо, ID типу "Нагорода"
        amount=Decimal("50.00"),
        condition_description="Виконання будь-якого першого завдання новим користувачем.",
        state="active"
    )
    example_rule.created_at = datetime.now(tz=timezone.utc)  # Імітація

    logger.info(f"\nПриклад екземпляра BonusRule (без сесії):\n  {example_rule}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <BonusRule(id=1, name='Бонус за перше завдання', state='active', amount=Decimal('50.00'), bonus_type_id=1, created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
