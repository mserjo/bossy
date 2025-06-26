# backend/app/src/schemas/dictionaries/task_type.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `TaskTypeModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні типів завдань/подій.
"""

from pydantic import Field
from typing import Optional, List
import uuid

from backend.app.src.schemas.dictionaries.base_dict import BaseDictSchema, BaseDictCreateSchema, BaseDictUpdateSchema

# --- Схема для відображення типу завдання/події (для читання) ---
class TaskTypeSchema(BaseDictSchema):
    """
    Схема для представлення типу завдання/події. Успадковує всі поля від BaseDictSchema.
    """
    # TaskTypeModel може мати додаткові специфічні поля, наприклад, прапорці,
    # що визначають поведінку цього типу.
    # Наприклад:
    # is_event: bool = Field(False, description="True, якщо це подія (не потребує активного виконання)")
    # default_bonus_type: Optional[str] = Field(None, description="Тип бонусу за замовчуванням ('positive', 'negative')")
    #
    # Поки що `TaskTypeModel` не має таких полів, але якщо вони будуть додані,
    # їх потрібно буде відобразити тут.
    is_event: bool = Field(False, description="True, якщо це подія")
    is_penalty_type: bool = Field(False, description="True, якщо цей тип передбачає штраф")
    can_have_subtasks: bool = Field(False, description="True, якщо завдання цього типу може мати підзавдання")

# --- Схема для створення нового типу завдання/події ---
class TaskTypeCreateSchema(BaseDictCreateSchema):
    """
    Схема для створення нового типу завдання/події. Успадковує поля від BaseDictCreateSchema.
    """
    # `name` та `code` є обов'язковими.
    # `description`, `state_id`, `notes` - опціональні.
    is_event: bool = Field(default=False, description="Чи є цей тип подією")
    is_penalty_type: bool = Field(default=False, description="Чи передбачає цей тип штраф")
    can_have_subtasks: bool = Field(default=False, description="Чи можуть завдання цього типу мати підзавдання")

# --- Схема для оновлення існуючого типу завдання/події ---
class TaskTypeUpdateSchema(BaseDictUpdateSchema):
    """
    Схема для оновлення існуючого типу завдання/події. Успадковує поля від BaseDictUpdateSchema.
    """
    # Всі поля опціональні.
    is_event: Optional[bool] = Field(None, description="Нове значення для прапорця 'is_event'")
    is_penalty_type: Optional[bool] = Field(None, description="Нове значення для прапорця 'is_penalty_type'")
    can_have_subtasks: Optional[bool] = Field(None, description="Нове значення для прапорця 'can_have_subtasks'")

# TODO: Переконатися, що схеми відповідають моделі `TaskTypeModel`.
# `TaskTypeModel` успадковує від `BaseDictModel`.
# `TaskTypeSchema` успадковує від `BaseDictSchema`.
# Поля `id, name, description, code, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes`
# коректно представлені в `TaskTypeSchema` через успадкування.
# `group_id` для типів завдань може бути `None` (глобальні типи) або вказувати на групу,
# якщо дозволені кастомні типи завдань на рівні групи (ТЗ цього явно не вимагає, але й не забороняє).
# Поки що припускаємо, що типи завдань переважно глобальні.
#
# Потенційні поля, такі як `is_event`, `can_have_subtasks` тощо,
# якщо будуть додані до `TaskTypeModel`, мають бути відображені і тут.
# Наразі схеми відповідають поточній структурі `TaskTypeModel`.
# Валідація `code` успадкована.
# Все виглядає узгоджено.
# Приклади типів завдань з ТЗ: "завдання", "підзавдання", "складне завдання",
# "командне завдання", "подія", "штраф".
# Ці різні характеристики (підзавдання, командне, подія, штраф) можуть бути
# або окремими типами (різними записами в `TaskTypeModel`), або прапорцями/атрибутами
# в `TaskModel` та/або `TaskTypeModel`.
# Поточна структура `TaskTypeModel` (лише базові поля довідника) передбачає,
# що це будуть різні записи в довіднику типів.
# Якщо, наприклад, "подія" - це характеристика, то в `TaskTypeModel` має бути поле `is_event: bool`,
# і воно має бути відображене в схемах. Поки що цього немає.
# Залишаю так, з можливістю розширення `TaskTypeModel` та цих схем.
