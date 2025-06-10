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
from datetime import datetime
from typing import Optional, List, Any  # Any для тимчасових полів
from decimal import Decimal

from pydantic import Field, EmailStr  # EmailStr тут не потрібен, але може бути в UserPublicProfileSchema

# Абсолютний імпорт базових схем та Enum
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin, BaseMainSchema
from backend.app.src.core.dicts import TaskStatus as TaskStatusEnum  # Для значень за замовчуванням та валідації
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
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
        description="Назва завдання або події.",
        examples=["Розробити новий функціонал"]
    )
    description: Optional[str] = Field(
        None,
        description="Детальний опис завдання або події."
    )
    # TODO: Валідувати task_type_code на основі існуючих кодів в довіднику dict_task_types
    task_type_code: str = Field(
        description="Код типу завдання з довідника (наприклад, 'REGULAR_TASK', 'EVENT')."
    )

    # TODO: Узгодити status_code/status_id з полем state з BaseMainSchema.
    # Якщо `state` з BaseMainSchema є основним полем статусу, то `status_code` тут може бути зайвим
    # або використовуватися для передачі коду статусу, який сервіс перетворить на `state` або `status_id` моделі.
    # Поки що залишимо `state` для схем Create/Update, а `status` (об'єкт) та `status_code` для Response.
    state: Optional[str] = Field(
        default=TaskStatusEnum.OPEN.value,
        max_length=50,
        description=f"Стан завдання (за замовчуванням '{TaskStatusEnum.OPEN.value}'). Використовуйте значення з TaskStatus Enum.",
        examples=[ts.value for ts in TaskStatusEnum]
    )
    due_date: Optional[datetime] = Field(
        None,
        description="Термін виконання завдання (кінцева дата та час).",
        examples=[(datetime.now() + timedelta(days=7)).isoformat()]
    )
    is_recurring: bool = Field(
        default=False,
        description="Прапорець: чи є завдання рекурентним."
    )
    recurrence_pattern: Optional[str] = Field(
        None,
        max_length=TASK_RECURRENCE_PATTERN_MAX_LENGTH,
        description="Шаблон рекурентності (наприклад, RRULE або cron-вираз).",
        examples=["RRULE:FREQ=WEEKLY;BYDAY=MO;INTERVAL=1"]
    )
    is_mandatory: bool = Field(
        default=False,
        description="Прапорець: чи є завдання обов'язковим для виконання."
    )
    parent_task_id: Optional[int] = Field(
        None,
        description="ID батьківського завдання (для створення підзавдання)."
    )
    points_reward: Optional[Decimal] = Field(
        None,
        ge=0,  # Бали не можуть бути від'ємними при прямому нарахуванні
        description="Кількість балів за успішне виконання завдання (якщо застосовно, не може бути від'ємним).",
        examples=[Decimal("10.00"), Decimal("50.50")]
    )
    penalty_amount: Optional[Decimal] = Field(
        None,
        ge=0,  # Штраф також вказується як позитивне число, а тип бонусу визначає списання.
        description="Сума штрафу за невиконання або прострочення (якщо застосовно, не може бути від'ємним).",
        examples=[Decimal("5.00")]
    )
    notes: Optional[str] = Field(
        None,
        description="Додаткові нотатки до завдання."
    )

    # Поля, специфічні для подій
    event_start_time: Optional[datetime] = Field(
        None,
        description="Час початку події (якщо завдання є подією)."
    )
    event_end_time: Optional[datetime] = Field(
        None,
        description="Час закінчення події (якщо завдання є подією)."
    )
    event_location: Optional[str] = Field(
        None,
        max_length=TASK_EVENT_LOCATION_MAX_LENGTH,
        description="Місце проведення події (якщо застосовно)."
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
    name: Optional[str] = Field(None, max_length=TASK_NAME_MAX_LENGTH)
    description: Optional[str] = None
    task_type_code: Optional[str] = None
    state: Optional[str] = Field(None, max_length=50)
    due_date: Optional[datetime] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = Field(None, max_length=TASK_RECURRENCE_PATTERN_MAX_LENGTH)
    is_mandatory: Optional[bool] = None
    parent_task_id: Optional[int] = None  # Може бути None для видалення зв'язку
    points_reward: Optional[Decimal] = Field(None, ge=0)
    penalty_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    event_start_time: Optional[datetime] = None
    event_end_time: Optional[datetime] = None
    event_location: Optional[str] = Field(None, max_length=TASK_EVENT_LOCATION_MAX_LENGTH)


class TaskSchema(
    BaseMainSchema):  # Успадковуємо від BaseMainSchema для id, timestamps, name, description, state, notes, group_id
    """
    Схема для представлення даних завдання у відповідях API.
    """
    # id, name, description, state, notes, group_id, created_at, updated_at, deleted_at - успадковані

    # Специфічні поля моделі Task, що не входять до BaseMainSchema або потребують іншого представлення
    task_type_code: Optional[str] = Field(None,
                                          description="Код типу завдання.")  # З моделі Task, але може бути корисним і в BaseMainSchema

    # TODO: Узгодити status_code/status_id з успадкованим полем `state`.
    # Якщо `state` є основним, то `status` (об'єкт StatusSchema) може його деталізувати.
    # Або `status_id` з моделі може мапитися сюди.
    status_code: Optional[str] = Field(None, description="Код поточного статусу завдання (з довідника dict_statuses).")

    due_date: Optional[datetime] = None
    is_recurring: bool
    recurrence_pattern: Optional[str] = None
    is_mandatory: bool
    parent_task_id: Optional[int] = None
    points_reward: Optional[Decimal] = None
    penalty_amount: Optional[Decimal] = None
    event_start_time: Optional[datetime] = None
    event_end_time: Optional[datetime] = None
    event_location: Optional[str] = None

    # Пов'язані об'єкти (для розширеної інформації)
    # TODO: Замінити Any на відповідні схеми
    task_type: Optional[TaskTypeSchema] = Field(None, description="Об'єкт типу завдання.")
    status: Optional[StatusSchema] = Field(None,
                                           description="Об'єкт статусу завдання (з довідника).")  # Якщо використовується status_id

    parent_task: Optional[Any] = Field(None,
                                       description="Коротка інформація про батьківське завдання (може бути TaskSchema).")  # Рекурсивна схема

    # Обчислювані поля (зазвичай додаються сервісом)
    sub_tasks_count: Optional[int] = Field(None, description="Кількість підзавдань.")
    assignments_count: Optional[int] = Field(None, description="Кількість призначень цього завдання.")
    completions_count: Optional[int] = Field(None, description="Кількість виконань цього завдання.")


class TaskDetailSchema(TaskSchema):
    """
    Схема для деталізованого представлення завдання, включаючи пов'язані об'єкти.
    """
    # sub_tasks, assignments, completions, reviews, bonus_rules успадковуються з TaskSchema,
    # але тут вони можуть бути визначені з більш конкретними типами або заповнені даними.

    # TODO: Замінити Any на відповідні списки схем
    sub_tasks: Optional[List[TaskSchema]] = Field(default_factory=list, description="Список підзавдань.")
    assignments: Optional[List[TaskAssignmentSchema]] = Field(default_factory=list,
                                                              description="Список призначень завдання.")
    completions: Optional[List[TaskCompletionSchema]] = Field(default_factory=list,
                                                              description="Список виконань завдання.")
    reviews: Optional[List[TaskReviewSchema]] = Field(default_factory=list, description="Список відгуків на завдання.")
    bonus_rules: Optional[List[BonusRuleSchema]] = Field(default_factory=list,
                                                         description="Список правил нарахування бонусів, пов'язаних із завданням.")


if __name__ == "__main__":
    # Демонстраційний блок для схем завдань.
    logger.info("--- Pydantic Схеми для Завдань (Task) ---")
    from datetime import timedelta  # Для timedelta в прикладах

    logger.info("\nTaskCreateSchema (приклад):")
    create_data = {
        "name": "Організувати корпоратив",  # TODO i18n
        "description": "Підготувати та провести корпоративний захід для команди.",  # TODO i18n
        "task_type_code": "EVENT",  # Має існувати в довіднику dict_task_types
        "state": TaskStatusEnum.OPEN.value,
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
        "state": TaskStatusEnum.IN_PROGRESS.value,
        "is_mandatory": True
    }
    update_instance = TaskUpdateSchema(**update_data)
    logger.info(update_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nTaskSchema (приклад відповіді API):")
    task_response_data = {
        "id": 1,
        "name": "Завершити звіт",  # TODO i18n
        "description": "Фіналізувати квартальний звіт по проекту Alpha.",  # TODO i18n
        "state": TaskStatusEnum.IN_PROGRESS.value,
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
