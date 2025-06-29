# backend/app/src/schemas/tasks/dependency.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `TaskDependencyModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні залежностей між завданнями.
"""

from pydantic import Field, model_validator, field_validator
from typing import Optional, List, Any, ForwardRef
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схему TaskSimpleSchema для зв'язків
# from backend.app.src.schemas.tasks.task import TaskSimpleSchema

from typing import TYPE_CHECKING # Додано TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.src.schemas.tasks.task import TaskSimpleSchema

# TaskSimpleSchema = ForwardRef('backend.app.src.schemas.tasks.task.TaskSimpleSchema') # Перенесено

# --- Схема для відображення залежності між завданнями (для читання) ---
class TaskDependencySchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення залежності між завданнями.
    """
    dependent_task_id: uuid.UUID = Field(..., description="ID завдання, яке залежить від іншого")
    prerequisite_task_id: uuid.UUID = Field(..., description="ID завдання, яке є передумовою")
    dependency_type: Optional[str] = Field(default="finish-to-start", description="Тип залежності (наприклад, 'finish-to-start')")

    # --- Розгорнуті зв'язки (приклад) ---
    dependent_task: Optional['TaskSimpleSchema'] = Field(None, description="Залежне завдання") # Рядкове посилання
    prerequisite_task: Optional['TaskSimpleSchema'] = Field(None, description="Завдання-передумова") # Рядкове посилання

# --- Схема для створення нової залежності між завданнями ---
class TaskDependencyCreateSchema(BaseSchema):
    """
    Схема для створення нової залежності між завданнями.
    """
    dependent_task_id: uuid.UUID = Field(..., description="ID залежного завдання")
    prerequisite_task_id: uuid.UUID = Field(..., description="ID завдання-передумови")
    dependency_type: Optional[str] = Field(default="finish-to-start", description="Тип залежності")

    @model_validator(mode='after')
    def check_tasks_are_different(cls, data: 'TaskDependencyCreateSchema') -> 'TaskDependencyCreateSchema':
        if data.dependent_task_id == data.prerequisite_task_id:
            raise ValueError("Завдання не може залежати саме від себе.")
        return data

    @field_validator('dependency_type')
    @classmethod
    def dependency_type_must_be_known(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            known_types = ['finish-to-start', 'start-to-start', 'finish-to-finish', 'start-to-finish']
            if value.lower() not in known_types: # Перевірка в нижньому регістрі для гнучкості
                raise ValueError(f"Невідомий тип залежності: '{value}'. Дозволені: {', '.join(known_types)}.")
            return value.lower()
        return value

# --- Схема для оновлення залежності (зазвичай залежності не оновлюються, а видаляються та створюються нові) ---
# Якщо все ж потрібно оновлювати, наприклад, тип залежності:
class TaskDependencyUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючої залежності між завданнями (наприклад, зміна типу).
    """
    dependency_type: Optional[str] = Field(None, description="Новий тип залежності")

    # `dependent_task_id` та `prerequisite_task_id` зазвичай не змінюються для існуючої залежності.
    # Якщо потрібно змінити самі завдання, то це видалення старої залежності та створення нової.

    @field_validator('dependency_type')
    @classmethod
    def dependency_type_must_be_known_update(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            known_types = ['finish-to-start', 'start-to-start', 'finish-to-finish', 'start-to-finish']
            if value.lower() not in known_types:
                raise ValueError(f"Невідомий тип залежності: '{value}'. Дозволені: {', '.join(known_types)}.")
            return value.lower()
        return value

# TaskDependencySchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `TaskDependencyModel`.
# `TaskDependencyModel` успадковує від `BaseModel`.
# `TaskDependencySchema` успадковує від `AuditDatesSchema` і додає `dependent_task_id`, `prerequisite_task_id`, `dependency_type`.
# Розгорнуті зв'язки `dependent_task` та `prerequisite_task` додані з `ForwardRef`.
#
# `TaskDependencyCreateSchema` містить необхідні поля для створення.
# Валідатор `check_tasks_are_different` запобігає самопосиланням.
# Валідатор для `dependency_type` (закоментований) може бути корисним.
#
# `TaskDependencyUpdateSchema` дозволяє оновлювати `dependency_type`.
#
# Все виглядає узгоджено.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` - час створення залежності.
# `updated_at` - якщо тип залежності змінюється.
# Це досить проста модель та схеми, що відображають зв'язок "багато-до-багатьох"
# між завданнями через цю проміжну таблицю/модель.
#
# Важливо, щоб сервісний шар перевіряв існування `dependent_task_id` та `prerequisite_task_id`
# перед створенням залежності, а також відсутність циклічних залежностей.
# (наприклад, А -> Б, Б -> В, В -> А).
# Схема сама по собі не може перевірити циклічність без доступу до всіх залежностей.
#
# Все виглядає добре.

# TaskDependencySchema.model_rebuild()
# TaskDependencyCreateSchema.model_rebuild()
# TaskDependencyUpdateSchema.model_rebuild()
