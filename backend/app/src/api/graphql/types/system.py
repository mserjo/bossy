# backend/app/src/api/graphql/types/system.py
# -*- coding: utf-8 -*-
"""
GraphQL типи, пов'язані з системними налаштуваннями, станом та іншою системною інформацією.
"""

import strawberry
from typing import Optional, List, Any
from datetime import datetime

from backend.app.src.api.graphql.types.base import Node, TimestampsInterface

@strawberry.type
class SystemSettingType: # Не успадковує Node, якщо налаштування ідентифікуються за унікальним ім'ям/кодом
    """GraphQL тип для одного системного налаштування."""
    name: str = strawberry.field(description="Унікальна назва (ключ) налаштування.")
    value: strawberry.JSON = strawberry.field(description="Значення налаштування (може бути будь-якого JSON-сумісного типу).")
    description: Optional[str] = strawberry.field(description="Опис налаштування.")
    # category: Optional[str] = strawberry.field(description="Категорія налаштування для групування.")
    # is_editable_by_superuser: bool = strawberry.field(description="Чи може суперюзер змінювати це налаштування через API.")
    updated_at: datetime = strawberry.field(description="Час останнього оновлення налаштування.")


@strawberry.type
class HealthStatusType:
    """GraphQL тип для статусу компонента системи."""
    service_name: str = strawberry.field(description="Назва сервісу/компонента.")
    status: str = strawberry.field(description="Статус (напр., 'OK', 'WARN', 'ERROR', 'UNKNOWN').")
    message: Optional[str] = strawberry.field(description="Додаткове повідомлення про стан.")
    details: Optional[strawberry.JSON] = strawberry.field(description="Деталізована інформація (напр., час відповіді).")

@strawberry.type
class SystemHealthType:
    """GraphQL тип для загального стану здоров'я системи."""
    overall_status: str = strawberry.field(description="Загальний статус системи.")
    api_status: HealthStatusType = strawberry.field(description="Статус API.")
    database_status: HealthStatusType = strawberry.field(description="Статус бази даних.")
    # TODO: Додати статуси інших важливих компонентів (Redis, Celery, зовнішні сервіси)
    # redis_status: Optional[HealthStatusType]
    # celery_status: Optional[HealthStatusType]
    checked_at: datetime = strawberry.field(description="Час останньої перевірки стану.")


# --- Вхідні типи (Input Types) для мутацій ---

@strawberry.input
class SystemSettingUpdateInput:
    """Вхідні дані для оновлення системного налаштування."""
    # name: str # Зазвичай передається як аргумент мутації, а не в інпуті
    value: strawberry.JSON # Нове значення налаштування


__all__ = [
    "SystemSettingType",
    "HealthStatusType",
    "SystemHealthType",
    "SystemSettingUpdateInput",
]
