# backend/app/src/api/graphql/types/notification.py
# -*- coding: utf-8 -*-
"""
GraphQL типи, пов'язані зі сповіщеннями.
"""

import strawberry
from typing import Optional, List, TYPE_CHECKING, Dict, Any
from datetime import datetime

from backend.app.src.api.graphql.types.base import Node, TimestampsInterface

if TYPE_CHECKING:
    from backend.app.src.api.graphql.types.user import UserType
    # from backend.app.src.api.graphql.types.group import GroupType # Якщо сповіщення прив'язане до групи
    # from backend.app.src.api.graphql.types.task import TaskType # Якщо сповіщення про завдання

# GraphQL Enum для типу каналу сповіщення
@strawberry.enum
class NotificationChannelEnum(str):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH" # Firebase, APNS
    MESSENGER = "MESSENGER" # Telegram, Slack etc.

# GraphQL Enum для типу самого сповіщення (події, що його викликала)
@strawberry.enum
class NotificationTypeEnum(str):
    """Тип події, що викликала сповіщення."""
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_STATUS_CHANGED = "TASK_STATUS_CHANGED"
    TASK_COMPLETED_FOR_REVIEW = "TASK_COMPLETED_FOR_REVIEW" # Завдання виконано, потребує перевірки
    TASK_VERIFIED_COMPLETED = "TASK_VERIFIED_COMPLETED" # Виконання підтверджено
    TASK_VERIFIED_REJECTED = "TASK_VERIFIED_REJECTED" # Виконання відхилено
    TASK_DEADLINE_SOON = "TASK_DEADLINE_SOON"
    TASK_OVERDUE = "TASK_OVERDUE"
    BONUS_TRANSACTION = "BONUS_TRANSACTION" # Нарахування/списання бонусів
    REWARD_REDEEMED = "REWARD_REDEEMED"
    NEW_BADGE_ACHIEVED = "NEW_BADGE_ACHIEVED"
    LEVEL_UP = "LEVEL_UP"
    GROUP_INVITATION = "GROUP_INVITATION"
    USER_JOINED_GROUP = "USER_JOINED_GROUP"
    USER_LEFT_GROUP = "USER_LEFT_GROUP"
    NEW_POLL_IN_GROUP = "NEW_POLL_IN_GROUP"
    SYSTEM_MESSAGE = "SYSTEM_MESSAGE" # Загальне системне сповіщення
    CUSTOM_ADMIN_MESSAGE = "CUSTOM_ADMIN_MESSAGE" # Повідомлення від адміна групи
    THANK_YOU_BONUS_RECEIVED = "THANK_YOU_BONUS_RECEIVED"
    # ... інші типи ...

@strawberry.type
class NotificationType(Node, TimestampsInterface):
    """
    GraphQL тип для сповіщення користувача.
    """
    id: strawberry.ID
    recipient: "UserType" = strawberry.field(description="Отримувач сповіщення.")

    title: Optional[str] = strawberry.field(description="Заголовок сповіщення (якщо є).")
    message: str = strawberry.field(description="Текст сповіщення.")
    notification_type: NotificationTypeEnum = strawberry.field(description="Тип події, що викликала сповіщення.")

    is_read: bool = strawberry.field(description="Чи прочитано сповіщення користувачем.")
    read_at: Optional[datetime] = strawberry.field(description="Час, коли сповіщення було прочитано.")

    # Поля для зв'язку з сутностями, що викликали сповіщення
    related_entity_type: Optional[str] = strawberry.field(description="Тип пов'язаної сутності (напр., 'Task', 'Group', 'User').")
    related_entity_id: Optional[strawberry.ID] = strawberry.field(description="ID пов'язаної сутності.")

    # Додаткові дані у форматі JSON, якщо потрібно передати щось специфічне для типу сповіщення
    # Наприклад, для TASK_COMPLETED_FOR_REVIEW може містити task_name, user_who_completed_name
    # Використовуємо strawberry.JSON (який є псевдонімом для Dict[str, Any])
    additional_data: Optional[strawberry.JSON] = strawberry.field(description="Додаткові дані, специфічні для типу сповіщення.")

    # @strawberry.field
    # async def related_object(self, info: strawberry.Info) -> Optional[Node]: # Або Union з можливими типами
    #     """Пов'язаний об'єкт (завдання, група тощо). Потребує резолвера."""
    #     # TODO: Реалізувати резолвер для отримання пов'язаного об'єкта
    #     # на основі related_entity_type та related_entity_id.
    #     # Потрібен доступ до відповідних даталоадерів.
    #     pass

    created_at: datetime
    updated_at: datetime # Може оновлюватися при зміні is_read
    # db_id: strawberry.Private[int]


