# backend/app/src/schemas/dictionaries/user_type.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `UserTypeModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні типів користувачів.
"""

from pydantic import Field
from typing import Optional

from backend.app.src.schemas.dictionaries.base_dict import BaseDictSchema, BaseDictCreateSchema, BaseDictUpdateSchema

# --- Схема для відображення типу користувача (для читання) ---
class UserTypeSchema(BaseDictSchema):
    """
    Схема для представлення типу користувача. Успадковує всі поля від BaseDictSchema.
    """
    # Модель UserTypeModel наразі не має додаткових власних полів,
    # окрім успадкованих від BaseDictModel.
    # Якщо б були, вони б додавалися тут.
    pass

# --- Схема для створення нового типу користувача ---
class UserTypeCreateSchema(BaseDictCreateSchema):
    """
    Схема для створення нового типу користувача. Успадковує поля від BaseDictCreateSchema.
    """
    # name, code - обов'язкові з BaseDictCreateSchema
    # description, state_id, notes - опціональні
    pass

# --- Схема для оновлення існуючого типу користувача ---
class UserTypeUpdateSchema(BaseDictUpdateSchema):
    """
    Схема для оновлення існуючого типу користувача. Успадковує поля від BaseDictUpdateSchema.
    """
    # name, code, description, state_id, notes, is_deleted - опціональні
    pass

# Локальні виклики model_rebuild() тут не потрібні,
# оскільки ці схеми прості і не мають ForwardRef.
# Якщо б UserTypeSchema мала ForwardRef, виклик був би перенесений до schemas/__init__.py.
