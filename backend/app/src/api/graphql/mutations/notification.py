# backend/app/src/api/graphql/mutations/notification.py
# -*- coding: utf-8 -*-
"""
GraphQL мутації (Mutations), пов'язані зі сповіщеннями.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.notification import (
    NotificationType, NotificationSettingsType,
    MarkNotificationsAsReadInput, NotificationSettingsUpdateInput
)
# TODO: Імпортувати сервіси
# from backend.app.src.services.notifications.notification_service import NotificationService
# from backend.app.src.services.notifications.user_notification_settings_service import UserNotificationSettingsService
# from backend.app.src.core.dependencies import get_current_active_user

@strawberry.type
class NotificationMutations:
    """
    Клас, що групує GraphQL мутації для управління сповіщеннями та їх налаштуваннями.
    """

    @strawberry.mutation(description="Позначити сповіщення як прочитані.")
    async def mark_notifications_as_read(self, info: strawberry.Info, input: MarkNotificationsAsReadInput) -> bool: # Або повернути список оновлених NotificationType
        """
        Позначає вказані сповіщення (за їх ID) або всі непрочитані сповіщення
        поточного користувача як прочитані. Повертає True у разі успіху.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова.")
        #
        # notification_service = NotificationService(context.db_session)
        #
        # if input.mark_all_as_read == True: # Явна перевірка на True
        #     await notification_service.mark_all_user_notifications_as_read(user_id=current_user.id)
        # elif input.notification_ids is not strawberry.UNSET and input.notification_ids:
        #     # Розкодувати strawberry.ID в int, якщо потрібно
        #     db_ids = [Node.decode_id_to_int(nid, "NotificationType") for nid in input.notification_ids]
        #     await notification_service.mark_notifications_as_read_by_ids(
        #         user_id=current_user.id, notification_ids=db_ids
        #     )
        # else:
        #     # Нічого не передано для позначення
        #     return False # Або кинути помилку
        # return True
        raise NotImplementedError("Позначення сповіщень як прочитаних ще не реалізовано.")

    @strawberry.mutation(description="Оновити налаштування сповіщень поточного користувача.")
    async def update_my_notification_settings(self, info: strawberry.Info, input: NotificationSettingsUpdateInput) -> Optional[NotificationSettingsType]:
        """
        Оновлює персональні налаштування сповіщень для поточного користувача.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова.")
        #
        # settings_service = UserNotificationSettingsService(context.db_session) # Потрібен реальний сервіс
        # updated_settings_model = await settings_service.update_user_notification_settings_graphql(
        #     user_id=current_user.id,
        #     settings_input=input
        # )
        # return NotificationSettingsType.from_pydantic(updated_settings_model) if updated_settings_model else None
        raise NotImplementedError("Оновлення налаштувань сповіщень ще не реалізовано.")

    # TODO: Мутації для адміністративного управління шаблонами сповіщень (CRUD),
    # якщо це потрібно в GraphQL API (зазвичай це робиться через REST API супер-адміном).
    # Якщо так, то потрібні відповідні Input типи та захист прав доступу.

# Експорт класу для агрегації в mutations/__init__.py
__all__ = [
    "NotificationMutations",
]
