# backend/app/src/models/tasks/task.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `TaskModel` для представлення завдань та подій в системі.
Завдання/події належать до певної групи, мають тип, можуть мати виконавців, терміни, бонуси/штрафи.
"""
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer, Numeric, Interval, \
    CheckConstraint  # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column  # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime, timedelta  # Для роботи з датами та часом

# Використовуємо BaseMainModel, оскільки завдання/подія має назву, опис, статус, належить до групи.
from backend.app.src.models.base import BaseMainModel

if TYPE_CHECKING:
    from backend.app.src.models.dictionaries.task_type import TaskTypeModel
    from backend.app.src.models.auth.user import UserModel
    from backend.app.src.models.teams.team import TeamModel
    from backend.app.src.models.tasks.assignment import TaskAssignmentModel
    from backend.app.src.models.tasks.completion import TaskCompletionModel
    from backend.app.src.models.tasks.review import TaskReviewModel
    from backend.app.src.models.tasks.dependency import TaskDependencyModel
    from backend.app.src.models.tasks.proposal import TaskProposalModel
    # GroupModel та StatusModel вже є в BaseMainModel


class TaskModel(BaseMainModel):
    """
    Модель для представлення завдань та подій.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор завдання/події (успадковано).
        name (str): Назва завдання/події (успадковано).
        description (str | None): Детальний опис (успадковано).
        state_id (uuid.UUID | None): Статус завдання/події (наприклад, "нове", "в роботі", "виконано", "скасовано").
                                     Посилається на StatusModel. (успадковано)
        group_id (uuid.UUID): Ідентифікатор групи, до якої належить завдання/подія. (успадковано, тут буде NOT NULL)

        task_type_id (uuid.UUID): Ідентифікатор типу завдання/події (з довідника TaskTypeModel).
        created_by_user_id (uuid.UUID): Ідентифікатор користувача (адміна групи), який створив завдання/подію.

        # Параметри бонусів/штрафів
        bonus_points (Numeric | None): Кількість бонусних балів за виконання.
        penalty_points (Numeric | None): Кількість штрафних балів за невиконання або прострочення.

        # Параметри виконання
        due_date (datetime | None): Термін виконання завдання.
        is_recurring (bool): Чи є завдання/подія постійним (повторюваним).
        recurring_interval (Interval | None): Інтервал повторення, якщо is_recurring=True (наприклад, щодня, щотижня).
        max_occurrences (int | None): Максимальна кількість повторень (якщо is_recurring).

        is_mandatory (bool): Чи є завдання обов'язковим для виконання.

        # Параметри для кількох виконавців
        allow_multiple_assignees (bool): Чи може завдання мати декількох виконавців одночасно.
        first_completes_gets_bonus (bool): Чи тільки перший виконавець отримує бонус (якщо allow_multiple_assignees=True).
                                          Якщо False, то всі, хто виконав, отримують бонус.

        # Ієрархія завдань
        parent_task_id (uuid.UUID | None): Ідентифікатор батьківського завдання (для підзадач).

        # Командні завдання
        team_id (uuid.UUID | None): Ідентифікатор команди, якій призначено завдання (якщо це командне завдання).
                                    Посилається на TeamModel.
        # Додаткові бонуси
        streak_bonus_enabled (bool): Чи ввімкнено бонус за послідовне виконання.
        streak_bonus_task_id (uuid.UUID | None): Посилання на завдання, за послідовне виконання якого дається бонус (може бути це ж завдання).
        streak_bonus_count (int | None): Кількість послідовних виконань для отримання бонусу.
        streak_bonus_points (Numeric | None): Розмір додаткового бонусу за серію.

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення (успадковано).
        is_deleted (bool): Прапорець "м'якого" видалення (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Зв'язки:
        group (relationship): Зв'язок з GroupModel.
        task_type (relationship): Зв'язок з TaskTypeModel.
        creator (relationship): Зв'язок з UserModel (хто створив).
        parent_task (relationship): Зв'язок з батьківським завданням.
        child_tasks (relationship): Список підзадач.
        assignments (relationship): Список призначень цього завдання (TaskAssignmentModel).
        completions (relationship): Список виконань цього завдання (TaskCompletionModel).
        reviews (relationship): Відгуки на це завдання (TaskReviewModel).
        team (relationship): Команда, якій призначено завдання.
        # TODO: Додати інші зв'язки:
        # - status (StatusModel) - вже є через state_id.
        # - dependencies (TaskDependencyModel) - залежності від інших завдань.
    """
    __tablename__ = "tasks"

    # group_id успадковано і має бути NOT NULL.

    task_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("task_types.id", name="fk_tasks_task_type_id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_tasks_creator_id", ondelete="SET NULL"), nullable=False, index=True) # Завдання може існувати, якщо автор видалений

    # --- Параметри бонусів/штрафів ---
    bonus_points: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    penalty_points: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # --- Параметри виконання ---
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    recurring_interval: Mapped[Optional[timedelta]] = mapped_column(Interval, nullable=True)
    max_occurrences: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Параметри для кількох виконавців ---
    allow_multiple_assignees: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    first_completes_gets_bonus: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Ієрархія завдань ---
    parent_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", name="fk_tasks_parent_task_id", ondelete="CASCADE"), nullable=True, index=True) # Якщо батьківське видаляється, дочірні теж

    # --- Командні завдання ---
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id", name="fk_tasks_team_id", ondelete="SET NULL"), nullable=True, index=True) # Якщо команда видаляється, завдання може стати індивідуальним або без виконавця

    # --- Додаткові бонуси за серію ---
    streak_bonus_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    streak_bonus_ref_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", name="fk_tasks_streak_bonus_ref_task_id", ondelete="SET NULL"), nullable=True)
    streak_bonus_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    streak_bonus_points: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # --- Зв'язки (Relationships) ---
    # group: Mapped["GroupModel"] - успадковано з BaseMainModel

    task_type: Mapped["TaskTypeModel"] = relationship(foreign_keys=[task_type_id], back_populates="tasks_of_this_type", lazy="selectin")
    creator: Mapped["UserModel"] = relationship(foreign_keys=[created_by_user_id], back_populates="created_tasks", lazy="selectin")

    parent_task: Mapped[Optional["TaskModel"]] = relationship(remote_side="TaskModel.id", back_populates="child_tasks", lazy="selectin")
    child_tasks: Mapped[List["TaskModel"]] = relationship(back_populates="parent_task", cascade="all, delete-orphan", lazy="select")

    assignments: Mapped[List["TaskAssignmentModel"]] = relationship(back_populates="task", cascade="all, delete-orphan", lazy="select")
    completions: Mapped[List["TaskCompletionModel"]] = relationship(back_populates="task", cascade="all, delete-orphan", lazy="select")
    reviews: Mapped[List["TaskReviewModel"]] = relationship(back_populates="task", cascade="all, delete-orphan", lazy="select")

    team: Mapped[Optional["TeamModel"]] = relationship(foreign_keys=[team_id], back_populates="tasks_assigned", lazy="selectin")

    streak_bonus_reference_task: Mapped[Optional["TaskModel"]] = relationship(remote_side="TaskModel.id", foreign_keys=[streak_bonus_ref_task_id], lazy="selectin")

    # state: Mapped[Optional["StatusModel"]] - успадковано з BaseMainModel

    dependent_tasks: Mapped[List["TaskDependencyModel"]] = relationship(
        foreign_keys="[TaskDependencyModel.prerequisite_task_id]",
        back_populates="prerequisite_task",
        cascade="all, delete-orphan",
        lazy="select"
    )
    prerequisite_links: Mapped[List["TaskDependencyModel"]] = relationship(
        foreign_keys="[TaskDependencyModel.dependent_task_id]",
        back_populates="dependent_task",
        cascade="all, delete-orphan",
        lazy="select"
    )

    # Зв'язок з TaskProposalModel (якщо це завдання створено з пропозиції)
    # Потрібно додати source_proposal_id в TaskModel, якщо зв'язок один-до-одного з боку TaskModel
    # Або в TaskProposalModel є created_task_id
    # Поточна TaskProposalModel.created_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("tasks.id"))
    # Отже, зворотний зв'язок:
    source_proposal: Mapped[Optional["TaskProposalModel"]] = relationship(back_populates="created_task", lazy="selectin")


    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі TaskModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', group_id='{self.group_id}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "завдання чи подія" - визначається через `task_type_id` (TaskTypeModel може мати прапорець is_event).
# - "скільки бонусів за виконання; який штраф за невиконання" - `bonus_points`, `penalty_points`.
# - "одноразове чи постійне" - `is_recurring`, `recurring_interval`, `max_occurrences`.
# - "з терміном виконання або без" - `due_date`.
# - "обов'язкове для виконання або ні" - `is_mandatory`.
# - "може брати у виконання тільки один користувач ... або багато" - `allow_multiple_assignees`.
# - "бонуси за виконання отримує тільки перший ... або усі" - `first_completes_gets_bonus`.
# - "завдання/події можуть бути ієрархічними" - `parent_task_id`.
# - "завдання можуть бути \"обов'язковими\" (адмін групи може назначити виконавців)" - `is_mandatory` та логіка призначення.
# - "завдання можуть бути командними" - `team_id`.
# - "додаткові бонуси за послідовне виконання" - `streak_bonus_enabled` та пов'язані поля.

# TODO: Узгодити назву таблиці `tasks` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseMainModel` як основи. `group_id` має бути NOT NULL.
# Всі ключові поля з ТЗ додані.
# Зв'язки визначені.
# `cascade="all, delete-orphan"` для залежних сутностей (assignments, completions, reviews, child_tasks, dependencies).
# `Numeric(10, 2)` для балів. `Interval` для `recurring_interval`.
# Все виглядає досить повно.
# Зв'язок `group` уточнено з `foreign_keys="TaskModel.group_id"`.
# Зв'язки для залежностей (`TaskDependencyModel`) додані.
# `streak_bonus_ref_task_id` посилається на `tasks.id`.
# Поле `name` з `BaseMainModel` - назва завдання/події.
# `description`, `state_id`, `notes`, `deleted_at`, `is_deleted` - успадковані.
# `group_id` - успадковане, але тут має бути обов'язковим.
# Це буде контролюватися на рівні логіки або валідації при створенні завдання.
# Або можна перевизначити `group_id` тут як `nullable=False`.
# Поки що залишаю як є, покладаючись на логіку сервісу.
# `lazy="joined"` для `parent_task` може бути корисним.
# Для `child_tasks` та інших списків за замовчуванням `lazy="select"`.

    __table_args__ = (
        CheckConstraint('group_id IS NOT NULL', name='ck_task_group_id_not_null'),
    )