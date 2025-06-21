# backend/app/src/schemas/tasks/task.py
"""
Pydantic схеми для сутності "Завдання" (Task).

Цей модуль визначає схеми для:
- Базового представлення завдання (`TaskBaseSchema`) для спільних полів створення/оновлення.
- Створення нового завдання (`TaskCreateSchema`).
- Оновлення існуючого завдання (`TaskUpdateSchema`).
- Представлення завдання у відповідях API (`TaskSchema`).
- Деталізованого представлення завдання (`TaskDetailSchema`).
"""
# TODO: Pydantic v1/v2 consistency: Review .dict() vs .model_dump(), .from_orm vs .model_validate
from datetime import datetime, date, timedelta  # date для дат, timedelta для прикладів
from typing import Optional, List, Any, Dict  # Dict для JSON
from decimal import Decimal

from pydantic import Field

# Абсолютний імпорт базових схем та Enum
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin, BaseMainSchema
from backend.app.src.core.dicts import TaskStatus as TaskStatusEnum  # Для значень за замовчуванням та валідації
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _
logger = get_logger(__name__)

# TODO: Замінити Any на конкретні схеми, коли вони будуть доступні/рефакторені.
# from backend.app.src.schemas.dictionaries.task_types import TaskTypeSchema
# from backend.app.src.schemas.dictionaries.statuses import StatusSchema
# from backend.app.src.schemas.auth.user import UserPublicProfileSchema # Для прикладів, якщо потрібно
# from .assignment import TaskAssignmentSchema # Потрібно буде створити
# from .completion import TaskCompletionSchema # Потрібно буде створити
# from .review import TaskReviewSchema # Потрібно буде створити
# from backend.app.src.schemas.bonuses.bonus_rule import BonusRuleSchema # Потрібно буде створити

TaskTypeSchema = Any  # Тимчасовий заповнювач
StatusSchema = Any  # Тимчасовий заповнювач
TaskAssignmentSchema = Any  # Тимчасовий заповнювач
TaskCompletionSchema = Any  # Тимчасовий заповнювач
TaskReviewSchema = Any  # Тимчасовий заповнювач
BonusRuleSchema = Any  # Тимчасовий заповнювач

TASK_NAME_MAX_LENGTH = 255
TASK_RECURRENCE_PATTERN_MAX_LENGTH = 255
TASK_EVENT_LOCATION_MAX_LENGTH = 255


class TaskBaseSchema(BaseSchema):
    """
    Базова схема для полів завдання, спільних для створення та оновлення.
    Не успадковує ID та часові мітки, оскільки вони не надаються клієнтом при створенні.
    """
    name: str = Field(
        ...,
        max_length=TASK_NAME_MAX_LENGTH,
        description=_("task.fields.name.description"),
        examples=["Розробити новий функціонал"]
    )
    description: Optional[str] = Field(
        None,
        description=_("task.fields.description.description")
    )
    task_type_code: str = Field(
        description=_("task.fields.task_type_code.description")
    )
    state: Optional[TaskStatusEnum] = Field(
        default=TaskStatusEnum.OPEN,
        description=_("task.fields.state.description"),
        examples=[ts for ts in TaskStatusEnum]
    )
    due_date: Optional[datetime] = Field(
        None,
        description=_("task.fields.due_date.description"),
        examples=[(datetime.now() + timedelta(days=7)).isoformat()]
    )
    is_recurring: bool = Field(
        default=False,
        description=_("task.fields.is_recurring.description")
    )
    recurrence_pattern: Optional[str] = Field(
        None,
        max_length=TASK_RECURRENCE_PATTERN_MAX_LENGTH,
        description=_("task.fields.recurrence_pattern.description"),
        examples=["RRULE:FREQ=WEEKLY;BYDAY=MO;INTERVAL=1"]
    )
    recurrence_start_date: Optional[date] = Field(
        None,
        description=_("task.fields.recurrence_start_date.description")
    )
    recurrence_end_date: Optional[date] = Field(
        None,
        description=_("task.fields.recurrence_end_date.description")
    )
    reminder_config: Optional[Dict[str, Any]] = Field(
        None,
        description=_("task.fields.reminder_config.description")
    )
    is_mandatory: bool = Field(
        default=False,
        description=_("task.fields.is_mandatory.description")
    )
    parent_task_id: Optional[int] = Field(
        None,
        description=_("task.fields.parent_task_id.description")
    )
    points_reward: Optional[Decimal] = Field(
        None,
        ge=0,
        description=_("task.fields.points_reward.description"),
        examples=[Decimal("10.00"), Decimal("50.50")]
    )
    penalty_amount: Optional[Decimal] = Field(
        None,
        ge=0,
        description=_("task.fields.penalty_amount.description"),
        examples=[Decimal("5.00")]
    )
    notes: Optional[str] = Field(
        None,
        description=_("task.fields.notes.description")
    )
    event_start_time: Optional[datetime] = Field(
        None,
        description=_("task.fields.event_start_time.description")
    )
    event_end_time: Optional[datetime] = Field(
        None,
        description=_("task.fields.event_end_time.description")
    )
    event_location: Optional[str] = Field(
        None,
        max_length=TASK_EVENT_LOCATION_MAX_LENGTH,
        description=_("task.fields.event_location.description")
    )


