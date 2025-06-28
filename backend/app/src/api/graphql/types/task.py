# backend/app/src/api/graphql/types/task.py
# -*- coding: utf-8 -*-
"""
GraphQL типи, пов'язані із завданнями та подіями.

Цей модуль визначає GraphQL типи для сутностей "Завдання/Подія",
"Призначення завдання", "Виконання завдання" тощо.
"""

import strawberry
from typing import Optional, List, TYPE_CHECKING, NewType, Annotated
from datetime import datetime
import uuid

from backend.app.src.api.graphql.types.base import Node, TimestampsInterface

if TYPE_CHECKING:
    from backend.app.src.api.graphql.types.user import UserType
    from backend.app.src.api.graphql.types.group import GroupType
    # from backend.app.src.api.graphql.types.dictionary import TaskTypeType, StatusType # Якщо це GraphQL типи

# GraphQL Enum для типу завдання/події (якщо це не довідник)
# @strawberry.enum
# class TaskOrEventTypeEnum(str):
#     TASK = "TASK"
#     EVENT = "EVENT"

# GraphQL Enum для статусу виконання завдання (якщо це не довідник)
# @strawberry.enum
# class TaskCompletionStatusEnum(str):
#     PENDING = "PENDING"      # Завдання очікує на взяття в роботу
#     IN_PROGRESS = "IN_PROGRESS" # Завдання в роботі
#     REVIEW = "REVIEW"        # Виконано, очікує перевірки
#     COMPLETED = "COMPLETED"    # Підтверджено, виконано успішно
#     REJECTED = "REJECTED"      # Відхилено після перевірки
#     CANCELLED = "CANCELLED"    # Скасовано користувачем або системою
#     FAILED = "FAILED"        # Не виконано в термін (якщо був дедлайн)


@strawberry.type
class TaskTypeType(Node, TimestampsInterface): # Якщо типи завдань - довідник
    """GraphQL тип для типу завдання/події (з довідника)."""
    id: strawberry.ID
    name: str = strawberry.field(description="Назва типу (наприклад, 'Завдання', 'Подія', 'Штраф').")
    code: str = strawberry.field(description="Унікальний код типу.")
    description: Optional[str] = strawberry.field(description="Опис типу завдання/події.")
    created_at: datetime
    updated_at: datetime

@strawberry.type
class TaskStatusType(Node, TimestampsInterface): # Якщо статуси - довідник
    """GraphQL тип для статусу завдання/виконання (з довідника)."""
    id: strawberry.ID
    name: str = strawberry.field(description="Назва статусу (наприклад, 'В роботі', 'Виконано', 'Перевірка').")
    code: str = strawberry.field(description="Унікальний код статусу.")
    description: Optional[str] = strawberry.field(description="Опис статусу.")
    created_at: datetime
    updated_at: datetime


@strawberry.type
class TaskType(Node, TimestampsInterface):
    """
    GraphQL тип, що представляє завдання або подію.
    """
    id: strawberry.ID
    name: str = strawberry.field(description="Назва завдання/події.")
    description: Optional[str] = strawberry.field(description="Детальний опис.")
    group: "GroupType" = strawberry.field(description="Група, до якої належить завдання/подія.")

    task_type_detail: Optional[TaskTypeType] = strawberry.field(description="Деталі типу завдання/події (з довідника).")
    # task_or_event: TaskOrEventTypeEnum = strawberry.field(description="Це завдання чи подія?") # Якщо Enum

    bonus_amount: Optional[float] = strawberry.field(description="Кількість бонусів за виконання.")
    penalty_amount: Optional[float] = strawberry.field(description="Штраф за невиконання (якщо є).")

    due_date: Optional[datetime] = strawberry.field(description="Термін виконання (дедлайн).")
    is_mandatory: bool = strawberry.field(description="Чи є завдання обов'язковим для виконання.")
    # max_assignees: Optional[int] = strawberry.field(description="Максимальна кількість виконавців (null - без обмежень).")
    # first_to_complete_gets_bonus: bool = strawberry.field(description="Чи тільки перший виконавець отримує бонус.")

    status: Optional[TaskStatusType] = strawberry.field(description="Поточний статус завдання (загальний, якщо не для конкретного користувача).")

    created_by: Optional["UserType"] = strawberry.field(description="Користувач, що створив завдання/подію (адмін групи).")
    created_at: datetime
    updated_at: datetime

    # TODO: Поля для зв'язків: виконавці (assignments), історія виконань (completions), підзадачі (dependencies)
    # @strawberry.field
    # async def assignments(self, info: strawberry.Info) -> List["TaskAssignmentType"]:
    #     pass

    # @strawberry.field
    # async def completions(self, info: strawberry.Info) -> List["TaskCompletionType"]:
    #     pass

    # db_id: strawberry.Private[int]


