# backend/app/src/api/graphql/types/group.py
# -*- coding: utf-8 -*-
"""
GraphQL типи, пов'язані з групами.

Цей модуль визначає GraphQL типи для сутності "Група",
включаючи об'єктний тип `GroupType`, вхідні типи для мутацій
(наприклад, `GroupCreateInput`, `GroupUpdateInput`), та будь-які
пов'язані типи (наприклад, `GroupMembershipType`, `GroupSettingsType`).
"""

import strawberry
from typing import Optional, List, TYPE_CHECKING, NewType, Annotated
from datetime import datetime
import uuid

# Імпорт базових типів/інтерфейсів
from backend.app.src.api.graphql.types.base import Node, TimestampsInterface

if TYPE_CHECKING:
    # Уникнення циклічних залежностей
    from backend.app.src.api.graphql.types.user import UserType, UserRoleType
    from backend.app.src.api.graphql.types.task import TaskType # Якщо завдання є полем групи
    from backend.app.src.api.graphql.types.bonuses import RewardType # Якщо нагороди є полем групи
    # ... та інші типи, що можуть бути полями GroupType

# GraphQL Enum для типів груп (якщо вони визначені як Enum)
# Або це може бути окремий GraphQL тип GroupTypeType, якщо типи груп - це довідник.
# Припустимо, що це довідник, і тип буде визначено в dictionary.py
# from .dictionary import GroupTypeType # Приклад

@strawberry.type
class GroupSettingsType(TimestampsInterface):
    """GraphQL тип для налаштувань групи."""
    # id: strawberry.ID # Якщо налаштування мають свій ID
    currency_name: str = strawberry.field(description="Назва валюти бонусів у групі (наприклад, 'бали', 'зірочки').")
    allow_negative_balance: bool = strawberry.field(description="Чи дозволений негативний баланс бонусів.")
    max_debt_amount: Optional[float] = strawberry.field(description="Максимально допустима сума боргу (якщо allow_negative_balance=True).")
    # TODO: Додати інші налаштування групи згідно `technical-task.md`
    # (бонуси цілі чи дробові, ієрархія груп (якщо це налаштування), тощо)
    created_at: datetime
    updated_at: datetime


@strawberry.type
class GroupMembershipType(Node, TimestampsInterface):
    """
    GraphQL тип, що представляє членство користувача в групі, включаючи його роль.
    """
    id: strawberry.ID # ID запису про членство
    user: "UserType" = strawberry.field(description="Користувач, що є членом групи.")
    # group: "GroupType" # Зазвичай не потрібно, бо отримується в контексті групи
    role: "UserRoleType" = strawberry.field(description="Роль користувача в цій групі.") # Використовуємо UserRoleType з user.py
    joined_at: datetime = strawberry.field(description="Час приєднання до групи.")
    created_at: datetime
    updated_at: datetime
    # TODO: Додати резолвери, якщо поля не мапляться напряму.