@strawberry.type
class NotificationSettingsType:
    """
    GraphQL тип для налаштувань сповіщень користувача.
    """
    user_id: strawberry.ID # ID користувача, до якого відносяться налаштування
    # Приклад налаштувань (потрібно узгодити з NotificationSettingsSchema в REST API)
    email_notifications_enabled: bool = strawberry.field(description="Чи увімкнені email сповіщення загалом.")
    in_app_notifications_enabled: bool = strawberry.field(description="Чи увімкнені внутрішньо-додаткові сповіщення.")

    # Детальні налаштування за типами подій та каналами
    # Наприклад, для кожного NotificationTypeEnum можна мати налаштування для кожного NotificationChannelEnum
    # Це може бути складна структура (наприклад, List[NotificationChannelSetting])
    # Або простіші булеві поля:
    notify_on_task_completed_email: bool = strawberry.field(description="Сповіщати по email про виконання завдання.")
    notify_on_task_completed_in_app: bool = strawberry.field(description="Сповіщати в додатку про виконання завдання.")
    # ... і так далі для інших типів та каналів ...

    # Для прикладу, зробимо простіше:
    task_updates_via_email: bool = strawberry.field(description="Отримувати оновлення по завданнях на email.")
    task_updates_via_in_app: bool = strawberry.field(description="Отримувати оновлення по завданнях в додатку.")
    bonus_changes_via_email: bool = strawberry.field(description="Отримувати сповіщення про зміни бонусів на email.")
    bonus_changes_via_in_app: bool = strawberry.field(description="Отримувати сповіщення про зміни бонусів в додатку.")
    # ...
    updated_at: datetime = strawberry.field(description="Час останнього оновлення налаштувань.")


# --- Вхідні типи (Input Types) для мутацій ---

@strawberry.input
class MarkNotificationsAsReadInput:
    """Вхідні дані для позначення сповіщень як прочитаних."""
    notification_ids: Optional[List[strawberry.ID]] = strawberry.UNSET # Список ID сповіщень
    mark_all_as_read: Optional[bool] = strawberry.UNSET # Позначити всі як прочитані

@strawberry.input
class NotificationSettingsUpdateInput:
    """Вхідні дані для оновлення налаштувань сповіщень."""
    # Поля мають відповідати полям в NotificationSettingsType, але бути опціональними
    email_notifications_enabled: Optional[bool] = strawberry.UNSET
    in_app_notifications_enabled: Optional[bool] = strawberry.UNSET
    task_updates_via_email: Optional[bool] = strawberry.UNSET
    task_updates_via_in_app: Optional[bool] = strawberry.UNSET
    bonus_changes_via_email: Optional[bool] = strawberry.UNSET
    bonus_changes_via_in_app: Optional[bool] = strawberry.UNSET
    # ... і так далі ...

__all__ = [
    "NotificationChannelEnum",
    "NotificationTypeEnum",
    "NotificationType",
    "NotificationSettingsType",
    "MarkNotificationsAsReadInput",
    "NotificationSettingsUpdateInput",
]
