# backend/app/src/models/tasks/review.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `TaskReviewModel`.
Ця модель дозволяє користувачам залишати відгуки та ставити рейтинги
на завдання або події в групі. Ця можливість налаштовується адміністратором групи.
"""
from typing import Optional

from sqlalchemy import Column, ForeignKey, DateTime, Text, Integer, UniqueConstraint # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column  # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

class TaskReviewModel(BaseModel):
    """
    Модель для відгуків та рейтингів на завдання/події.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор відгуку (успадковано).
        task_id (uuid.UUID): Ідентифікатор завдання/події, до якого залишено відгук.
        user_id (uuid.UUID): Ідентифікатор користувача, який залишив відгук.
        rating (int | None): Рейтинг, виставлений користувачем (наприклад, від 1 до 5).
                             NULL, якщо залишено лише текстовий відгук.
        comment (Text | None): Текстовий коментар відгуку.

        # Статус відгуку (якщо потрібна модерація відгуків)
        # status_id (uuid.UUID | None): Статус відгуку (наприклад, "опубліковано", "на модерації", "відхилено").
        #                               Посилається на StatusModel.

        created_at (datetime): Дата та час створення відгуку (успадковано).
        updated_at (datetime): Дата та час останнього оновлення (успадковано, якщо відгуки можна редагувати).

    Зв'язки:
        task (relationship): Зв'язок з TaskModel.
        user (relationship): Зв'язок з UserModel.
        # status (relationship): Зв'язок зі StatusModel (якщо є модерація).
    """
    __tablename__ = "task_reviews"

    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_task_reviews_user_id", ondelete="CASCADE"), nullable=False, index=True)

    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Коментар для Alembic:
    # Додати в міграцію:
    # op.create_check_constraint('ck_task_review_rating_range', 'task_reviews', '(rating >= 1 AND rating <= 5) OR rating IS NULL')

    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # status_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("statuses.id", ondelete="SET NULL"), nullable=True, index=True) # Якщо буде модерація

    # --- Зв'язки (Relationships) ---
    task: Mapped["TaskModel"] = relationship(back_populates="reviews")
    # TODO: Узгодити back_populates="task_reviews_left" з UserModel
    user: Mapped["UserModel"] = relationship(foreign_keys=[user_id], back_populates="task_reviews_left")
    # status: Mapped[Optional["StatusModel"]] = relationship(foreign_keys=[status_id], back_populates="task_reviews_with_this_status") # Якщо буде модерація

    # Обмеження унікальності: один користувач може залишити лише один відгук на одне завдання.
    __table_args__ = (
        UniqueConstraint('task_id', 'user_id', name='uq_task_user_review'),
    )

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі TaskReviewModel.
        """
        return f"<{self.__class__.__name__}(task_id='{self.task_id}', user_id='{self.user_id}', rating='{self.rating}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "(всі ролі в рамках групи) можна залишати відгуки на завдання/події та ставити рейтинги
#   (ця можливість налаштовується адміном в групі)" - ця модель для відгуків/рейтингів.
#   Налаштування (`task_reviews_enabled`) знаходиться в `GroupSettingsModel`.

# TODO: Узгодити назву таблиці `task_reviews` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля: `task_id`, `user_id`.
# Додаткові поля: `rating`, `comment`.
# Можливість модерації через `status_id` (поки що закоментовано).
# `ondelete="CASCADE"` для `task_id` та `user_id`.
# `UniqueConstraint` для `(task_id, user_id)`.
# Зв'язки визначені.
# Все виглядає логічно.
# `rating` може бути `nullable`, якщо дозволено залишати лише текстовий коментар.
# CHECK constraint для діапазону `rating` (наприклад, 1-5) краще додати на рівні БД через міграцію.
# Якщо відгуки можна редагувати, то `updated_at` буде корисним.
# Якщо відгуки анонімні (не планується згідно ТЗ), то `user_id` буде `nullable`.
# Поточна реалізація передбачає неанонімні відгуки.