@strawberry.type
class GroupType(Node, TimestampsInterface):
    """
    GraphQL тип, що представляє групу.
    """
    id: strawberry.ID
    name: str = strawberry.field(description="Назва групи.")
    description: Optional[str] = strawberry.field(description="Опис групи.")
    # group_type: Optional["GroupTypeType"] = strawberry.field(description="Тип групи (з довідника).") # TODO: Визначити GroupTypeType
    icon_url: Optional[str] = strawberry.field(description="URL іконки групи.")

    owner: Optional["UserType"] = strawberry.field(description="Власник (засновник) групи.") # Може бути актуально, якщо це не просто адмін

    created_at: datetime
    updated_at: datetime

    # Поля, що потребують резолверів
    @strawberry.field
    async def settings(self, info: strawberry.Info) -> Optional[GroupSettingsType]:
        """Налаштування цієї групи."""
        # TODO: Реалізувати резолвер для отримання налаштувань групи
        # db_id = self.db_id # Якщо є приватне поле для ID з БД
        # return await info.context.dataloaders.group_settings_by_group_id.load(db_id)
        return GroupSettingsType(currency_name="Заглушка Бали", allow_negative_balance=True, max_debt_amount=0, created_at=datetime.now(), updated_at=datetime.now()) # Заглушка

    @strawberry.field
    async def members(self, info: strawberry.Info, role_code: Optional[str] = None) -> List[GroupMembershipType]:
        """Список учасників групи, опціонально відфільтрований за кодом ролі."""
        # TODO: Реалізувати резолвер
        # db_id = self.db_id
        # return await info.context.dataloaders.group_members_by_group_id.load((db_id, role_code))
        return [] # Заглушка

    @strawberry.field
    async def member_count(self, info: strawberry.Info) -> int:
        """Кількість учасників у групі."""
        # TODO: Реалізувати резолвер
        return 0 # Заглушка

    # TODO: Додати поля для зв'язків: завдання, нагороди, опитування, команди тощо, що належать цій групі.
    # @strawberry.field
    # async def tasks(self, info: strawberry.Info, active_only: bool = True) -> List["TaskType"]:
    #     pass

    # @strawberry.field
    # async def rewards(self, info: strawberry.Info, active_only: bool = True) -> List["RewardType"]:
    #     pass

    # db_id: strawberry.Private[int] # ID з бази даних


# --- Вхідні типи (Input Types) для мутацій ---

@strawberry.input
class GroupCreateInput:
    """Вхідні дані для створення нової групи."""
    name: str
    description: Optional[str] = strawberry.UNSET
    # group_type_code: Optional[str] = strawberry.UNSET # Код типу групи з довідника
    icon_url: Optional[str] = strawberry.UNSET # Може бути URL або обробка завантаження файлу
    # TODO: Додати поля для початкових налаштувань групи, якщо вони встановлюються при створенні

@strawberry.input
class GroupUpdateInput:
    """Вхідні дані для оновлення існуючої групи."""
    name: Optional[str] = strawberry.UNSET
    description: Optional[str] = strawberry.UNSET
    # group_type_code: Optional[str] = strawberry.UNSET
    icon_url: Optional[str] = strawberry.UNSET

@strawberry.input
class GroupSettingsUpdateInput:
    """Вхідні дані для оновлення налаштувань групи."""
    currency_name: Optional[str] = strawberry.UNSET
    allow_negative_balance: Optional[bool] = strawberry.UNSET
    max_debt_amount: Optional[float] = strawberry.UNSET
    # TODO: Додати інші налаштування

@strawberry.input
class GroupMemberAddInput:
    """Вхідні дані для додавання учасника до групи."""
    user_id: strawberry.ID # ID користувача, якого додають
    role_code: str # Код ролі, яку призначають користувачу в групі (напр. 'user', 'group_admin')

@strawberry.input
class GroupMemberUpdateRoleInput:
    """Вхідні дані для оновлення ролі учасника в групі."""
    user_id: strawberry.ID # ID користувача, чию роль оновлюють
    new_role_code: str # Новий код ролі

@strawberry.input
class GroupInviteInput:
    """Вхідні дані для створення запрошення до групи (може бути email або інші параметри)."""
    # Залежить від реалізації запрошень (email, посилання тощо)
    email_to_invite: Optional[strawberry.scalars.Email] = strawberry.UNSET # Якщо запрошуємо по email
    # Або параметри для генерації унікального посилання
    expires_in_days: Optional[int] = strawberry.UNSET # Термін дії запрошення


# Експорт визначених типів
__all__ = [
    "GroupSettingsType",
    "GroupMembershipType",
    "GroupType",
    "GroupCreateInput",
    "GroupUpdateInput",
    "GroupSettingsUpdateInput",
    "GroupMemberAddInput",
    "GroupMemberUpdateRoleInput",
    "GroupInviteInput",
]
