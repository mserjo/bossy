# backend/app/src/models/tasks/proposal.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `TaskProposalModel`.
Ця модель дозволяє користувачам пропонувати нові завдання або події на розгляд
адміністратору групи. Адміністратор може на основі пропозиції створити
реальне завдання/подію та, за бажанням, нарахувати бонуси за вдалу пропозицію.
"""

from sqlalchemy import Column, ForeignKey, DateTime, Text, String # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
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

    group_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    proposed_by_user_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_task_proposals_proposer_id", ondelete="CASCADE"), nullable=False, index=True)

    title: Column[str] = Column(String(255), nullable=False)
    description: Column[str] = Column(Text, nullable=False)

    # Запропоновані параметри для завдання (можна зберігати в JSON або окремими полями)
    # Використаємо JSONB для гнучкості, щоб зберігати різні запропоновані атрибути завдання.
    # Наприклад: {"task_type_code": "chore", "bonus_points": 10, "due_date": "2024-12-31T23:59:00Z"}
    proposed_task_details: Column[JSONB | None] = Column(JSONB, nullable=True)

    # Статус пропозиції
    # TODO: Замінити "statuses.id" на константу або імпорт моделі StatusModel.
    status_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("statuses.id", name="fk_task_proposals_status_id"), nullable=False, index=True)

    admin_review_notes: Column[str | None] = Column(Text, nullable=True)
    reviewed_by_user_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_task_proposals_reviewer_id", ondelete="SET NULL"), nullable=True, index=True)
    reviewed_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True)

    # Посилання на завдання, створене на основі цієї пропозиції (якщо прийнято)
    created_task_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("tasks.id", name="fk_task_proposals_created_task_id", ondelete="SET NULL"), nullable=True, index=True, unique=True)
    # `unique=True` тут означає, що одне завдання може бути створене лише з однієї пропозиції.

    bonus_for_proposal_awarded: Column[bool] = Column(Boolean, default=False, nullable=False)


    # --- Зв'язки (Relationships) ---
    group = relationship("GroupModel") # back_populates="task_proposals" буде в GroupModel
    proposer = relationship("UserModel", foreign_keys=[proposed_by_user_id]) # back_populates="task_proposals" буде в UserModel
    status = relationship("StatusModel", foreign_keys=[status_id]) # back_populates="task_proposal_statuses" буде в StatusModel
    reviewer = relationship("UserModel", foreign_keys=[reviewed_by_user_id]) # back_populates="reviewed_task_proposals" буде в UserModel
    created_task = relationship("TaskModel", foreign_keys=[created_task_id]) # back_populates="source_proposal" буде в TaskModel (якщо потрібен зворотний зв'язок)

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