class TaskCreateSchema(TaskBaseSchema):
    """
    Схема для створення нового завдання.
    `group_id` зазвичай передається як параметр шляху або встановлюється сервісом.
    `creator_id` (якщо є) встановлюється сервісом на основі поточного користувача.
    """
    # Успадковує всі поля з TaskBaseSchema.
    # group_id буде встановлено сервісом, якщо завдання створюється в контексті групи.
    pass


class TaskUpdateSchema(TaskBaseSchema):
    """
    Схема для оновлення існуючого завдання.
    Всі поля, успадковані з `TaskBaseSchema`, стають опціональними для оновлення.
    """
    # Робимо всі поля з TaskBaseSchema опціональними
    name: Optional[str] = Field(None, max_length=TASK_NAME_MAX_LENGTH, description=_("task.update_fields.name.description"))
    description: Optional[str] = Field(None, description=_("task.fields.description.description")) # Reuse from base
    task_type_code: Optional[str] = Field(None, description=_("task.fields.task_type_code.description")) # Reuse
    state: Optional[TaskStatusEnum] = Field(None, description=_("task.fields.state.description")) # Reuse
    due_date: Optional[datetime] = Field(None, description=_("task.fields.due_date.description")) # Reuse

    is_recurring: Optional[bool] = Field(None, description=_("task.fields.is_recurring.description")) # Reuse
    is_recurring_template: Optional[bool] = Field(None, description=_("task.update_fields.is_recurring_template.description"))
    recurrence_pattern: Optional[str] = Field(None, max_length=TASK_RECURRENCE_PATTERN_MAX_LENGTH, description=_("task.fields.recurrence_pattern.description")) # Reuse
    recurrence_start_date: Optional[date] = Field(None, description=_("task.fields.recurrence_start_date.description")) # Reuse
    recurrence_end_date: Optional[date] = Field(None, description=_("task.fields.recurrence_end_date.description")) # Reuse
    reminder_config: Optional[Dict[str, Any]] = Field(None, description=_("task.fields.reminder_config.description")) # Reuse

    is_mandatory: Optional[bool] = Field(None, description=_("task.fields.is_mandatory.description")) # Reuse
    parent_task_id: Optional[int] = Field(None, description=_("task.fields.parent_task_id.description")) # Reuse
    points_reward: Optional[Decimal] = Field(None, ge=0, description=_("task.fields.points_reward.description")) # Reuse
    penalty_amount: Optional[Decimal] = Field(None, ge=0, description=_("task.fields.penalty_amount.description")) # Reuse
    notes: Optional[str] = Field(None, description=_("task.fields.notes.description")) # Reuse
    event_start_time: Optional[datetime] = Field(None, description=_("task.fields.event_start_time.description")) # Reuse
    event_end_time: Optional[datetime] = Field(None, description=_("task.fields.event_end_time.description")) # Reuse
    event_location: Optional[str] = Field(None, max_length=TASK_EVENT_LOCATION_MAX_LENGTH, description=_("task.fields.event_location.description")) # Reuse


