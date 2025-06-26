# backend/app/src/schemas/tasks/task.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `TaskModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні завдань та подій.
"""

from pydantic import Field, model_validator, field_validator
from typing import Optional, List, Any, ForwardRef, Union # Додано Union
import uuid
from datetime import datetime, timedelta # Додано timedelta

from backend.app.src.schemas.base import BaseMainSchema, BaseSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.dictionaries.task_type import TaskTypeSchema
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.groups.group import GroupSimpleSchema
# from backend.app.src.schemas.teams.team import TeamSimpleSchema
# from backend.app.src.schemas.tasks.assignment import TaskAssignmentSchema
# from backend.app.src.schemas.tasks.completion import TaskCompletionSchema
# from backend.app.src.schemas.tasks.review import TaskReviewSchema
# from backend.app.src.schemas.tasks.dependency import TaskDependencySchema # (можливо, не розгортається)

TaskTypeSchema = ForwardRef('backend.app.src.schemas.dictionaries.task_type.TaskTypeSchema')
UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
# GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema') # group_id вже є
# TeamSimpleSchema = ForwardRef('backend.app.src.schemas.teams.team.TeamSimpleSchema') # team_id вже є
TaskAssignmentSchema = ForwardRef('backend.app.src.schemas.tasks.assignment.TaskAssignmentSchema')
TaskCompletionSchema = ForwardRef('backend.app.src.schemas.tasks.completion.TaskCompletionSchema')
TaskReviewSchema = ForwardRef('backend.app.src.schemas.tasks.review.TaskReviewSchema')


# --- Схема для відображення повної інформації про завдання/подію ---
class TaskSchema(BaseMainSchema):
    """
    Повна схема для представлення завдання/події.
    Успадковує `id, name, description, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes`
    від `BaseMainSchema`.
    """
    task_type_id: uuid.UUID = Field(..., description="ID типу завдання/події")
    created_by_user_id: uuid.UUID = Field(..., description="ID користувача (адміна групи), який створив завдання/подію")

    bonus_points: Optional[float] = Field(None, description="Кількість бонусних балів за виконання (використовуємо float для Numeric)")
    penalty_points: Optional[float] = Field(None, description="Кількість штрафних балів за невиконання/прострочення")

    due_date: Optional[datetime] = Field(None, description="Термін виконання завдання")
    is_recurring: bool = Field(..., description="Чи є завдання/подія постійним (повторюваним)")
    recurring_interval: Optional[timedelta] = Field(None, description="Інтервал повторення (якщо is_recurring)")
    max_occurrences: Optional[int] = Field(None, ge=0, description="Максимальна кількість повторень (якщо is_recurring)")

    is_mandatory: bool = Field(..., description="Чи є завдання обов'язковим для виконання")

    allow_multiple_assignees: bool = Field(..., description="Чи може завдання мати декількох виконавців")
    first_completes_gets_bonus: bool = Field(..., description="Чи тільки перший виконавець отримує бонус (якщо allow_multiple_assignees=True)")

    parent_task_id: Optional[uuid.UUID] = Field(None, description="ID батьківського завдання (для підзадач)")
    team_id: Optional[uuid.UUID] = Field(None, description="ID команди, якій призначено завдання")

    streak_bonus_enabled: bool = Field(..., description="Чи ввімкнено бонус за послідовне виконання")
    streak_bonus_ref_task_id: Optional[uuid.UUID] = Field(None, description="ID завдання, за послідовне виконання якого дається бонус")
    streak_bonus_count: Optional[int] = Field(None, ge=1, description="Кількість послідовних виконань для бонусу")
    streak_bonus_points: Optional[float] = Field(None, description="Розмір додаткового бонусу за серію")

    # --- Розгорнуті зв'язки (приклад) ---
    task_type: Optional[TaskTypeSchema] = Field(None, description="Тип завдання/події")
    creator: Optional[UserPublicSchema] = Field(None, description="Користувач, який створив завдання")
    parent_task: Optional['TaskSchema'] = Field(None, description="Батьківське завдання (якщо це підзадача)")
    # child_tasks: List['TaskSchema'] = Field(default_factory=list, description="Список підзадач") # Зазвичай окремий запит
    team: Optional[ForwardRef('backend.app.src.schemas.teams.team.TeamSimpleSchema')] = Field(None, description="Команда, якій призначено завдання")
    streak_bonus_reference_task_info: Optional['TaskSchema'] = Field(None, description="Інформація про завдання, за яке нараховується стрік-бонус")

    # Списки призначень, виконань, відгуків зазвичай отримуються окремими запитами з пагінацією.
    # assignments: List[TaskAssignmentSchema] = Field(default_factory=list)
    # completions: List[TaskCompletionSchema] = Field(default_factory=list)
    # reviews: List[TaskReviewSchema] = Field(default_factory=list)

    state: Optional[ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema')] = Field(None, description="Статус завдання/події")


# --- Схема для створення нового завдання/події ---
class TaskCreateSchema(BaseSchema):
    """
    Схема для створення нового завдання/події.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Назва завдання/події")
    description: Optional[str] = Field(None, description="Детальний опис")
    # group_id: uuid.UUID # З URL
    # created_by_user_id: uuid.UUID # З поточного користувача
    state_id: Optional[uuid.UUID] = Field(None, description="Початковий статус завдання/події")

    task_type_id: uuid.UUID = Field(..., description="ID типу завдання/події")

    bonus_points: Optional[float] = Field(None)
    penalty_points: Optional[float] = Field(None)

    due_date: Optional[datetime] = Field(None)
    is_recurring: bool = Field(default=False)
    # recurring_interval_seconds: Optional[int] = Field(None, ge=1, description="Інтервал повторення в секундах")
    # Або ж, якщо приймаємо рядок типу "1 day", "2 weeks"
    recurring_interval_description: Optional[str] = Field(None, description="Опис інтервалу повторення, наприклад, 'daily', 'weekly', 'P1DT12H' (ISO 8601 duration)")
    max_occurrences: Optional[int] = Field(None, ge=0)

    is_mandatory: bool = Field(default=False)

    allow_multiple_assignees: bool = Field(default=False)
    first_completes_gets_bonus: bool = Field(default=True) # Має сенс, лише якщо allow_multiple_assignees=True

    parent_task_id: Optional[uuid.UUID] = Field(None)
    team_id: Optional[uuid.UUID] = Field(None) # Для командних завдань

    streak_bonus_enabled: bool = Field(default=False)
    streak_bonus_ref_task_id: Optional[uuid.UUID] = Field(None)
    streak_bonus_count: Optional[int] = Field(None, ge=1)
    streak_bonus_points: Optional[float] = Field(None)

    notes: Optional[str] = Field(None)

    # TODO: Додати валідатори:
    # - Якщо `is_recurring`=True, то `recurring_interval_description` має бути заповнене. (Вже є `validate_recurring_settings`)
    # - Якщо `allow_multiple_assignees`=False, то `first_completes_gets_bonus` не має значення (або має бути True).
    # - Якщо `streak_bonus_enabled`=True, то `streak_bonus_count` та `streak_bonus_points` мають бути заповнені. (Вже є `validate_streak_bonus_settings`)
    # - `streak_bonus_ref_task_id` має посилатися на існуюче завдання (перевірка на сервісі).

    @field_validator('due_date')
    @classmethod
    def due_date_must_be_in_future(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is not None and value <= datetime.utcnow().replace(tzinfo=None): # Або datetime.now(timezone.utc)
            # Потрібно узгодити часові зони. Припускаємо, що value приходить як naive UTC або вже UTC.
            raise ValueError("Термін виконання завдання (due_date) не може бути в минулому.")
        return value

    @model_validator(mode='after')
    def validate_recurring_settings(cls, data: 'TaskCreateSchema') -> 'TaskCreateSchema':
        if data.is_recurring and data.recurring_interval_description is None:
            raise ValueError("Для повторюваного завдання необхідно вказати інтервал повторення (recurring_interval_description).")
        if not data.is_recurring and (data.recurring_interval_description is not None or data.max_occurrences is not None):
            raise ValueError("Інтервал повторення та максимальна кількість повторень можуть бути вказані лише для повторюваних завдань.")
        return data

    @model_validator(mode='after')
    def validate_streak_bonus_settings(cls, data: 'TaskCreateSchema') -> 'TaskCreateSchema':
        if data.streak_bonus_enabled and (data.streak_bonus_count is None or data.streak_bonus_points is None):
            raise ValueError("Для увімкненого стрік-бонусу необхідно вказати кількість послідовних виконань та розмір бонусу.")
        if not data.streak_bonus_enabled and \
           (data.streak_bonus_ref_task_id is not None or data.streak_bonus_count is not None or data.streak_bonus_points is not None):
            raise ValueError("Параметри стрік-бонусу можуть бути вказані лише якщо стрік-бонус увімкнено.")
        return data


# --- Схема для оновлення існуючого завдання/події ---
class TaskUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючого завдання/події.
    Всі поля опціональні.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    state_id: Optional[uuid.UUID] = Field(None) # Зміна статусу

    task_type_id: Optional[uuid.UUID] = Field(None)

    bonus_points: Optional[float] = Field(None)
    penalty_points: Optional[float] = Field(None)

    due_date: Optional[datetime] = Field(None)
    is_recurring: Optional[bool] = Field(None)
    recurring_interval_description: Optional[str] = Field(None)
    max_occurrences: Optional[int] = Field(None, ge=0)

    is_mandatory: Optional[bool] = Field(None)

    allow_multiple_assignees: Optional[bool] = Field(None)
    first_completes_gets_bonus: Optional[bool] = Field(None)

    parent_task_id: Optional[uuid.UUID] = Field(None) # Зміна батьківського завдання - обережно
    team_id: Optional[uuid.UUID] = Field(None)

    streak_bonus_enabled: Optional[bool] = Field(None)
    streak_bonus_ref_task_id: Optional[uuid.UUID] = Field(None)
    streak_bonus_count: Optional[int] = Field(None, ge=1)
    streak_bonus_points: Optional[float] = Field(None)

    notes: Optional[str] = Field(None)
    is_deleted: Optional[bool] = Field(None) # Для "м'якого" видалення

    # TODO: Додати валідатори, аналогічні до CreateSchema, для перевірки узгодженості полів,
    # якщо вони передаються для оновлення. Це складніше, бо треба враховувати поточні значення з БД.
    # Краще таку логіку винести на сервісний рівень.
    pass

# TaskSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `TaskModel`.
# `TaskModel` успадковує від `BaseMainModel`.
# `TaskSchema` успадковує від `BaseMainSchema` і додає всі специфічні поля завдання.
# `float` використовується для `Numeric` полів (bonus_points, penalty_points).
# `timedelta` для `recurring_interval` в `TaskSchema`.
# `TaskCreateSchema` використовує `recurring_interval_description` (рядок) або `interval_seconds` (int),
# які потім конвертуються в `timedelta` на сервісному рівні для моделі.
# Це стандартний підхід для API.
#
# Розгорнуті зв'язки в `TaskSchema` (task_type, creator, parent_task, child_tasks, team)
# додані з використанням `ForwardRef` або будуть додані пізніше.
# Списки assignments, completions, reviews зазвичай не включаються в основну схему завдання
# для уникнення надмірності даних; їх отримують окремими запитами.
#
# Валідатори в `TaskCreateSchema` для `recurring_settings` та `streak_bonus_settings` додані.
# Все виглядає узгоджено.
# `group_id` та `state_id` успадковані з `BaseMainSchema`.
# `deleted_at`, `is_deleted`, `notes` також успадковані.
# `name` та `description` з `BaseMainSchema` використовуються для назви та опису завдання.
#
# Потрібно буде визначити `TaskSimpleSchema` для списків завдань, якщо `TaskSchema` буде занадто великою.
# Поки що залишаю одну `TaskSchema` для читання.
#
# Важливо: сервісний шар відповідатиме за правильну обробку `recurring_interval_description`
# (парсинг рядка типу "daily", "P1W" або використання `interval_seconds`)
# та конвертацію в `timedelta` для збереження в `TaskModel.recurring_interval`.
# Також за перевірку існування `parent_task_id`, `team_id`, `task_type_id` тощо.
#
# Все виглядає добре.

TaskSchema.model_rebuild()
TaskCreateSchema.model_rebuild()
TaskUpdateSchema.model_rebuild()
