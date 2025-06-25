# backend/app/src/models/tasks/assignment.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `TaskAssignmentModel`.
Ця модель представляє призначення завдання (`TaskModel`) конкретному користувачеві (`UserModel`)
або команді (`TeamModel`). Вона фіксує, хто є виконавцем завдання.
"""

from sqlalchemy import Column, ForeignKey, DateTime, Text, UniqueConstraint # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

class TaskAssignmentModel(BaseModel):
    """
    Модель для призначення завдань виконавцям (користувачам або командам).

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор призначення (успадковано).
        task_id (uuid.UUID): Ідентифікатор завдання, яке призначається.
        user_id (uuid.UUID | None): Ідентифікатор користувача-виконавця.
                                     NULL, якщо завдання призначено команді.
        team_id (uuid.UUID | None): Ідентифікатор команди-виконавця.
                                     NULL, якщо завдання призначено окремому користувачеві.
        assigned_by_user_id (uuid.UUID | None): Ідентифікатор користувача (адміна), який зробив призначення.
        assigned_at (datetime): Час призначення (може бути `created_at`).
        status_id (uuid.UUID | None): Статус цього конкретного призначення (наприклад, "прийнято в роботу", "відхилено виконавцем").
                                      Посилається на StatusModel.
        notes (str | None): Нотатки щодо цього призначення.

        created_at (datetime): Дата та час створення запису (успадковано, відповідає `assigned_at`).
        updated_at (datetime): Дата та час останнього оновлення (успадковано).

    Зв'язки:
        task (relationship): Зв'язок з TaskModel.
        user (relationship): Зв'язок з UserModel (виконавець).
        team (relationship): Зв'язок з TeamModel (команда-виконавець).
        assigner (relationship): Зв'язок з UserModel (хто призначив).
        status (relationship): Зв'язок зі StatusModel.
    """
    __tablename__ = "task_assignments"

    task_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Виконавець - або користувач, або команда. Одне з цих полів має бути заповнене.
    user_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_task_assignments_user_id", ondelete="CASCADE"), nullable=True, index=True)
    team_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("teams.id", name="fk_task_assignments_team_id", ondelete="CASCADE"), nullable=True, index=True)
    # TODO: Додати CHECK constraint, щоб гарантувати, що або user_id, або team_id заповнене, але не обидва одночасно.
    # Або ж це контролюється логікою.

    # Хто призначив завдання. Може бути NULL, якщо завдання "відкрите для всіх" або автоматично призначене.
    assigned_by_user_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_task_assignments_assigner_id", ondelete="SET NULL"), nullable=True, index=True)

    # `created_at` з BaseModel може слугувати як `assigned_at`.

    # Статус конкретного призначення. Наприклад, якщо користувач взяв завдання в роботу.
    # TODO: Замінити "statuses.id" на константу або імпорт моделі StatusModel.
    status_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("statuses.id", name="fk_task_assignments_status_id"), nullable=True, index=True)

    notes: Column[str | None] = Column(Text, nullable=True)


    # --- Зв'язки (Relationships) ---
    task = relationship("TaskModel", back_populates="assignments")
    user = relationship("UserModel", foreign_keys=[user_id]) # back_populates="task_assignments" буде в UserModel
    team = relationship("TeamModel", foreign_keys=[team_id]) # back_populates="task_assignments" буде в TeamModel
    assigner = relationship("UserModel", foreign_keys=[assigned_by_user_id]) # back_populates="made_task_assignments" буде в UserModel
    status = relationship("StatusModel", foreign_keys=[status_id]) # back_populates="task_assignment_statuses" буде в StatusModel

    # Обмеження унікальності:
    # Одне завдання не може бути призначене одному й тому ж користувачеві двічі.
    # Одне завдання не може бути призначене одній і тій же команді двічі.
    # TODO: Подумати над більш складними обмеженнями, якщо `user_id` та `team_id` взаємовиключні.
    # Поки що, якщо обидва NULL, це може означати "відкрите для взяття" завдання, але це краще реалізувати інакше.
    # Це таблиця саме призначень.
    __table_args__ = (
        UniqueConstraint('task_id', 'user_id', name='uq_task_user_assignment', postgresql_where=(user_id.isnot(None))),
        UniqueConstraint('task_id', 'team_id', name='uq_task_team_assignment', postgresql_where=(team_id.isnot(None))),
        # CheckConstraint(
        #     or_(user_id.isnot(None), team_id.isnot(None)),
        #     name='cc_task_assignment_assignee_present'
        # ),
        # CheckConstraint(
        #     not_(and_(user_id.isnot(None), team_id.isnot(None))),
        #     name='cc_task_assignment_assignee_exclusive'
        # )
        # TODO: Check constraints краще додавати через міграції Alembic, оскільки SQLAlchemy ORM може мати обмеження
        # з ними, особливо з `postgresql_where` в UniqueConstraint.
    )

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі TaskAssignmentModel.
        """
        assignee_info = f"user_id='{self.user_id}'" if self.user_id else f"team_id='{self.team_id}'"
        return f"<{self.__class__.__name__}(task_id='{self.task_id}', {assignee_info})>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "завдання можуть бути \"обов'язковими\" (адмін групи може назначити виконавців)" - ця модель для призначення.
# - "може брати у виконання тільки один користувач (хто перший взяв у виконання), або багато користувачів одночасно"
#   - Ця логіка більше стосується `TaskModel.allow_multiple_assignees` та процесу взяття в роботу (`TaskCompletionModel`).
#   - `TaskAssignmentModel` фіксує, кому *призначено*. Якщо завдання "відкрите", то запис сюди може
#     створюватися, коли користувач "бере в роботу".

# TODO: Узгодити назву таблиці `task_assignments` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля: `task_id`, `user_id` (nullable), `team_id` (nullable).
# `ondelete="CASCADE"` для `task_id`, `user_id`, `team_id` (видалення призначення при видаленні завдання/користувача/команди).
# `ondelete="SET NULL"` для `assigned_by_user_id` (якщо адмін, що призначив, видаляється, призначення залишається).
# Додаткові поля `status_id`, `notes`.
# Зв'язки визначені.
# Унікальні обмеження для запобігання дублюючих призначень.
# CHECK constraints для взаємовиключності `user_id` та `team_id` та наявності хоча б одного з них
# є хорошою ідеєю для цілісності даних, але їх реалізація через SQLAlchemy може бути складною;
# краще робити це на рівні БД через міграції. Поки що покладаємося на логіку сервісу.
# Або ж, якщо завдання завжди призначається або користувачу, або команді, то можна зробити два окремих поля
# і логічно контролювати, яке з них заповнене. Поточний підхід з двома nullable ForeignKey є гнучким.
# `postgresql_where` в `UniqueConstraint` корисний для умовних обмежень.
# Все виглядає логічно.
