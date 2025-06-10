# backend/app/src/models/tasks/task.py
"""
Модель SQLAlchemy для сутності "Завдання" (Task).

Цей модуль визначає модель `Task`, яка представляє завдання або події в системі Kudos.
Завдання можуть бути призначені користувачам, мати терміни виконання, типи, статуси,
бали за виконання або штрафи, а також можуть бути пов'язані з групами.
Модель також підтримує рекурентні завдання та ієрархію підзавдань.
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from decimal import Decimal  # Для полів балів/штрафів

from sqlalchemy import String, ForeignKey, Text, Numeric, Boolean  # Boolean для is_recurring, is_mandatory
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базової моделі та інших необхідних типів
from backend.app.src.models.base import BaseMainModel
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# from backend.app.src.core.dicts import TaskStatus as TaskStatusEnum # Буде використовуватися для поля state

# Попереднє оголошення типів для уникнення циклічних імпортів
if TYPE_CHECKING:
    from backend.app.src.models.groups.group import Group
    from backend.app.src.models.dictionaries.task_types import TaskType
    from backend.app.src.models.dictionaries.statuses import Status  # Для поля status_id
    from backend.app.src.models.tasks.assignment import TaskAssignment
    from backend.app.src.models.tasks.completion import TaskCompletion
    from backend.app.src.models.tasks.review import TaskReview
    from backend.app.src.models.bonuses.bonus_rule import BonusRule  # Модель правил нарахування бонусів


class Task(BaseMainModel):
    """
    Модель Завдання/Події.

    Успадковує `BaseMainModel` (id, name, description, state, group_id, notes, timestamps, soft_delete).
    Поле `state` з `BaseMainModel` може використовуватися для основного статусу завдання,
    або ж можна використовувати `status_id` для більш детального зв'язку з довідником статусів.

    Атрибути:
        task_type_id (Mapped[int]): ID типу завдання з довідника `dict_task_types`.
        status_id (Mapped[Optional[int]]): ID статусу завдання з довідника `dict_statuses`.
                                           TODO: Узгодити використання з успадкованим полем `state`.
        due_date (Mapped[Optional[datetime]]): Термін виконання завдання.
        is_recurring (Mapped[bool]): Чи є завдання рекурентним.
        recurrence_pattern (Mapped[Optional[str]]): Шаблон рекурентності (наприклад, cron-вираз або RRULE).
        is_mandatory (Mapped[bool]): Чи є завдання обов'язковим для виконання.
        parent_task_id (Mapped[Optional[int]]): ID батьківського завдання для ієрархії.
        points_reward (Mapped[Optional[Decimal]]): Кількість балів за успішне виконання (пряме нарахування).
        penalty_amount (Mapped[Optional[Decimal]]): Сума штрафу за невиконання (пряме нарахування).

        event_start_time (Mapped[Optional[datetime]]): Час початку події (якщо завдання є подією).
        event_end_time (Mapped[Optional[datetime]]): Час закінчення події (якщо завдання є подією).
        event_location (Mapped[Optional[str]]): Місце проведення події.

        # Зв'язки (Relationships)
        group (Mapped["Group"]): Група, до якої належить завдання.
        task_type (Mapped["TaskType"]): Тип завдання.
        status (Mapped[Optional["Status"]]): Статус завдання (з довідника).
        parent_task (Mapped[Optional["Task"]]): Батьківське завдання.
        sub_tasks (Mapped[List["Task"]]): Список підзавдань.
        assignments (Mapped[List["TaskAssignment"]]): Призначення завдання користувачам.
        completions (Mapped[List["TaskCompletion"]]): Записи про виконання завдання.
        reviews (Mapped[List["TaskReview"]]): Відгуки на завдання.
        bonus_rules (Mapped[List["BonusRule"]]): Правила нарахування бонусів, пов'язані з цим завданням.
    """
    __tablename__ = "tasks"

    # --- Специфічні поля для Завдання/Події ---
    task_type_id: Mapped[int] = mapped_column(
        ForeignKey('dict_task_types.id', name='fk_task_task_type_id', ondelete='RESTRICT'),
        nullable=False,
        comment="ID типу завдання з довідника dict_task_types"
    )
    # TODO: Узгодити використання status_id та успадкованого поля state.
    # Можливо, state буде використовувати значення з TaskStatus Enum, а status_id - це ForeignKey, якщо статуси в БД.
    # Якщо dict_statuses містить ті ж значення, що й TaskStatus Enum, то одне з них може бути зайвим.
    # Припускаємо, що status_id є зовнішнім ключем до таблиці dict_statuses.
    status_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('dict_statuses.id', name='fk_task_status_id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="ID статусу завдання з довідника dict_statuses"
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, comment="Термін виконання завдання (кінцева дата)"
    )
    is_recurring: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Прапорець: чи є завдання рекурентним"
    )
    recurrence_pattern: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Шаблон рекурентності (наприклад, RRULE або cron)"
    )
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Прапорець: чи є завдання обов'язковим"
    )
    parent_task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('tasks.id', name='fk_task_parent_task_id', ondelete='SET NULL'),
        # Або CASCADE, якщо підзавдання мають видалятися з батьківським
        nullable=True,
        index=True,
        comment="ID батьківського завдання (для ієрархії завдань)"
    )

    # Поля для прямого нарахування балів/штрафів. Можуть бути альтернативою або доповненням до BonusRule.
    points_reward: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Кількість балів за виконання завдання (якщо застосовно)"
    )
    penalty_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Сума штрафу за невиконання або прострочення (якщо застосовно)"
    )

    # --- Поля, специфічні для Подій (якщо Task використовується і для подій) ---
    event_start_time: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, comment="Час початку події (якщо завдання є подією)"
    )
    event_end_time: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, comment="Час закінчення події (якщо завдання є подією)"
    )
    event_location: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Місце проведення події (якщо застосовно)"
    )

    # --- Зв'язки (Relationships) ---
    # group_id успадковано з BaseMainModel (через GroupAffiliationMixin)
    group: Mapped["Group"] = relationship(
        foreign_keys=[BaseMainModel.group_id],  # Явно вказуємо foreign_keys через неоднозначність успадкування
        back_populates="tasks",
        lazy="selectin"
    )
    task_type: Mapped["TaskType"] = relationship(foreign_keys=[task_type_id], lazy="selectin")
    status: Mapped[Optional["Status"]] = relationship(foreign_keys=[status_id], lazy="selectin")

    parent_task: Mapped[Optional["Task"]] = relationship(remote_side=[BaseMainModel.id], back_populates="sub_tasks",
                                                         lazy="selectin")  # id успадковано
    sub_tasks: Mapped[List["Task"]] = relationship(back_populates="parent_task", cascade="all, delete-orphan",
                                                   lazy="selectin")

    assignments: Mapped[List["TaskAssignment"]] = relationship(back_populates="task", cascade="all, delete-orphan",
                                                               lazy="selectin")
    completions: Mapped[List["TaskCompletion"]] = relationship(back_populates="task", cascade="all, delete-orphan",
                                                               lazy="selectin")
    reviews: Mapped[List["TaskReview"]] = relationship(back_populates="task", cascade="all, delete-orphan",
                                                       lazy="selectin")

    bonus_rules: Mapped[List["BonusRule"]] = relationship(back_populates="task", cascade="all, delete-orphan",
                                                          lazy="selectin")

    # _repr_fields успадковуються та збираються з BaseMainModel та його міксинів.
    # Додаємо специфічні для Task поля.
    _repr_fields = ["task_type_id", "status_id", "due_date", "is_recurring", "parent_task_id"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі Task.
    logger.info("--- Модель Завдання/Події (Task) ---")
    logger.info(f"Назва таблиці: {Task.__tablename__}")

    logger.info("\nОчікувані поля (успадковані та власні):")
    expected_fields = [
        'id', 'name', 'description', 'state', 'group_id', 'notes',
        'created_at', 'updated_at', 'deleted_at',
        'task_type_id', 'status_id', 'due_date', 'is_recurring', 'recurrence_pattern',
        'is_mandatory', 'parent_task_id', 'points_reward', 'penalty_amount',
        'event_start_time', 'event_end_time', 'event_location'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = [
        'group', 'task_type', 'status', 'parent_task', 'sub_tasks',
        'assignments', 'completions', 'reviews', 'bonus_rules'
    ]
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_task = Task(
        id=1,
        name="Виконати щотижневий звіт",
        description="Підготувати та надіслати звіт про виконану роботу за тиждень.",
        group_id=202,  # ID групи, до якої належить завдання
        task_type_id=1,  # ID типу завдання (наприклад, "Звичайне завдання")
        # status_id=1,    # ID статусу (наприклад, "Відкрито") - або використовувати поле state
        state="open",  # Успадковане поле state, може використовувати значення з TaskStatus Enum
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        is_recurring=True,
        recurrence_pattern="RRULE:FREQ=WEEKLY;BYDAY=FR",  # Приклад RRULE
        is_mandatory=True,
        points_reward=Decimal("10.00")
    )
    example_task.created_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра Task (без сесії):\n  {example_task}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <Task(id=1, name='Виконати щотижневий звіт', state='open', task_type_id=1, due_date=..., created_at=...)>

    logger.info(
        "\nПримітка: Для повноцінної роботи з моделлю та її зв'язками потрібна сесія SQLAlchemy та підключення до БД.")
    logger.info("TODO: Узгодити використання поля 'state' (успадковане) та 'status_id' (специфічне для Task).")
