# backend/app/src/api/graphql/types/gamification.py
# -*- coding: utf-8 -*-
"""
GraphQL типи, пов'язані з гейміфікацією (рівні, бейджі, досягнення, рейтинги).
"""

import strawberry
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from backend.app.src.api.graphql.types.base import Node, TimestampsInterface

if TYPE_CHECKING:
    from backend.app.src.api.graphql.types.user import UserType
    from backend.app.src.api.graphql.types.group import GroupType


@strawberry.type
class LevelDefinitionType(Node, TimestampsInterface): # Раніше називався LevelSchema в REST, тут LevelDefinitionType для розрізнення з UserLevelType
    """
    GraphQL тип для визначення (налаштування) рівня в групі.
    """
    id: strawberry.ID
    group: "GroupType" = strawberry.field(description="Група, до якої належить це налаштування рівня.")
    name: str = strawberry.field(description="Назва рівня (наприклад, 'Новачок', 'Експерт').")
    level_number: int = strawberry.field(description="Порядковий номер рівня (1, 2, 3...).")
    required_score: int = strawberry.field(description="Кількість очок/бонусів, необхідних для досягнення цього рівня.")
    description: Optional[str] = strawberry.field(description="Опис рівня.")
    icon_url: Optional[str] = strawberry.field(description="URL іконки для цього рівня.")
    created_at: datetime
    updated_at: datetime
    # db_id: strawberry.Private[int]


@strawberry.type
class UserLevelType(Node, TimestampsInterface): # Це може бути UserLevelProgressType
    """
    GraphQL тип, що представляє поточний рівень користувача в групі та його прогрес.
    """
    id: strawberry.ID # Може бути ID запису UserGroupLevel або просто user_id+group_id
    user: "UserType" = strawberry.field(description="Користувач.")
    group: "GroupType" = strawberry.field(description="Група, в якій досягнуто рівень.")
    current_level: Optional[LevelDefinitionType] = strawberry.field(description="Поточне визначення рівня користувача.")
    current_score: int = strawberry.field(description="Поточна кількість очок/бонусів користувача в групі.")
    next_level: Optional[LevelDefinitionType] = strawberry.field(description="Наступне визначення рівня (якщо є).")
    progress_to_next_level_percent: Optional[float] = strawberry.field(description="Прогрес до наступного рівня у відсотках (0-100).")
    # achieved_at: datetime # Час досягнення поточного рівня
    created_at: datetime # Час створення запису про рівень користувача
    updated_at: datetime # Час останнього оновлення прогресу/рівня
    # db_id: strawberry.Private[int]


@strawberry.type
class BadgeType(Node, TimestampsInterface):
    """
    GraphQL тип для визначення (шаблону) бейджа.
    """
    id: strawberry.ID
    group: "GroupType" = strawberry.field(description="Група, до якої належить цей бейдж.")
    name: str = strawberry.field(description="Назва бейджа.")
    description: str = strawberry.field(description="Опис бейджа та умов його отримання.")
    icon_url: Optional[str] = strawberry.field(description="URL іконки бейджа.")
    # criteria: Optional[str] # Може бути текстовий опис або структуровані дані
    is_active: bool = strawberry.field(description="Чи активний бейдж для отримання.")
    created_at: datetime
    updated_at: datetime
    # db_id: strawberry.Private[int]


@strawberry.type
class UserAchievementType(Node, TimestampsInterface): # Представляє отриманий користувачем бейдж
    """
    GraphQL тип, що представляє досягнення користувача (отриманий бейдж).
    """
    id: strawberry.ID # ID запису про досягнення
    user: "UserType" = strawberry.field(description="Користувач, що отримав досягнення.")
    badge: BadgeType = strawberry.field(description="Бейдж, який було отримано.")
    group: "GroupType" = strawberry.field(description="Група, в якій було отримано досягнення.")
    achieved_at: datetime = strawberry.field(description="Час отримання досягнення.")
    # notes: Optional[str] # Якщо є якісь нотатки до конкретного досягнення
    created_at: datetime # Технічне поле
    updated_at: datetime # Технічне поле
    # db_id: strawberry.Private[int]


@strawberry.type
class UserGroupRatingEntryType: # Не є Node, бо це запис в рейтингу, а не окрема сутність
    """
    GraphQL тип для одного запису в рейтингу користувачів групи.
    """
    user: "UserType" = strawberry.field(description="Користувач.")
    rank: int = strawberry.field(description="Позиція користувача в рейтингу.")
    score: float = strawberry.field(description="Показник користувача (наприклад, кількість бонусів, виконаних завдань).")
    # group: "GroupType" # Зазвичай рейтинг отримується в контексті групи, тому це поле може бути зайвим тут

# --- Вхідні типи (Input Types) для мутацій ---
# Зазвичай, для гейміфікації мутації стосуються налаштувань (адміном),
# а самі рівні/бейджі присвоюються автоматично сервісами.

@strawberry.input
class LevelDefinitionCreateInput:
    group_id: strawberry.ID
    name: str
    level_number: int
    required_score: int
    description: Optional[str] = strawberry.UNSET
    icon_url: Optional[str] = strawberry.UNSET

@strawberry.input
class LevelDefinitionUpdateInput:
    name: Optional[str] = strawberry.UNSET
    level_number: Optional[int] = strawberry.UNSET
    required_score: Optional[int] = strawberry.UNSET
    description: Optional[str] = strawberry.UNSET
    icon_url: Optional[str] = strawberry.UNSET

@strawberry.input
class BadgeCreateInput:
    group_id: strawberry.ID
    name: str
    description: str
    icon_url: Optional[str] = strawberry.UNSET
    # criteria: Optional[str] = strawberry.UNSET
    is_active: Optional[bool] = strawberry.UNSET

@strawberry.input
class BadgeUpdateInput:
    name: Optional[str] = strawberry.UNSET
    description: Optional[str] = strawberry.UNSET
    icon_url: Optional[str] = strawberry.UNSET
    # criteria: Optional[str] = strawberry.UNSET
    is_active: Optional[bool] = strawberry.UNSET


__all__ = [
    "LevelDefinitionType",
    "UserLevelType",
    "BadgeType",
    "UserAchievementType",
    "UserGroupRatingEntryType",
    "LevelDefinitionCreateInput",
    "LevelDefinitionUpdateInput",
    "BadgeCreateInput",
    "BadgeUpdateInput",
]
