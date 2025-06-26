# backend/app/src/schemas/dictionaries/group_type.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `GroupTypeModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні типів груп.
"""

from pydantic import Field
from typing import Optional, List
import uuid

from backend.app.src.schemas.dictionaries.base_dict import BaseDictSchema, BaseDictCreateSchema, BaseDictUpdateSchema

# --- Схема для відображення типу групи (для читання) ---
class GroupTypeSchema(BaseDictSchema):
    """
    Схема для представлення типу групи. Успадковує всі поля від BaseDictSchema.
    """
    # GroupTypeModel наразі не має додаткових специфічних полів,
    # окрім успадкованих від BaseDictModel.
    # Якщо б були, наприклад, поле `can_have_hierarchy: bool`, воно б додавалося тут.
    can_have_hierarchy: bool = Field(False, description="Чи може група цього типу мати ієрархію")

# --- Схема для створення нового типу групи ---
class GroupTypeCreateSchema(BaseDictCreateSchema):
    """
    Схема для створення нового типу групи. Успадковує поля від BaseDictCreateSchema.
    """
    # `name` та `code` є обов'язковими.
    # `description`, `state_id`, `notes` - опціональні.
    can_have_hierarchy: bool = Field(default=False, description="Чи може група цього типу мати ієрархію")

# --- Схема для оновлення існуючого типу групи ---
class GroupTypeUpdateSchema(BaseDictUpdateSchema):
    """
    Схема для оновлення існуючого типу групи. Успадковує поля від BaseDictUpdateSchema.
    """
    # Всі поля опціональні.
    can_have_hierarchy: Optional[bool] = Field(None, description="Нове значення для можливості ієрархії")

# TODO: Переконатися, що схеми відповідають моделі `GroupTypeModel`.
# `GroupTypeModel` успадковує від `BaseDictModel`.
# `GroupTypeSchema` успадковує від `BaseDictSchema`.
# Поля `id, name, description, code, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes`
# коректно представлені в `GroupTypeSchema` через успадкування.
# `group_id` для типів груп, ймовірно, завжди буде `None`, оскільки це глобальний довідник.
#
# Потенційні поля, такі як `can_have_hierarchy` або `max_members`,
# якщо будуть додані до `GroupTypeModel`, мають бути відображені і тут.
# Наразі схеми відповідають поточній структурі `GroupTypeModel`.
# Валідація `code` успадкована.
# Все виглядає узгоджено.