class TaskSchema(
    BaseMainSchema):  # Успадковуємо від BaseMainSchema для id, timestamps, name, description, state, notes, group_id
    """
    Схема для представлення даних завдання у відповідях API.
    """
    # id, name, description, notes, group_id, created_at, updated_at, deleted_at - успадковані
    # state успадковано, але тут буде перевизначено для використання Enum

    # Специфічні поля моделі Task, що не входять до BaseMainSchema або потребують іншого представлення
    state: Optional[TaskStatusEnum] = Field(None, description=_("task.fields.state.description")) # Reuse
    task_type_code: Optional[str] = Field(None, description=_("task.fields.task_type_code.description")) # Reuse

    status_code: Optional[str] = Field(None, description=_("task.response.fields.status_code.description"))

    due_date: Optional[datetime] = Field(None, description=_("task.fields.due_date.description"))

    # Поля повторення та нагадувань
    is_recurring: bool = Field(description=_("task.fields.is_recurring.description")) # Reuse
    is_recurring_template: Optional[bool] = Field(None, description=_("task.response.fields.is_recurring_template.description"))
    recurrence_pattern: Optional[str] = Field(None, description=_("task.fields.recurrence_pattern.description")) # Reuse
    recurrence_start_date: Optional[date] = Field(None, description=_("task.fields.recurrence_start_date.description")) # Reuse
    recurrence_end_date: Optional[date] = Field(None, description=_("task.fields.recurrence_end_date.description")) # Reuse
    last_instance_created_at: Optional[datetime] = Field(None, description=_("task.response.fields.last_instance_created_at.description"))
    next_occurrence_at: Optional[datetime] = Field(None, description=_("task.response.fields.next_occurrence_at.description"))
    last_reminder_sent_at: Optional[datetime] = Field(None, description=_("task.response.fields.last_reminder_sent_at.description"))
    reminder_config: Optional[Dict[str, Any]] = Field(None, description=_("task.fields.reminder_config.description")) # Reuse

    is_mandatory: bool = Field(description=_("task.fields.is_mandatory.description")) # Reuse
    parent_task_id: Optional[int] = Field(None, description=_("task.fields.parent_task_id.description")) # Reuse
    points_reward: Optional[Decimal] = Field(None, description=_("task.fields.points_reward.description")) # Reuse
    penalty_amount: Optional[Decimal] = Field(None, description=_("task.fields.penalty_amount.description")) # Reuse
    event_start_time: Optional[datetime] = Field(None, description=_("task.fields.event_start_time.description")) # Reuse
    event_end_time: Optional[datetime] = Field(None, description=_("task.fields.event_end_time.description")) # Reuse
    event_location: Optional[str] = Field(None, description=_("task.fields.event_location.description")) # Reuse

    # Пов'язані об'єкти (для розширеної інформації)
    task_type: Optional[TaskTypeSchema] = Field(None, description=_("task.response.fields.task_type.description"))
    status: Optional[StatusSchema] = Field(None, description=_("task.response.fields.status.description"))

    parent_task: Optional[Any] = Field(None, description=_("task.response.fields.parent_task.description"))

    # Обчислювані поля (зазвичай додаються сервісом)
    sub_tasks_count: Optional[int] = Field(None, description=_("task.response.fields.sub_tasks_count.description"))
    assignments_count: Optional[int] = Field(None, description=_("task.response.fields.assignments_count.description"))
    completions_count: Optional[int] = Field(None, description=_("task.response.fields.completions_count.description"))


