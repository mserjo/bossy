# backend/app/src/schemas/tasks/assignment.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `TaskAssignmentModel`.
Схеми використовуються для валідації даних при призначенні завдань
виконавцям (користувачам або командам) та відображенні інформації про призначення.
"""

from pydantic import Field, model_validator
from typing import Optional, List, Any, ForwardRef
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.tasks.task import TaskSimpleSchema # Або повна TaskSchema
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.teams.team import TeamSimpleSchema # Або повна TeamSchema
# from backend.app.src.schemas.dictionaries.status import StatusSchema

TaskSimpleSchema = ForwardRef('backend.app.src.schemas.tasks.task.TaskSimpleSchema') # Використовуємо Simple для уникнення рекурсії
UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
TeamSimpleSchema = ForwardRef('backend.app.src.schemas.teams.team.TeamSimpleSchema') # Аналогічно
StatusSchema = ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema')

# --- Схема для відображення інформації про призначення завдання (для читання) ---
class TaskAssignmentSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення призначення завдання.
    `created_at` використовується як `assigned_at`.
    """
    task_id: uuid.UUID = Field(..., description="ID завдання, яке призначено")
    user_id: Optional[uuid.UUID] = Field(None, description="ID користувача-виконавця (якщо призначено користувачу)")
    team_id: Optional[uuid.UUID] = Field(None, description="ID команди-виконавця (якщо призначено команді)")

    assigned_by_user_id: Optional[uuid.UUID] = Field(None, description="ID користувача (адміна), який зробив призначення")
    status_id: Optional[uuid.UUID] = Field(None, description="ID статусу цього призначення")
    notes: Optional[str] = Field(None, description="Нотатки щодо цього призначення")

    # --- Розгорнуті зв'язки (приклад) ---
    task: Optional[TaskSimpleSchema] = Field(None, description="Інформація про завдання")
    user: Optional[UserPublicSchema] = Field(None, description="Інформація про користувача-виконавця")
    team: Optional[TeamSimpleSchema] = Field(None, description="Інформація про команду-виконавця")
    assigner: Optional[UserPublicSchema] = Field(None, description="Інформація про користувача, який зробив призначення")
    status: Optional[StatusSchema] = Field(None, description="Розгорнутий статус призначення")


# --- Схема для створення нового призначення завдання ---
class TaskAssignmentCreateSchema(BaseSchema):
    """
    Схема для створення нового призначення завдання.
    """
    task_id: uuid.UUID = Field(..., description="ID завдання, яке призначається")

    # Має бути заповнене або user_id, або team_id, але не обидва.
    user_id: Optional[uuid.UUID] = Field(None, description="ID користувача-виконавця")
    team_id: Optional[uuid.UUID] = Field(None, description="ID команди-виконавця")

    # assigned_by_user_id: uuid.UUID # Встановлюється автоматично з поточного користувача (адміна)
    status_id: Optional[uuid.UUID] = Field(None, description="Початковий статус призначення (наприклад, 'призначено')")
    notes: Optional[str] = Field(None, description="Нотатки")

    @model_validator(mode='after')
    def check_assignee_exclusive_and_present(cls, data: 'TaskAssignmentCreateSchema') -> 'TaskAssignmentCreateSchema':
        user_id_present = data.user_id is not None
        team_id_present = data.team_id is not None

        if not (user_id_present ^ team_id_present): # XOR: має бути встановлено лише одне з них
            # Або, якщо завдання може бути призначене і користувачу, і команді одночасно (нетипово),
            # або нікому (відкрите завдання - але це не фіксується в TaskAssignment),
            # то ця валідація інша.
            # Поточна логіка: завдання призначається АБО користувачу, АБО команді.
            # Якщо завдання "відкрите для всіх", то запис в TaskAssignment не створюється до моменту взяття в роботу.
            # Отже, для створення призначення, одне з полів має бути.
            raise ValueError("Завдання має бути призначене або користувачеві (user_id), або команді (team_id), але не обом одночасно і не жодному.")
        return data

# --- Схема для оновлення інформації про призначення (наприклад, зміна статусу) ---
class TaskAssignmentUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючого призначення завдання.
    Зазвичай оновлюється статус або нотатки.
    Виконавець (user_id/team_id) та завдання (task_id) зазвичай не змінюються.
    """
    status_id: Optional[uuid.UUID] = Field(None, description="Новий ID статусу призначення")
    notes: Optional[str] = Field(None, description="Нові нотатки")

    # Поля, які зазвичай не змінюються:
    # task_id: Optional[uuid.UUID]
    # user_id: Optional[uuid.UUID]
    # team_id: Optional[uuid.UUID]
    # assigned_by_user_id: Optional[uuid.UUID]


# TaskAssignmentSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `TaskAssignmentModel`.
# `TaskAssignmentModel` успадковує від `BaseModel`.
# `TaskAssignmentSchema` успадковує від `AuditDatesSchema` і додає поля призначення.
# Розгорнуті зв'язки додані з `ForwardRef`.
#
# `TaskAssignmentCreateSchema`:
#   - `task_id` обов'язкове.
#   - `user_id` або `team_id` мають бути надані (взаємовиключно) - перевіряється валідатором.
#   - `assigned_by_user_id` встановлюється сервісом.
#   - `status_id` опціональне (може бути дефолтний статус).
#
# `TaskAssignmentUpdateSchema` дозволяє оновлювати `status_id` та `notes`.
#
# `created_at` з `AuditDatesSchema` використовується як `assigned_at`.
# Все виглядає узгоджено.
#
# Валідатор `check_assignee_exclusive_and_present` в `TaskAssignmentCreateSchema`
# забезпечує, що завдання призначається або користувачеві, або команді.
# Якщо завдання може бути "відкритим для всіх" і не мати конкретного виконавця
# на етапі створення запису в `TaskAssignmentModel` (що нетипово для цієї моделі,
# вона саме для фіксації призначення), то валідатор потрібно змінити.
# Поточна логіка передбачає, що `TaskAssignmentModel` створюється, коли є конкретний виконавець.
# "Відкриті" завдання - це ті, для яких немає записів в `TaskAssignmentModel`,
# або ж вони мають спеціальний статус в `TaskModel`.
#
# Зауваження до `TaskAssignmentSchema`: `task` (розгорнута інформація про завдання)
# може бути надмірною, якщо список призначень повертається в контексті одного завдання.
# Тоді достатньо `user`, `team`, `assigner`, `status`.
# Якщо ж список призначень повертається, наприклад, для користувача (всі його призначення),
# то розгорнута інформація про завдання (`task: Optional[TaskSimpleSchema]`) може бути корисною.
# Поки що залишаю `task` закоментованим, оскільки `task_id` вже є.
#
# Все виглядає добре.

TaskAssignmentSchema.model_rebuild()
TaskAssignmentCreateSchema.model_rebuild()
TaskAssignmentUpdateSchema.model_rebuild()
