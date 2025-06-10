# backend/app/src/models/tasks/completion.py
"""
Модель SQLAlchemy для сутності "Виконання Завдання" (TaskCompletion).

Цей модуль визначає модель `TaskCompletion`, яка фіксує спроби та факти
виконання завдань користувачами, включаючи час виконання, статус перевірки
та нотатки користувача.
"""
from datetime import datetime, timezone  # timezone для __main__
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Text, func  # func для server_default в TimestampedMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютні імпорти базових класів та Enum
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # `created_at` як час спроби/подання
from backend.app.src.core.dicts import TaskStatus  # Для статусу виконання

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.tasks.task import Task


class TaskCompletion(Base, TimestampedMixin):
    """
    Модель виконання завдання.

    Зберігає інформацію про те, коли користувач виконав завдання, хто перевірив
    виконання, та статус цього виконання. `created_at` з `TimestampedMixin`
    може використовуватися як час, коли користувач позначив завдання як виконане (спроба).

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису про виконання.
        task_id (Mapped[int]): ID завдання, що виконується.
        user_id (Mapped[int]): ID користувача, який виконав завдання.
        completed_at (Mapped[Optional[datetime]]): Фактичний час завершення завдання користувачем.
                                                  Може відрізнятися від `created_at`, якщо `created_at`
                                                  використовується як час подання на перевірку.
        verified_at (Mapped[Optional[datetime]]): Час перевірки виконання адміністратором.
        verifier_id (Mapped[Optional[int]]): ID користувача (адміністратора), який перевірив виконання.
        status (Mapped[str]): Статус виконання (наприклад, "pending_review", "completed", "rejected").
                              Використовує значення з `core.dicts.TaskStatus`.
        notes (Mapped[Optional[str]]): Нотатки користувача щодо виконання завдання.

        task (Mapped["Task"]): Зв'язок з моделлю `Task`.
        user (Mapped["User"]): Зв'язок з користувачем, який виконав завдання.
        verifier (Mapped[Optional["User"]]): Зв'язок з користувачем, який перевірив завдання.
        created_at, updated_at: Успадковано. `created_at` - час подання на перевірку.
    """
    __tablename__ = "task_completions"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор запису про виконання"
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey('tasks.id', name='fk_task_completion_task_id', ondelete="CASCADE"),
        nullable=False,
        comment="ID завдання, що було виконано"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', name='fk_task_completion_user_id', ondelete="CASCADE"),
        # Якщо користувач видаляється, його виконання теж
        nullable=False,
        comment="ID користувача, який виконав завдання"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        # Час, коли користувач фактично позначив завдання як зроблене
        nullable=True, comment="Фактичний час завершення завдання користувачем"
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, comment="Час перевірки та затвердження/відхилення виконання"
    )
    verifier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('users.id', name='fk_task_completion_verifier_id', ondelete="SET NULL"),
        # Якщо верифікатор видалений, запис залишається
        nullable=True,
        comment="ID адміністратора, який перевірив виконання"
    )

    # Використовуємо значення з Enum TaskStatus
    # TODO: Переконатися, що SQLEnum імпортовано та використовується, якщо тип колонки в БД є Enum.
    #       Або ж зберігати як рядок і валідувати на рівні логіки/схем Pydantic.
    # status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING_REVIEW, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default=TaskStatus.PENDING_REVIEW.value,
        nullable=False,
        index=True,
        comment="Статус виконання завдання (pending_review, completed, rejected)"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Нотатки користувача щодо виконання"
    )

    # --- Зв'язки (Relationships) ---
    task: Mapped["Task"] = relationship(back_populates="completions", lazy="selectin")
    user: Mapped["User"] = relationship(foreign_keys=[user_id],
                                        lazy="selectin")  # back_populates="task_completions" можна додати до User
    verifier: Mapped[Optional["User"]] = relationship(foreign_keys=[verifier_id],
                                                      lazy="selectin")  # back_populates="verified_completions" можна додати до User

    # Поля для __repr__
    _repr_fields = ["id", "task_id", "user_id", "status", "completed_at", "verified_at"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі TaskCompletion.
    print("--- Модель Виконання Завдання (TaskCompletion) ---")
    print(f"Назва таблиці: {TaskCompletion.__tablename__}")

    print("\nОчікувані поля:")
    expected_fields = [
        'id', 'task_id', 'user_id', 'completed_at', 'verified_at',
        'verifier_id', 'status', 'notes', 'created_at', 'updated_at'
    ]
    for field in expected_fields:
        print(f"  - {field}")

    print("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['task', 'user', 'verifier']
    for rel in expected_relationships:
        print(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    from datetime import timedelta

    example_completion = TaskCompletion(
        id=1,
        task_id=1,
        user_id=101,
        completed_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Користувач виконав годину тому
        status=TaskStatus.PENDING_REVIEW.value  # Очікує на перевірку
    )
    # Імітуємо часові мітки (created_at - час подання)
    example_completion.created_at = datetime.now(timezone.utc)
    example_completion.updated_at = datetime.now(timezone.utc)

    print(f"\nПриклад екземпляра TaskCompletion (без сесії):\n  {example_completion}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <TaskCompletion(id=1, task_id=1, user_id=101, status='pending_review', completed_at=..., created_at=...)>

    print("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
    print(
        f"Використовується TaskStatus Enum для поля 'status', наприклад: TaskStatus.COMPLETED = '{TaskStatus.COMPLETED.value}'")