class TaskDetailSchema(TaskSchema):
    """
    Схема для деталізованого представлення завдання, включаючи пов'язані об'єкти.
    """
    sub_tasks: Optional[List[TaskSchema]] = Field(default_factory=list, description=_("task.detail_response.fields.sub_tasks.description"))
    assignments: Optional[List[TaskAssignmentSchema]] = Field(default_factory=list, description=_("task.detail_response.fields.assignments.description"))
    completions: Optional[List[TaskCompletionSchema]] = Field(default_factory=list, description=_("task.detail_response.fields.completions.description"))
    reviews: Optional[List[TaskReviewSchema]] = Field(default_factory=list, description=_("task.detail_response.fields.reviews.description"))
    bonus_rules: Optional[List[BonusRuleSchema]] = Field(default_factory=list, description=_("task.detail_response.fields.bonus_rules.description"))


if __name__ == "__main__":
    # Демонстраційний блок для схем завдань.
    logger.info("--- Pydantic Схеми для Завдань (Task) ---")
    from datetime import timedelta  # Для timedelta в прикладах

    logger.info("\nTaskCreateSchema (приклад):")
    create_data = {
        "name": "Організувати корпоратив",  # TODO i18n
        "description": "Підготувати та провести корпоративний захід для команди.",  # TODO i18n
        "task_type_code": "EVENT",  # Має існувати в довіднику dict_task_types
        "state": TaskStatusEnum.OPEN, # Використовуємо Enum напряму
        "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "event_start_time": (datetime.now() + timedelta(days=29)).isoformat(),
        "event_end_time": (datetime.now() + timedelta(days=29, hours=4)).isoformat(),
        "event_location": "Конференц-зал 'Київ'",  # TODO i18n
        "points_reward": Decimal("100.00")
    }
    create_instance = TaskCreateSchema(**create_data)
    logger.info(create_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nTaskUpdateSchema (приклад):")
    update_data = {
        "description": "Оновлений опис: Підготувати та провести корпоративний захід для команди до кінця кварталу.",
        # TODO i18n
        "state": TaskStatusEnum.IN_PROGRESS, # Використовуємо Enum напряму
        "is_mandatory": True
    }
    update_instance = TaskUpdateSchema(**update_data)
    logger.info(update_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nTaskSchema (приклад відповіді API):")
    task_response_data = {
        "id": 1,
        "name": "Завершити звіт",  # TODO i18n
        "description": "Фіналізувати квартальний звіт по проекту Alpha.",  # TODO i18n
        "state": TaskStatusEnum.IN_PROGRESS, # Використовуємо Enum напряму
        "group_id": 10,
        "created_at": datetime.now() - timedelta(days=2),
        "updated_at": datetime.now(),
        "task_type_code": "REGULAR_TASK",
        # "task_type": {"id": 1, "name": "Звичайне Завдання", "code": "REGULAR_TASK"}, # Приклад TaskTypeSchema
        "due_date": datetime.now() + timedelta(days=5),
        "is_recurring": False,
        "is_mandatory": True,
        "points_reward": Decimal("25.00"),
        "assignments_count": 2,
        "completions_count": 0,
    }
    task_response_instance = TaskSchema(**task_response_data)
    logger.info(task_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nTaskDetailSchema (приклад деталізованої відповіді API):")
    task_detail_data = {
        **task_response_data,  # Успадковує поля з TaskSchema
        "sub_tasks_count": 0,  # Замість повного списку, якщо він порожній
        "assignments": [  # Приклад TaskAssignmentSchema
            {"task_id": 1, "user_id": 101, "status": "accepted", "created_at": datetime.now() - timedelta(days=1)},
            {"task_id": 1, "user_id": 102, "status": "assigned", "created_at": datetime.now()}
        ],
        # completions, reviews, bonus_rules можуть бути порожніми списками або заповненими
    }
    task_detail_instance = TaskDetailSchema(**task_detail_data)
    logger.info(task_detail_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми для пов'язаних об'єктів (TaskTypeSchema, StatusSchema, TaskAssignmentSchema і т.д.)")
    logger.info("наразі є заповнювачами (Any). Їх потрібно буде імпортувати після їх рефакторингу/визначення.")
    logger.info("Також, `task_type_code` та `status_code` потребують валідації на рівні сервісу або схеми.")
    logger.info("Узгодження `status_code` та `state` залишається відкритим питанням (TODO).")
