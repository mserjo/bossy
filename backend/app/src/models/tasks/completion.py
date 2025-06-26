# backend/app/src/models/tasks/completion.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `TaskCompletionModel`.
Ця модель фіксує факт та деталі виконання завдання (`TaskModel`)
конкретним користувачем (`UserModel`) або командою. Вона також відстежує
статус перевірки та підтвердження виконання.
"""
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, ForeignKey, DateTime, Text, UniqueConstraint, Numeric, LargeBinary # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column  # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

class TaskCompletionModel(BaseModel):
    """
    Модель для фіксації виконання завдань.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запису про виконання (успадковано).
        task_id (uuid.UUID): Ідентифікатор завдання, яке виконується/виконано.
        user_id (uuid.UUID | None): Ідентифікатор користувача, який виконав завдання.
                                     NULL, якщо завдання виконано командою як єдиним цілим,
                                     або якщо це подія, що не має конкретного виконавця.
        team_id (uuid.UUID | None): Ідентифікатор команди, яка виконала завдання.
                                     (Якщо бонуси розподіляються між членами команди,
                                     то кожен член може мати свій запис про виконання,
                                     або ж тут фіксується виконання командою, а бонуси розподіляються окремо).

        # Статуси процесу виконання/перевірки
        status_id (uuid.UUID): Статус виконання (наприклад, "в роботі", "на перевірці", "підтверджено", "відхилено", "скасовано").
                               Посилається на StatusModel.

        started_at (datetime | None): Час, коли користувач взяв завдання в роботу.
        submitted_for_review_at (datetime | None): Час, коли користувач позначив завдання як "виконано" (надіслав на перевірку).
        completed_at (datetime | None): Час, коли виконання було підтверджено адміном (або час фактичного завершення).

        # Результати перевірки
        reviewed_by_user_id (uuid.UUID | None): Ідентифікатор адміна, який перевірив виконання.
        reviewed_at (datetime | None): Час перевірки.
        review_notes (Text | None): Коментарі адміна щодо перевірки (наприклад, причина відхилення).

        # Нараховані бонуси/штрафи за це конкретне виконання
        bonus_points_awarded (Numeric | None): Фактично нараховані бонусні бали.
        penalty_points_applied (Numeric | None): Фактично застосовані штрафні бали.

        # Додаткова інформація від виконавця
        completion_notes (Text | None): Коментарі виконавця щодо виконання.
        attachments (JSONB | None): Список посилань на файли або метадані файлів,
                                    доданих як доказ виконання (якщо потрібно).

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення (успадковано).

    Зв'язки:
        task (relationship): Зв'язок з TaskModel.
        user (relationship): Зв'язок з UserModel (виконавець).
        team (relationship): Зв'язок з TeamModel (команда-виконавець).
        status (relationship): Зв'язок зі StatusModel.
        reviewer (relationship): Зв'язок з UserModel (хто перевірив).
    """
    __tablename__ = "task_completions"

    task_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Виконавець - або користувач, або команда.
    user_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_task_completions_user_id", ondelete="CASCADE"), nullable=True, index=True)
    team_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("teams.id", name="fk_task_completions_team_id", ondelete="CASCADE"), nullable=True, index=True)
    # TODO: Додати CHECK constraint, щоб user_id або team_id були заповнені, якщо це не автоматична подія.
    # Для подій, які не мають виконавця, обидва можуть бути NULL.

    # Статус виконання завдання
    status_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("statuses.id", name="fk_task_completions_status_id", ondelete="RESTRICT"), nullable=False, index=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_for_review_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_task_completions_reviewer_id", ondelete="SET NULL"), nullable=True, index=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    bonus_points_awarded: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    penalty_points_applied: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    completion_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachments: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB, nullable=True) # JSONB для списку словників


    # --- Зв'язки (Relationships) ---
    task: Mapped["TaskModel"] = relationship(back_populates="completions")
    # TODO: Узгодити back_populates="task_completions" з UserModel
    user: Mapped[Optional["UserModel"]] = relationship(foreign_keys=[user_id], back_populates="task_completions")
    # TODO: Узгодити back_populates="task_completions" з TeamModel
    team: Mapped[Optional["TeamModel"]] = relationship(foreign_keys=[team_id], back_populates="task_completions") # Припускаючи, що в TeamModel є task_completions
    status: Mapped["StatusModel"] = relationship(foreign_keys=[status_id], back_populates="task_completions_with_this_status")
    # TODO: Узгодити back_populates="reviewed_task_completions" з UserModel
    reviewer: Mapped[Optional["UserModel"]] = relationship(foreign_keys=[reviewed_by_user_id], back_populates="reviewed_task_completions")

    # Обмеження унікальності:
    # Зазвичай, один користувач може мати один "активний" запис про виконання для одного завдання.
    # (наприклад, не може взяти в роботу завдання, яке вже в роботі у нього).
    # Або, якщо завдання можна виконувати багато разів (повторювані або постійні),
    # то для кожного "екземпляра" виконання буде окремий запис.
    # Якщо TaskModel.is_recurring = False (одноразове):
    #   - (task_id, user_id) має бути унікальним, якщо завдання призначене користувачу.
    #   - (task_id, team_id) має бути унікальним, якщо завдання призначене команді.
    # Якщо TaskModel.is_recurring = True:
    #   - Потрібен додатковий ідентифікатор екземпляра повторення (наприклад, дата або номер),
    #     щоб дозволити кілька записів TaskCompletionModel для одного (task_id, user_id).
    #     Або ж, TaskCompletionModel завжди створюється новий, і логіка контролює, чи можна створити новий.
    # Поки що, для простоти, припускаємо, що комбінація (task_id, user_id) або (task_id, team_id)
    # може бути не унікальною, якщо завдання дозволяє багаторазове виконання.
    # Унікальність контролюється на рівні логіки "взяття в роботу".
    # Якщо завдання може бути виконане лише один раз одним користувачем, то:
    # UniqueConstraint('task_id', 'user_id', name='uq_task_user_completion', postgresql_where=(user_id.isnot(None))),
    # UniqueConstraint('task_id', 'team_id', name='uq_task_team_completion', postgresql_where=(team_id.isnot(None))),
    # Але це завадить повторному виконанню.
    # Тому, унікальні обмеження тут можуть бути недоречними без додаткового контексту (наприклад, "occurrence_date").
    # Залишаємо без жорстких унікальних обмежень на комбінації, покладаючись на логіку сервісу.

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі TaskCompletionModel.
        """
        executor_info = f"user_id='{self.user_id}'" if self.user_id else (f"team_id='{self.team_id}'" if self.team_id else "event")
        return f"<{self.__class__.__name__}(task_id='{self.task_id}', {executor_info}, status_id='{self.status_id}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "користувач ставить статус "в роботі" (дія "взяти у роботу" в завданні)" - `started_at`, `status_id`.
