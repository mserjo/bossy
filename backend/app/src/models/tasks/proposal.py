# backend/app/src/models/tasks/proposal.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `TaskProposalModel`.
Ця модель дозволяє користувачам пропонувати нові завдання або події на розгляд
адміністратору групи. Адміністратор може на основі пропозиції створити
реальне завдання/подію та, за бажанням, нарахувати бонуси за вдалу пропозицію.
"""
from typing import Optional, Dict, Any

from sqlalchemy import Column, ForeignKey, DateTime, Text, String, Boolean  # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column  # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

# Використовуємо BaseMainModel, оскільки пропозиція має назву (заголовок), опис, статус,
# і належить до групи (неявно, через запропоноване завдання для групи).
# Однак, пропозиція сама по собі може не мати всіх атрибутів BaseMainModel.
# Спробуємо з BaseModel і додамо потрібні поля.
from backend.app.src.models.base import BaseModel

class TaskProposalModel(BaseModel):
    """
    Модель для пропозицій завдань/подій від користувачів.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор пропозиції (успадковано).
        group_id (uuid.UUID): Ідентифікатор групи, для якої робиться пропозиція.
        proposed_by_user_id (uuid.UUID): Ідентифікатор користувача, який зробив пропозицію.

        title (str): Заголовок або коротка назва запропонованого завдання/події.
        description (Text): Детальний опис пропозиції.
        proposed_task_type_code (str | None): Запропонований код типу завдання/події (з TaskTypeModel.code).
        proposed_bonus_points (Numeric | None): Запропонована кількість бонусів.
        proposed_penalty_points (Numeric | None): Запропонована кількість штрафів.
        proposed_due_date (datetime | None): Запропонований термін виконання.
        # ... інші поля, що відповідають атрибутам TaskModel, які користувач може запропонувати

        status_id (uuid.UUID): Статус пропозиції (наприклад, "на розгляді", "прийнято", "відхилено").
                               Посилається на StatusModel.
        admin_review_notes (Text | None): Коментарі адміністратора щодо розгляду пропозиції.
        reviewed_by_user_id (uuid.UUID | None): Ідентифікатор адміна, який розглянув пропозицію.
        reviewed_at (datetime | None): Час розгляду пропозиції.

        created_task_id (uuid.UUID | None): Ідентифікатор завдання/події, створеного на основі цієї пропозиції.
                                            Посилається на TaskModel.
        bonus_for_proposal_awarded (bool): Чи були нараховані бонуси за вдалу пропозицію.

        created_at (datetime): Дата та час створення пропозиції (успадковано).
        updated_at (datetime): Дата та час останнього оновлення (успадковано).
    """
    __tablename__ = "task_proposals"

    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    proposed_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_task_proposals_proposer_id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    proposed_task_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    status_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("statuses.id", name="fk_task_proposals_status_id", ondelete="RESTRICT"), nullable=False, index=True)

    admin_review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_task_proposals_reviewer_id", ondelete="SET NULL"), nullable=True, index=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", name="fk_task_proposals_created_task_id", ondelete="SET NULL"), nullable=True, index=True, unique=True)

    bonus_for_proposal_awarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


    # --- Зв'язки (Relationships) ---
    # TODO: Узгодити back_populates з GroupModel
    group: Mapped["GroupModel"] = relationship(foreign_keys=[group_id], back_populates="task_proposals")
    # TODO: Узгодити back_populates="task_proposals_made" з UserModel
    proposer: Mapped["UserModel"] = relationship(foreign_keys=[proposed_by_user_id], back_populates="task_proposals_made")
    status: Mapped["StatusModel"] = relationship(foreign_keys=[status_id], back_populates="task_proposals_with_this_status")
    # TODO: Узгодити back_populates="task_proposals_reviewed" з UserModel
    reviewer: Mapped[Optional["UserModel"]] = relationship(foreign_keys=[reviewed_by_user_id], back_populates="task_proposals_reviewed")
    # TODO: Узгодити back_populates="source_proposal" з TaskModel
    created_task: Mapped[Optional["TaskModel"]] = relationship(foreign_keys=[created_task_id], back_populates="source_proposal")

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі TaskProposalModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', title='{self.title}', group_id='{self.group_id}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "користувач може створити пропозицію завдання/події та відправити на розгляд адміна групи" - ця модель.
# - "на основі цієї пропозиції адмін групи може створити завдання/подію" - поле `created_task_id`.
# - "і за бажанням нарахувати бонуси за вдалу пропозицію" - поле `bonus_for_proposal_awarded`.
# - "(ця можливість налаштовується адміном в групі)" - налаштування `task_proposals_enabled` в `GroupSettingsModel`.

# TODO: Узгодити назву таблиці `task_proposals` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля: `group_id`, `proposed_by_user_id`, `title`, `description`, `status_id`.
# `proposed_task_details` (JSONB) для зберігання запропонованих атрибутів завдання.
# Поля для процесу розгляду: `admin_review_notes`, `reviewed_by_user_id`, `reviewed_at`.
# Посилання на створене завдання `created_task_id`.
# `ondelete="CASCADE"` для `group_id` та `proposed_by_user_id`.
# `ondelete="SET NULL"` для `reviewed_by_user_id` та `created_task_id`.
# Зв'язки визначені.
# Все виглядає логічно.
# Статуси для пропозицій можуть бути: "pending_review", "approved", "rejected", "implemented".
# `bonus_for_proposal_awarded` - простий прапорець, фактичне нарахування бонусів - окрема транзакція.
# `created_task_id` є `unique=True`, що логічно, оскільки одне завдання не може бути результатом двох різних пропозицій.
# Або, якщо одна пропозиція може породити кілька завдань, то цей зв'язок має бути один-до-багатьох з боку TaskModel,
# або `created_task_id` не буде унікальним. Поки що залишаємо `unique=True`.
# Якщо одна пропозиція може породити кілька завдань, то `created_task_id` тут не підходить,
# і зв'язок має бути реалізований полем `source_proposal_id` в `TaskModel`.
# Поки що припускаємо, що одна пропозиція -> одне завдання (або жодного).
# Тому `created_task_id` з `unique=True` тут є коректним.
