# backend/app/src/api/graphql/subscriptions/notification.py
# -*- coding: utf-8 -*-
"""
GraphQL підписки (Subscriptions), пов'язані зі сповіщеннями.
"""

import strawberry
from typing import AsyncGenerator, Optional

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.notification import NotificationType

# TODO: Імпортувати сервіси або механізми для роботи з Pub/Sub (наприклад, Redis)
# from backend.app.src.services.notifications.subscription_manager import NotificationSubscriptionManager
# from backend.app.src.core.dependencies import get_current_active_user # Для ідентифікації користувача

@strawberry.type
class NotificationSubscriptions:
    """
    Клас, що групує GraphQL підписки на сповіщення.
    """

    @strawberry.subscription(description="Підписатися на нові сповіщення для поточного користувача.")
    async def new_notifications_for_user(self, info: strawberry.Info) -> AsyncGenerator[NotificationType, None]:
        """
        Асинхронний генератор, що надсилає нові сповіщення поточному користувачу
        в реальному часі, як тільки вони з'являються.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     # GraphQL зазвичай не дозволяє кидати винятки в підписках таким чином,
        #     # або це потрібно обробляти на рівні WebSocket з'єднання / протоколу.
        #     # Краще просто завершити генератор, якщо користувач не автентифікований.
        #     # Hoặc Strawberry може мати свій механізм обробки прав для підписок.
        #     yield # Просто щоб зробити тип валідним, але нічого не надішле
        #     return
        #
        # user_id = current_user.id
        # # logger.info(f"User {user_id} subscribed to new notifications.") # Потрібен logger
        #
        # # Приклад з використанням уявного NotificationSubscriptionManager
        # # manager = NotificationSubscriptionManager(context.redis) # Або інший Pub/Sub
        # # async for notification_data in manager.subscribe_to_user_notifications(user_id):
        # #     # notification_data - це дані, з яких можна створити NotificationType
        # #     # Наприклад, Pydantic модель або dict
        # #     yield NotificationType.from_pydantic(notification_data) # Або from_dict
        #
        # # Заглушка: імітація надходження сповіщень
        # import asyncio
        # from datetime import datetime
        # from backend.app.src.api.graphql.types.notification import NotificationTypeEnum
        # from backend.app.src.api.graphql.types.user import UserType # Для заглушки recipient
        #
        # recipient_stub = UserType(id=strawberry.ID(str(user_id)), email="stub@example.com", is_active=True, is_superuser=False, created_at=datetime.utcnow(), updated_at=datetime.utcnow())

        # count = 0
        # while True: # У реальному житті цикл керується менеджером підписок
        #     await asyncio.sleep(5) # Імітуємо очікування нового сповіщення
        #     count += 1
        #     yield NotificationType(
        #         id=strawberry.ID(f"NotifStub:{count}"),
        #         recipient=recipient_stub, # Потрібно передати реального користувача або його ID
        #         message=f"Тестове сповіщення #{count} для користувача {user_id}.",
        #         notification_type=NotificationTypeEnum.SYSTEM_MESSAGE,
        #         is_read=False,
        #         read_at=None,
        #         created_at=datetime.utcnow(),
        #         updated_at=datetime.utcnow(),
        #         related_entity_id=None,
        #         related_entity_type=None,
        #         additional_data=None
        #     )
        #     if count >= 3: # Обмеження для заглушки
        #         # logger.info(f"User {user_id} unsubscribed from notifications (stub limit).")
        #         break
        if False: # Щоб зробити тип AsyncGenerator[NotificationType, None] валідним
            yield # pragma: no cover
        raise NotImplementedError("Підписка на сповіщення ще не реалізована.")


# Експорт класу для агрегації в subscriptions/__init__.py
__all__ = [
    "NotificationSubscriptions",
]
