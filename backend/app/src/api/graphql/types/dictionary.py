# backend/app/src/api/graphql/types/dictionary.py
# -*- coding: utf-8 -*-
"""
GraphQL типи, пов'язані з довідниками системи.

Цей модуль визначає GraphQL типи для різних довідників,
таких як типи груп, типи бонусів тощо, якщо вони не визначені
в більш специфічних файлах типів (наприклад, task.py для TaskTypeType).
"""

import strawberry
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from backend.app.src.api.graphql.types.base import Node, TimestampsInterface

# Приклади типів довідників.
# Якщо TaskTypeType та TaskStatusType були визначені в task.py,
# а UserRoleType в user.py, то тут їх повторно визначати не потрібно,
# лише імпортувати в __init__.py пакета types.

@strawberry.type
class DictionaryGenericType(Node, TimestampsInterface): # Базовий тип для простих довідників
    """Загальний GraphQL тип для елемента довідника."""
    id: strawberry.ID
    code: str = strawberry.field(description="Унікальний код елемента довідника.")
    name: str = strawberry.field(description="Назва елемента довідника.")
    description: Optional[str] = strawberry.field(description="Опис елемента довідника.")
    created_at: datetime
    updated_at: datetime
    # db_id: strawberry.Private[int] # Якщо потрібно для резолверів


@strawberry.type
class GroupTypeType(DictionaryGenericType): # Успадковує від загального, якщо поля схожі
    """GraphQL тип для типу групи (з довідника)."""
    # Всі поля успадковані від DictionaryGenericType
    # Можна додати специфічні поля для типу групи, якщо вони є
    pass


@strawberry.type
class BonusTypeType(DictionaryGenericType):
    """GraphQL тип для типу бонусу (з довідника)."""
    # Наприклад, "бали", "зірочки", "поінти"
    # is_fractional: Optional[bool] = strawberry.field(description="Чи може цей тип бонусу бути дробовим.")
    pass


@strawberry.type
class IntegrationTypeType(DictionaryGenericType):
    """GraphQL тип для типу зовнішньої інтеграції (з довідника)."""
    # Наприклад, "google_calendar", "telegram", "jira"
    # category: Optional[str] = strawberry.field(description="Категорія інтеграції (напр. 'calendar', 'messenger', 'tracker').")
    pass


# --- Вхідні типи для CRUD операцій з довідниками (для адмінів) ---
# Зазвичай, довідники керуються через REST API (супер-адміном),
# але якщо потрібно надати GraphQL мутації:

@strawberry.input
class DictionaryItemCreateInput:
    code: str
    name: str
    description: Optional[str] = strawberry.UNSET

@strawberry.input
class DictionaryItemUpdateInput:
    code: Optional[str] = strawberry.UNSET
    name: Optional[str] = strawberry.UNSET
    description: Optional[str] = strawberry.UNSET


__all__ = [
    "DictionaryGenericType",
    "GroupTypeType",
    "BonusTypeType",
    "IntegrationTypeType",
    "DictionaryItemCreateInput",
    "DictionaryItemUpdateInput",
]
