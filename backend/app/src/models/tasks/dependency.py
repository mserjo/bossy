# backend/app/src/models/tasks/dependency.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `TaskDependencyModel`.
Ця модель представляє залежності між завданнями, де одне завдання
не може бути розпочате або завершене, доки не завершене інше (передумова).
Це реалізує зв'язок "багато-до-багатьох" між завданнями.
"""
from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, String, UniqueConstraint # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column  # type: ignore # Додано mapped_column
import uuid # Для роботи з UUID

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

if TYPE_CHECKING:
    from backend.app.src.models.tasks.task import TaskModel


class TaskDependencyModel(BaseModel):
    """
    Модель для визначення залежностей між завданнями.
    Представляє зв'язок, де `dependent_task` залежить від `prerequisite_task`.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор залежності (успадковано).
        dependent_task_id (uuid.UUID): Ідентифікатор завдання, яке залежить від іншого.
        prerequisite_task_id (uuid.UUID): Ідентифікатор завдання, яке є передумовою.
        dependency_type (str | None): Тип залежності (наприклад, "finish-to-start", "start-to-start").
                                      За замовчуванням "finish-to-start".

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення (успадковано).

    Зв'язки:
        dependent_task (relationship): Зв'язок з TaskModel (залежне завдання).
        prerequisite_task (relationship): Зв'язок з TaskModel (завдання-передумова).
    """
    __tablename__ = "task_dependencies"

    # Ідентифікатор завдання, яке залежить від іншого (не може початися, поки не виконано prerequisite_task_id)
    dependent_task_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Ідентифікатор завдання, яке є передумовою для dependent_task_id
    prerequisite_task_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Тип залежності. Найпоширеніший - "finish-to-start" (FS):
    # dependent_task не може початися, доки prerequisite_task не завершено.
    # Інші можливі типи: "start-to-start" (SS), "finish-to-finish" (FF), "start-to-finish" (SF).
    # TODO: Визначити Enum або довідник для типів залежностей, якщо їх буде багато.
    dependency_type: Column[str | None] = Column(String(50), default="finish-to-start", nullable=True)


    # --- Зв'язки (Relationships) ---
    dependent_task: Mapped["TaskModel"] = relationship(
        foreign_keys=[dependent_task_id],
        back_populates="prerequisite_links",
        lazy="selectin"
    )

    prerequisite_task: Mapped["TaskModel"] = relationship(
        foreign_keys=[prerequisite_task_id],
        back_populates="dependent_tasks",
        lazy="selectin"
    )

    # Обмеження унікальності: одна й та сама пара залежності не повинна існувати двічі.
    # Також, завдання не може залежати саме від себе (це контролюється логікою).
    __table_args__ = (
        UniqueConstraint('dependent_task_id', 'prerequisite_task_id', 'dependency_type', name='uq_task_dependency_pair_type'),
        # TODO: Додати CHECK constraint, щоб dependent_task_id != prerequisite_task_id.
        # CheckConstraint('dependent_task_id != prerequisite_task_id', name='cc_task_dependency_no_self_ref')
        # Це краще робити через міграції.
    )

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі TaskDependencyModel.
        """
        return f"<{self.__class__.__name__}(dependent='{self.dependent_task_id}' -> prerequisite='{self.prerequisite_task_id}')>"

# TODO: Перевірити відповідність `technical-task.md` та `structure-claude-v3.md`.
# - `technical-task.md` згадує "завдання/події можуть бути ієрархічними (одна задача може мати підзадачі)" -
#   це реалізовано через `parent_task_id` в `TaskModel`.
# - Залежності (dependencies) не згадані явно, але є логічним розширенням для складних проектів.
#   `structure-claude-v3.md` вказує `backend/app/src/models/tasks/dependency.py`.
# Назва таблиці `task_dependencies` є логічною.
# Використання `BaseModel` як основи.
# Ключові поля: `dependent_task_id`, `prerequisite_task_id`.
# Додаткове поле `dependency_type` для гнучкості.
# `ondelete="CASCADE"` для зовнішніх ключів, щоб при видаленні завдання пов'язані з ним залежності також видалялися.
# Зв'язки визначені з правильними `back_populates`.
# `UniqueConstraint` для запобігання дублюючих залежностей.
# CHECK constraint для запобігання самопосилань є хорошою ідеєю.
# Все виглядає узгоджено.
# Ця модель дозволяє створювати ланцюжки завдань, де виконання одного залежить від іншого.
# Наприклад, завдання Б не може початися, доки не завершено завдання А.
# dependent_task_id = ID_завдання_Б
# prerequisite_task_id = ID_завдання_А
# dependency_type = "finish-to-start"
# В `TaskModel` зв'язки `dependent_tasks` та `prerequisite_links` дозволять легко отримувати
# ці залежності.
# `prerequisite_links` в `TaskModel` - це список об'єктів `TaskDependencyModel`, де поточне завдання є `dependent_task`.
# `dependent_tasks` в `TaskModel` - це список об'єктів `TaskDependencyModel`, де поточне завдання є `prerequisite_task`.
# Можливо, назви `back_populates` варто зробити симетричнішими, але поточні назви відображають суть.
# `prerequisite_links` - це посилання на передумови (тобто, які завдання є передумовами для поточного).
# `dependent_tasks` - це завдання, які залежать від поточного (поточне є передумовою для них).
# Це правильно.
