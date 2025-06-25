# backend/app/src/schemas/dictionaries/bonus_type.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `BonusTypeModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні типів бонусів.
"""

from pydantic import Field
from typing import Optional, List
import uuid

from backend.app.src.schemas.dictionaries.base_dict import BaseDictSchema, BaseDictCreateSchema, BaseDictUpdateSchema

# --- Схема для відображення типу бонусів (для читання) ---
class BonusTypeSchema(BaseDictSchema):
    """
    Схема для представлення типу бонусів. Успадковує всі поля від BaseDictSchema.
    Додає специфічне поле `allow_decimal`.
    """
    allow_decimal: bool = Field(..., description="Прапорець, чи дозволені дробові значення для цього типу бонусів")

# --- Схема для створення нового типу бонусів ---
class BonusTypeCreateSchema(BaseDictCreateSchema):
    """
    Схема для створення нового типу бонусів. Успадковує поля від BaseDictCreateSchema.
    Додає поле `allow_decimal`.
    """
    allow_decimal: bool = Field(default=False, description="Чи дозволені дробові значення для цього типу бонусів (за замовчуванням False)")

# --- Схема для оновлення існуючого типу бонусів ---
class BonusTypeUpdateSchema(BaseDictUpdateSchema):
    """
    Схема для оновлення існуючого типу бонусів. Успадковує поля від BaseDictUpdateSchema.
    Додає поле `allow_decimal`.
    """
    allow_decimal: Optional[bool] = Field(None, description="Нове значення для прапорця 'allow_decimal'")

# TODO: Переконатися, що схеми відповідають моделі `BonusTypeModel`.
# `BonusTypeModel` успадковує від `BaseDictModel` і додає поле `allow_decimal`.
# `BonusTypeSchema` успадковує від `BaseDictSchema` і також додає `allow_decimal`.
# `BonusTypeCreateSchema` та `BonusTypeUpdateSchema` також включають `allow_decimal`.
# Це виглядає коректним.
#
# Поля `id, name, description, code, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes`
# успадковуються з `BaseDictSchema`.
# `group_id` для типів бонусів, ймовірно, завжди буде `None`, оскільки це глобальний довідник,
# з якого групи обирають та налаштовують свою "валюту" (згідно ТЗ).
#
# Валідація `code` успадкована.
# Поле `allow_decimal` є важливим для визначення, чи можуть бонуси бути дробовими.
# Все виглядає узгоджено.
# Приклади типів бонусів з ТЗ: "бонуси", "бони", "бали", "очки", "зірочки".
# Кожен з них матиме свій запис в `BonusTypeModel` з відповідним значенням `allow_decimal`.
# Група потім обирає один з цих типів і може перевизначити `allow_decimal` та назву валюти
# в `GroupSettingsModel`.
# `BonusTypeModel` надає базові типи, з яких можна вибирати.
# `BonusTypeSchema` коректно відображає структуру `BonusTypeModel`.