@strawberry.type
class TaskAssignmentType(Node, TimestampsInterface):
    """Призначення завдання конкретному користувачу."""
    id: strawberry.ID
    task: TaskType = strawberry.field(description="Завдання, що призначено.")
    assignee: "UserType" = strawberry.field(description="Користувач, якому призначено завдання.")
    assigned_at: datetime = strawberry.field(description="Час призначення.")
    status: Optional[TaskStatusType] = strawberry.field(description="Статус виконання цього призначення.") # Напр. 'IN_PROGRESS', 'REVIEW'
    # completion_details: Optional["TaskCompletionType"] = strawberry.field(description="Деталі виконання, якщо є.")
    created_at: datetime
    updated_at: datetime
    # db_id: strawberry.Private[int]


@strawberry.type
class TaskCompletionType(Node, TimestampsInterface):
    """Факт виконання завдання користувачем."""
    id: strawberry.ID
    task: TaskType = strawberry.field(description="Виконане завдання.")
    user: "UserType" = strawberry.field(description="Користувач, що виконав завдання.")
    completed_at: datetime = strawberry.field(description="Час позначки 'виконано' користувачем.")
    # verified_at: Optional[datetime] = strawberry.field(description="Час підтвердження адміном.")
    # verifier: Optional["UserType"] = strawberry.field(description="Адмін, що підтвердив виконання.")
    status: TaskStatusType = strawberry.field(description="Кінцевий статус виконання (напр. 'COMPLETED', 'REJECTED').")
    # awarded_bonus_amount: Optional[float] = strawberry.field(description="Кількість нарахованих бонусів.")
    # applied_penalty_amount: Optional[float] = strawberry.field(description="Кількість застосованих штрафів.")
    notes_by_user: Optional[str] = strawberry.field(description="Коментар користувача при виконанні.")
    # notes_by_verifier: Optional[str] = strawberry.field(description="Коментар адміна при перевірці.")
    created_at: datetime
    updated_at: datetime
    # db_id: strawberry.Private[int]


# --- Вхідні типи (Input Types) для мутацій ---

@strawberry.input
class TaskCreateInput:
    name: str
    group_id: strawberry.ID # ID групи, до якої належить завдання
    description: Optional[str] = strawberry.UNSET
    task_type_code: str # Код типу завдання з довідника
    bonus_amount: Optional[float] = strawberry.UNSET
    penalty_amount: Optional[float] = strawberry.UNSET
    due_date: Optional[datetime] = strawberry.UNSET
    is_mandatory: Optional[bool] = strawberry.UNSET
    # ... інші поля для створення завдання ...

@strawberry.input
class TaskUpdateInput:
    name: Optional[str] = strawberry.UNSET
    description: Optional[str] = strawberry.UNSET
    task_type_code: Optional[str] = strawberry.UNSET
    bonus_amount: Optional[float] = strawberry.UNSET
    penalty_amount: Optional[float] = strawberry.UNSET
    due_date: Optional[datetime] = strawberry.UNSET
    is_mandatory: Optional[bool] = strawberry.UNSET
    status_code: Optional[str] = strawberry.UNSET # Оновлення загального статусу завдання адміном
    # ... інші поля ...

@strawberry.input
class TaskAssignInput:
    """Вхідні дані для призначення завдання користувачу."""
    user_id: strawberry.ID # ID користувача, якому призначається завдання

@strawberry.input
class TaskSetStatusInput:
    """Вхідні дані для зміни статусу виконання завдання користувачем."""
    # Наприклад, 'IN_PROGRESS', 'REVIEW', 'CANCELLED'
    status_code: str # Код нового статусу з довідника
    notes: Optional[str] = strawberry.UNSET # Коментар користувача

@strawberry.input
class TaskVerifyCompletionInput:
    """Вхідні дані для адміна для підтвердження/відхилення виконання."""
    # 'COMPLETED' або 'REJECTED'
    status_code: str
    admin_notes: Optional[str] = strawberry.UNSET
    # Можливо, коригування бонусів, якщо це дозволено
    # adjusted_bonus: Optional[float] = strawberry.UNSET


__all__ = [
    "TaskTypeType",
    "TaskStatusType",
    "TaskType",
    "TaskAssignmentType",
    "TaskCompletionType",
    "TaskCreateInput",
    "TaskUpdateInput",
    "TaskAssignInput",
    "TaskSetStatusInput",
    "TaskVerifyCompletionInput",
]
