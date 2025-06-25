# backend/app/src/models/tasks/task.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `TaskModel` для представлення завдань та подій в системі.
Завдання/події належать до певної групи, мають тип, можуть мати виконавців, терміни, бонуси/штрафи.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer, Numeric, Interval # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

# Використовуємо BaseMainModel, оскільки завдання/подія має назву, опис, статус, належить до групи.
from backend.app.src.models.base import BaseMainModel

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
    # ForeignKey("groups.id") вже є в BaseMainModel.

    # Тип завдання/події
    # TODO: Замінити "task_types.id" на константу або імпорт моделі TaskTypeModel.
    task_type_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("task_types.id", name="fk_tasks_task_type_id"), nullable=False, index=True)

    # Хто створив завдання/подію
    # TODO: Замінити "users.id" на константу або імпорт моделі UserModel.
    created_by_user_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_tasks_creator_id"), nullable=False, index=True)

    # --- Параметри бонусів/штрафів ---
    bonus_points: Column[Numeric | None] = Column(Numeric(10, 2), nullable=True)
    penalty_points: Column[Numeric | None] = Column(Numeric(10, 2), nullable=True) # Може бути від'ємним або додатнім, що віднімається

    # --- Параметри виконання ---
    due_date: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True, index=True)
    is_recurring: Column[bool] = Column(Boolean, default=False, nullable=False, index=True)
    recurring_interval: Column[Interval | None] = Column(Interval, nullable=True) # Наприклад, timedelta(days=1)
    max_occurrences: Column[int | None] = Column(Integer, nullable=True) # Для обмеження кількості повторень

    is_mandatory: Column[bool] = Column(Boolean, default=False, nullable=False)

    # --- Параметри для кількох виконавців ---
    allow_multiple_assignees: Column[bool] = Column(Boolean, default=False, nullable=False)
    # Якщо True, бонус отримує перший, хто виконав. Якщо False, бонус отримують усі, хто виконав.
    # Застосовується, якщо allow_multiple_assignees = True.
    first_completes_gets_bonus: Column[bool] = Column(Boolean, default=True, nullable=False)

    # --- Ієрархія завдань ---
    parent_task_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("tasks.id", name="fk_tasks_parent_task_id"), nullable=True, index=True)

    # --- Командні завдання ---
    # TODO: Замінити "teams.id" на константу або імпорт моделі TeamModel.
    team_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("teams.id", name="fk_tasks_team_id"), nullable=True, index=True)

    # --- Додаткові бонуси за серію ---
    streak_bonus_enabled: Column[bool] = Column(Boolean, default=False, nullable=False)
    # Посилання на завдання, за послідовне виконання якого дається бонус.
    # Може посилатися на себе ж (this task) або на інше завдання.
    # Якщо NULL, то мається на увазі це ж завдання.
    streak_bonus_ref_task_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("tasks.id", name="fk_tasks_streak_bonus_ref_task_id"), nullable=True)
    streak_bonus_count: Column[int | None] = Column(Integer, nullable=True) # Наприклад, 5 разів поспіль
    streak_bonus_points: Column[Numeric | None] = Column(Numeric(10, 2), nullable=True)

    # --- Зв'язки (Relationships) ---
    # group успадковано з BaseMainModel, якщо там є relationship.
    # group = relationship("GroupModel", foreign_keys=[group_id], back_populates="tasks")
    # Потрібно переконатися, що foreign_keys=[group_id] не конфліктує, якщо group_id є в BaseMainModel.
    # Оскільки group_id в BaseMainModel вже є ForeignKey, можна просто:
    group = relationship("GroupModel", foreign_keys="TaskModel.group_id", back_populates="tasks")


    task_type = relationship("TaskTypeModel", foreign_keys=[task_type_id]) # back_populates="tasks" буде в TaskTypeModel
    creator = relationship("UserModel", foreign_keys=[created_by_user_id]) # back_populates="created_tasks" буде в UserModel

    parent_task = relationship("TaskModel", remote_side=[id], back_populates="child_tasks", lazy="joined")
    child_tasks = relationship("TaskModel", back_populates="parent_task", cascade="all, delete-orphan") # lazy="joined" можна додати

    assignments = relationship("TaskAssignmentModel", back_populates="task", cascade="all, delete-orphan")
    completions = relationship("TaskCompletionModel", back_populates="task", cascade="all, delete-orphan")
    reviews = relationship("TaskReviewModel", back_populates="task", cascade="all, delete-orphan")

    team = relationship("TeamModel", foreign_keys=[team_id]) # back_populates="tasks" буде в TeamModel

    # Зв'язок для streak_bonus_ref_task_id
    streak_bonus_reference_task = relationship("TaskModel", remote_side=[id], foreign_keys=[streak_bonus_ref_task_id])

    # Зв'язок зі статусом (успадкований з BaseMainModel, якщо там визначено relationship `state`)
    # state = relationship("StatusModel", foreign_keys=[state_id])

    # Залежності (зв'язок "багато-до-багатьох" через TaskDependencyModel)
    # `dependent_tasks` - завдання, які залежать від цього завдання (це завдання є передумовою для них)
    dependent_tasks = relationship(
        "TaskDependencyModel",
        foreign_keys="[TaskDependencyModel.prerequisite_task_id]",
        back_populates="prerequisite_task",
        cascade="all, delete-orphan"
    )
    # `prerequisite_tasks` - завдання, від яких залежить це завдання (вони є передумовами для цього завдання)
    prerequisite_links = relationship(
        "TaskDependencyModel",
        foreign_keys="[TaskDependencyModel.dependent_task_id]",
        back_populates="dependent_task",
        cascade="all, delete-orphan"
    )


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
