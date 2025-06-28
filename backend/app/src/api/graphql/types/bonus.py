# backend/app/src/api/graphql/types/bonus.py
# -*- coding: utf-8 -*-
"""
GraphQL типи, пов'язані з бонусами, рахунками та нагородами.
"""

import strawberry
from typing import Optional, List, TYPE_CHECKING, NewType, Annotated
from datetime import datetime
import uuid

from backend.app.src.api.graphql.types.base import Node, TimestampsInterface

if TYPE_CHECKING:
    from backend.app.src.api.graphql.types.user import UserType
    from backend.app.src.api.graphql.types.group import GroupType
    from backend.app.src.api.graphql.types.task import TaskType # Якщо бонус пов'язаний із завданням

# GraphQL Enum для типу транзакції
@strawberry.enum
class TransactionTypeEnum(str):
    """Тип бонусної транзакції."""
    TASK_COMPLETION = "TASK_COMPLETION" # Нарахування за завдання
    REWARD_REDEMPTION = "REWARD_REDEMPTION" # Списання за нагороду
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT" # Ручне коригування адміном
    THANK_YOU_BONUS_SENT = "THANK_YOU_BONUS_SENT" # Подяка відправлена
    THANK_YOU_BONUS_RECEIVED = "THANK_YOU_BONUS_RECEIVED" # Подяка отримана
    PENALTY = "PENALTY" # Штраф
    INITIAL_BALANCE = "INITIAL_BALANCE" # Початковий баланс (якщо є)
    OTHER = "OTHER" # Інше


@strawberry.type
class UserAccountType(Node, TimestampsInterface):
    """GraphQL тип для бонусного рахунку користувача в групі."""
    id: strawberry.ID
    user: "UserType" = strawberry.field(description="Користувач, якому належить рахунок.")
    group: "GroupType" = strawberry.field(description="Група, до якої прив'язаний рахунок.")
    balance: float = strawberry.field(description="Поточний баланс бонусів на рахунку.")
    currency_name: Optional[str] = strawberry.field(description="Назва валюти бонусів (з налаштувань групи).")
    created_at: datetime
    updated_at: datetime

    # @strawberry.field
    # async def transactions(self, info: strawberry.Info, first: Optional[int] = 10, after: Optional[str] = None) -> "TransactionConnection": # Приклад Relay-пагінації
    #     """Історія транзакцій по цьому рахунку."""
    #     # TODO: Реалізувати резолвер з пагінацією
    #     pass
    # db_id: strawberry.Private[int]


@strawberry.type
class AccountTransactionType(Node, TimestampsInterface):
    """GraphQL тип для транзакції по бонусному рахунку."""
    id: strawberry.ID
    account: UserAccountType = strawberry.field(description="Рахунок, до якого відноситься транзакція.")
    transaction_type: TransactionTypeEnum = strawberry.field(description="Тип транзакції.")
    amount: float = strawberry.field(description="Сума транзакції (додатня для нарахування, від'ємна для списання).")
    balance_after_transaction: Optional[float] = strawberry.field(description="Баланс рахунку після цієї транзакції.")
    description: Optional[str] = strawberry.field(description="Опис транзакції.")
    related_task: Optional["TaskType"] = strawberry.field(description="Завдання, пов'язане з транзакцією (якщо є).")
    related_reward: Optional["RewardType"] = strawberry.field(description="Нагорода, пов'язана з транзакцією (якщо є).")
    actor: Optional["UserType"] = strawberry.field(description="Користувач, що ініціював транзакцію (напр. адмін для ручного коригування, або система).")
    created_at: datetime
    updated_at: datetime # Може не оновлюватися
    # db_id: strawberry.Private[int]


@strawberry.type
class RewardType(Node, TimestampsInterface):
    """GraphQL тип для нагороди, яку можна отримати за бонуси."""
    id: strawberry.ID
    name: str = strawberry.field(description="Назва нагороди.")
    description: Optional[str] = strawberry.field(description="Опис нагороди.")
    group: "GroupType" = strawberry.field(description="Група, в якій доступна нагорода.")
    cost: float = strawberry.field(description="Вартість нагороди в бонусах.")
    icon_url: Optional[str] = strawberry.field(description="URL іконки нагороди.")
    # Тип нагороди: разовий, обмежена кількість, постійний
    # reward_availability_type: str = strawberry.field(description="Тип доступності: 'SINGLE_USE', 'LIMITED', 'PERMANENT'.")
    quantity_available: Optional[int] = strawberry.field(description="Кількість доступних нагород (для типу 'LIMITED').")
    is_active: bool = strawberry.field(description="Чи активна нагорода для отримання.")
    created_at: datetime
    updated_at: datetime
    # db_id: strawberry.Private[int]


# --- Вхідні типи (Input Types) для мутацій ---

@strawberry.input
class RedeemRewardInput:
    """Вхідні дані для отримання (покупки) нагороди."""
    reward_id: strawberry.ID # ID нагороди, яку користувач хоче отримати

@strawberry.input
class ThankYouBonusInput:
    """Вхідні дані для надсилання "подяки" (бонусів) іншому користувачу."""
    recipient_user_id: strawberry.ID # ID користувача-отримувача
    group_id: strawberry.ID # ID групи, в контексті якої відбувається подяка
    amount: float # Сума подяки
    message: Optional[str] = strawberry.UNSET

@strawberry.input
class ManualAdjustmentInput:
    """Вхідні дані для ручного коригування балансу користувача адміном групи."""
    user_id: strawberry.ID # ID користувача, чий баланс коригується
    group_id: strawberry.ID # ID групи
    amount: float # Сума коригування (може бути від'ємною для списання)
    description: str # Обов'язковий опис причини коригування


__all__ = [
    "TransactionTypeEnum",
    "UserAccountType",
    "AccountTransactionType",
    "RewardType",
    "RedeemRewardInput",
    "ThankYouBonusInput",
    "ManualAdjustmentInput",
]