# - "користувач ставить статус "перевірка" (дія "виконано" в завданні)" - `submitted_for_review_at`, `status_id`.
# - "користувач ставить статус "скасовано" (дія "відмовитися" в завданні)" - `status_id`.
# - "(адмін групи) адмін перевіряє і ставить статус "підтверджено" / "відхилено" / "заблоковано""
#   - `reviewed_by_user_id`, `reviewed_at`, `review_notes`, `status_id`.
# - "за виконані командні завдання бонуси отримують усі учасники команди в рівних долях"
#   - Якщо `team_id` заповнено, логіка нарахування бонусів розподіляє їх.
#   - Або для кожного члена команди створюється окремий запис `TaskCompletionModel`.
#     Це залежить від реалізації. Поточна модель дозволяє обидва підходи.

# TODO: Узгодити назву таблиці `task_completions` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля: `task_id`, `user_id` (nullable), `team_id` (nullable), `status_id`.
# Поля для відстеження часу: `started_at`, `submitted_for_review_at`, `completed_at`, `reviewed_at`.
# Поля для результатів перевірки та нарахованих бонусів.
# `JSONB` для `attachments`.
# `ondelete="CASCADE"` для `task_id`, `user_id`, `team_id`.
# `ondelete="SET NULL"` для `reviewed_by_user_id`.
# Зв'язки визначені.
# Унікальні обмеження поки що не додані через складність логіки повторних виконань.
# Все виглядає логічно.
# Якщо `user_id` і `team_id` обидва `NULL`, це може означати автоматичне виконання "події" без конкретного виконавця.
# Або ж, для подій записи в `TaskCompletionModel` можуть не створюватися, а їх "виконання"
# (настання події) обробляється іншим механізмом (наприклад, cron-задачею, що створює транзакції).
# Поки що модель гнучка і дозволяє це.
# Поле `attachments` для завантаження файлів-доказів.
# Поля `bonus_points_awarded` та `penalty_points_applied` для фіксації фактичних сум,
# які можуть відрізнятися від планових в `TaskModel` (наприклад, часткове виконання).
