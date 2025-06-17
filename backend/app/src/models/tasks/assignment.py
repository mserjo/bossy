# backend/app/src/models/tasks/assignment.py
"""
Модель SQLAlchemy для сутності "Призначення Завдання" (TaskAssignment).

Цей модуль визначає модель `TaskAssignment`, яка представляє зв'язок
багато-до-багатьох між завданнями (`Task`) та користувачами (`User`),
показуючи, якому користувачеві призначено яке завдання.
"""
from datetime import datetime  # Необхідно для TYPE_CHECKING
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютні імпорти базових класів та Enum
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # Для відстеження часу призначення
from backend.app.src.config.logging import get_logger
from backend.app.src.core.dicts import TaskAssignmentStatus # Імпорт Enum
from sqlalchemy import Enum as SQLEnum # Імпорт SQLEnum
logger = get_logger(__name__)


if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.tasks.task import Task


class TaskAssignment(Base, TimestampedMixin):
    """
    Модель призначення завдання користувачеві.

    Ця модель реалізує зв'язок багато-до-багатьох між завданнями та користувачами.
    Поле `created_at` з `TimestampedMixin` може використовуватися як час призначення завдання.

    Атрибути:
        task_id (Mapped[int]): ID завдання (частина складеного первинного ключа, зовнішній ключ до `tasks.id`).
        user_id (Mapped[int]): ID користувача (частина складеного первинного ключа, зовнішній ключ до `users.id`).
        status (Mapped[Optional[TaskAssignmentStatus]]): Статус цього конкретного призначення (використовує Enum `TaskAssignmentStatus`).
        task (Mapped["Task"]): Зв'язок з моделлю `Task`.
        user (Mapped["User"]): Зв'язок з моделлю `User`.
        created_at, updated_at: Часові мітки (успадковано). `created_at` позначає час призначення.
    """
    __tablename__ = "task_assignments"

    # Складений первинний ключ
    task_id: Mapped[int] = mapped_column(
        ForeignKey('tasks.id', name='fk_task_assignment_task_id', ondelete="CASCADE"),
        primary_key=True,
        comment="ID завдання, яке призначено"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', name='fk_task_assignment_user_id', ondelete="CASCADE"),
        primary_key=True,
        comment="ID користувача, якому призначено завдання"
    )

    # Статус призначення (може бути корисним, якщо відрізняється від загального статусу завдання)
    status: Mapped[Optional[TaskAssignmentStatus]] = mapped_column(
        SQLEnum(TaskAssignmentStatus), nullable=True, index=True, comment="Статус призначення (напр., assigned, accepted, declined)"
    )

    # Обмеження унікальності для пари task_id та user_id, щоб уникнути дублювання призначень.
    # Це вже забезпечується складеним первинним ключем, але явне визначення з ім'ям може бути корисним.
    __table_args__ = (
        UniqueConstraint('task_id', 'user_id', name='uq_task_user_assignment'),
    )

    # --- Зв'язки (Relationships) ---
    task: Mapped["Task"] = relationship(back_populates="assignments", lazy="selectin")
    user: Mapped["User"] = relationship(lazy="selectin")  # back_populates="task_assignments" може бути додано до User

    # Поля для __repr__
    # Ця модель має композитний ПК (task_id, user_id), тому вони повинні бути включені.
    # `created_at`, `updated_at` успадковуються з TimestampedMixin._repr_fields.
    _repr_fields = ("task_id", "user_id", "status")


if __name__ == "__main__":
    # Демонстраційний блок для моделі TaskAssignment.
    logger.info("--- Модель Призначення Завдання (TaskAssignment) ---")
    logger.info(f"Назва таблиці: {TaskAssignment.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = ['task_id', 'user_id', 'status', 'created_at', 'updated_at']
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['task', 'user']
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_assignment = TaskAssignment(
        task_id=1,
        user_id=101,
        status=TaskAssignmentStatus.ASSIGNED  # Використання Enum
    )
    # Імітуємо часові мітки
    example_assignment.created_at = datetime.now(tz=timezone.utc)
    example_assignment.updated_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра TaskAssignment (без сесії):\n  {example_assignment}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <TaskAssignment(task_id=1, user_id=101, status=<TaskAssignmentStatus.ASSIGNED: 'assigned'>, created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
