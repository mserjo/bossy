# backend/app/src/api/graphql/types/base.py
# -*- coding: utf-8 -*-
"""
Базові GraphQL типи та інтерфейси.

Цей модуль може містити:
- Інтерфейси, такі як `Node` (для Relay-сумісності), що вимагають глобально
  унікального поля `id: ID!`.
- Базові типи або міксіни для спільних полів (наприклад, `created_at`, `updated_at`).
- Загальні Enum типи, якщо вони не належать до конкретної сутності.
"""

import strawberry
from typing import Optional, List, NewType, Annotated
from datetime import datetime
import uuid

# Глобально унікальний ID для Relay
# Strawberry автоматично обробляє ID як рядок, але можна визначити кастомний скаляр, якщо потрібно
# GraphQLID = strawberry.scalar(
#     NewType("GraphQLID", str),
#     description="Глобально унікальний ідентифікатор, зазвичай Base64 кодований рядок `TypeName:id`."
# )
# Замість кастомного скаляра, будемо використовувати strawberry.ID

@strawberry.interface
class Node:
    """
    Інтерфейс для об'єктів, що мають глобально унікальний ID (Relay specification).
    """
    id: strawberry.ID = strawberry.field(description="Глобально унікальний ID об'єкта.")
    # Конкретні типи, що реалізують цей інтерфейс, повинні надавати резолвер для поля id,
    # який зазвичай повертає base64(f"{TypeName}:{database_id}").

@strawberry.type
class PageInfo:
    """
    Інформація для пагінації в стилі Relay.
    """
    has_next_page: bool = strawberry.field(description="Чи є наступна сторінка результатів.")
    has_previous_page: bool = strawberry.field(description="Чи є попередня сторінка результатів.")
    start_cursor: Optional[str] = strawberry.field(description="Курсор першого елемента на поточній сторінці.")
    end_cursor: Optional[str] = strawberry.field(description="Курсор останнього елемента на поточній сторінці.")

# Можна додати інші базові типи або інтерфейси тут.
# Наприклад, інтерфейс для об'єктів з полями created_at/updated_at:

@strawberry.interface
class TimestampsInterface:
    """
    Інтерфейс для об'єктів, що мають позначки часу створення та оновлення.
    """
    created_at: datetime = strawberry.field(description="Час створення об'єкта.")
    updated_at: datetime = strawberry.field(description="Час останнього оновлення об'єкта.")

# Приклад загального Enum, якщо він не прив'язаний до конкретної моделі
@strawberry.enum
class SortDirection(str):
    """Напрямок сортування."""
    ASC = "ASC"
    DESC = "DESC"

# TODO: Розглянути необхідність інших базових елементів.
# Наприклад, Connection та Edge типи для Relay-сумісної пагінації,
# але Strawberry може надавати свої утиліти для цього (наприклад, strawberry.relay).

# Експорт визначених типів для використання в інших модулях GraphQL
__all__ = [
    "Node",
    "PageInfo",
    "TimestampsInterface",
    "SortDirection",
    # "GraphQLID", # Якщо використовується кастомний скаляр
]
