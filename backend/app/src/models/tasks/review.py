# backend/app/src/models/tasks/review.py
"""
Модель SQLAlchemy для сутності "Відгук на Завдання" (TaskReview).

Цей модуль визначає модель `TaskReview`, яка дозволяє користувачам
залишати відгуки (рейтинг та коментар) на виконані завдання.
"""
from datetime import datetime, timezone  # timezone для __main__
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Text, CheckConstraint, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # Для created_at, updated_at
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.tasks.task import Task


class TaskReview(Base, TimestampedMixin):
    """
    Модель відгуку на завдання.

    Зберігає рейтинг та коментар, залишений користувачем щодо конкретного завдання.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор відгуку.
        task_id (Mapped[int]): ID завдання, до якого залишено відгук.
        user_id (Mapped[int]): ID користувача, який залишив відгук.
        rating (Mapped[Optional[int]]): Числовий рейтинг (наприклад, від 1 до 5).
        comment (Mapped[Optional[str]]): Текстовий коментар відгуку.

        task (Mapped["Task"]): Зв'язок з моделлю `Task`.
        user (Mapped["User"]): Зв'язок з моделлю `User` (автор відгуку).
        created_at, updated_at: Успадковано від `TimestampedMixin`.
    """
    __tablename__ = "task_reviews"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор відгуку"
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey('tasks.id', name='fk_task_review_task_id', ondelete="CASCADE"),
        nullable=False,
        comment="ID завдання, до якого залишено відгук"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', name='fk_task_review_user_id', ondelete="CASCADE"),
        # Якщо користувач видаляється, його відгуки теж
        nullable=False,
        comment="ID користувача, який залишив відгук"
    )

    rating: Mapped[Optional[int]] = mapped_column(
        nullable=True, comment="Числовий рейтинг завдання (наприклад, 1-5)"
    )
    comment: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Текстовий коментар до відгуку"
    )

    # Обмеження таблиці
    __table_args__ = (
        CheckConstraint('rating IS NULL OR (rating >= 1 AND rating <= 5)', name='cc_task_review_rating_range'),
        UniqueConstraint('task_id', 'user_id', name='uq_task_user_review')
    # Користувач може залишити лише один відгук на завдання
    )

    # --- Зв'язки (Relationships) ---
    task: Mapped["Task"] = relationship(back_populates="reviews", lazy="selectin")
    # User relationship (автор відгуку)
    user: Mapped["User"] = relationship(foreign_keys=[user_id],
                                        lazy="selectin")  # back_populates="task_reviews" можна додати до User

    # Поля для __repr__
    _repr_fields = ["id", "task_id", "user_id", "rating"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі TaskReview.
    logger.info("--- Модель Відгуку на Завдання (TaskReview) ---")
    logger.info(f"Назва таблиці: {TaskReview.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = ['id', 'task_id', 'user_id', 'rating', 'comment', 'created_at', 'updated_at']
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['task', 'user']
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_review = TaskReview(
        id=1,
        task_id=1,
        user_id=101,
        rating=5,
        comment="Чудове завдання, було цікаво виконувати!"  # TODO i18n
    )
    # Імітуємо часові мітки
    example_review.created_at = datetime.now(tz=timezone.utc)
    example_review.updated_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра TaskReview (без сесії):\n  {example_review}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <TaskReview(id=1, task_id=1, user_id=101, rating=5, created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
