# backend/app/src/models/tasks/assignment.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `TaskAssignmentModel`.
Ця модель представляє призначення завдання (`TaskModel`) конкретному користувачеві (`UserModel`)
або команді (`TeamModel`). Вона фіксує, хто є виконавцем завдання.
"""
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, DateTime, Text, UniqueConstraint, Index, text  # type: ignore # Додано Index, text
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column  # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

if TYPE_CHECKING:
    from backend.app.src.models.tasks.task import TaskModel
    from backend.app.src.models.auth.user import UserModel
    from backend.app.src.models.teams.team import TeamModel
    from backend.app.src.models.dictionaries.status import StatusModel


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

    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Виконавець - або користувач, або команда. Одне з цих полів має бути заповнене.
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_task_assignments_user_id", ondelete="CASCADE"), nullable=True, index=True)
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id", name="fk_task_assignments_team_id", ondelete="CASCADE"), nullable=True, index=True)

    assigned_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_task_assignments_assigner_id", ondelete="SET NULL"), nullable=True, index=True)

    status_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("statuses.id", name="fk_task_assignments_status_id", ondelete="SET NULL"), nullable=True, index=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


    # --- Зв'язки (Relationships) ---
    task: Mapped["TaskModel"] = relationship(back_populates="assignments", lazy="selectin")
    # TODO: Узгодити back_populates="task_assignments" з UserModel
    user: Mapped[Optional["UserModel"]] = relationship(foreign_keys=[user_id], back_populates="task_assignments", lazy="selectin")
    # TODO: Узгодити back_populates="task_assignments" з TeamModel
    team: Mapped[Optional["TeamModel"]] = relationship(foreign_keys=[team_id], back_populates="task_assignments", lazy="selectin") # Припускаючи, що в TeamModel є tasks_assigned, а не task_assignments
    # TODO: Узгодити back_populates="made_task_assignments" з UserModel
    assigner: Mapped[Optional["UserModel"]] = relationship(foreign_keys=[assigned_by_user_id], back_populates="made_task_assignments", lazy="selectin")
    status: Mapped[Optional["StatusModel"]] = relationship(foreign_keys=[status_id], back_populates="task_assignments_with_this_status", lazy="selectin")

    # Обмеження унікальності:
    # Одне завдання не може бути призначене одному й тому ж користувачеві двічі.
    # Одне завдання не може бути призначене одній і тій же команді двічі.
    # TODO: Подумати над більш складними обмеженнями, якщо `user_id` та `team_id` взаємовиключні.
    # Поки що, якщо обидва NULL, це може означати "відкрите для взяття" завдання, але це краще реалізувати інакше.
    # Це таблиця саме призначень.
    __table_args__ = (
        Index(
            'ix_task_user_assignment_unique',
            task_id,
            user_id,
            unique=True,
            postgresql_where=user_id.isnot(None) # type: ignore
        ),
        Index(
            'ix_task_team_assignment_unique',
            task_id,
            team_id,
            unique=True,
            postgresql_where=team_id.isnot(None) # type: ignore
        ),
        # Коментар для Alembic:
        # Додати в міграцію для забезпечення, що або user_id, або team_id заповнене, але не обидва:
        # op.create_check_constraint(
        #     'cc_task_assignment_assignee_exclusive_present',
        #     'task_assignments',
        #     "((user_id IS NOT NULL AND team_id IS NULL) OR (user_id IS NULL AND team_id IS NOT NULL))"
        # )
        # Або, якщо завдання може бути не призначене нікому (що не логічно для цієї таблиці):
        # op.create_check_constraint(
        #     'cc_task_assignment_assignee_not_both',
        #     'task_assignments',
        #     "NOT (user_id IS NOT NULL AND team_id IS NOT NULL)"
        # )
        # Поточна логіка передбачає, що призначення завжди або користувачу, або команді.
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
