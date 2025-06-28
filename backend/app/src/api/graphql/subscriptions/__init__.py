# backend/app/src/api/graphql/subscriptions/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'subscriptions' GraphQL API.

Цей пакет відповідає за визначення кореневого типу `Subscription` та всіх
резолверів для полів цього типу, якщо GraphQL підписки використовуються в проекті.
Підписки дозволяють клієнтам отримувати оновлення даних в реальному часі.

Резолвери для логічно пов'язаних підписок можуть групуватися в окремі
файли всередині цього пакету (наприклад, `notification.py`, `task.py`).
Ці файли зазвичай визначають класи, які містять асинхронні генератори,
декоровані `@strawberry.subscription`.

Цей `__init__.py` файл імпортує ці класи-частини та об'єднує їх
в єдиний клас `Subscription`, який потім експортується для використання
в `graphql/schema.py`.

Якщо підписки не використовуються, цей пакет може бути порожнім,
а клас `Subscription` не експортується або експортується як `None`.
"""

import strawberry
from typing import AsyncGenerator # Потрібно для анотації типів підписок Strawberry
import asyncio # Для прикладу в заглушці

# TODO: Імпортувати класи з полями Subscription з відповідних файлів цього пакету,
# якщо підписки реалізовані.
# from backend.app.src.api.graphql.subscriptions.notification import NotificationSubscriptions
# from backend.app.src.api.graphql.subscriptions.task import TaskSubscriptions

# --- Заглушка для класу Subscription ---
@strawberry.type
class Subscription:
    """
    Кореневий GraphQL тип для підписок (Subscriptions).
    Об'єднує всі доступні підписки для отримання даних в реальному часі.
    Якщо підписки не використовуються, це поле може бути відсутнім у схемі.
    """
    @strawberry.subscription
    async def placeholder_subscription(self, entity_id: strawberry.ID) -> AsyncGenerator[str, None]:
        """
        Заглушка для поля підписки.
        Демонструє, як може виглядати підписка.
        В реальному житті, тут буде логіка прослуховування подій
        (наприклад, з Redis Pub/Sub, Kafka, або внутрішніх подій системи)
        та асинхронного надсилання даних клієнту.
        """
        for i in range(3):
            await asyncio.sleep(1) # Імітація затримки або очікування події
            yield f"Оновлення для сутності {entity_id}: Подія номер {i+1}"
        # Якщо підписки не використовуються активно, але поле Subscription існує,
        # можна зробити так, щоб генератор нічого не повертав:
        # if False: # pragma: no cover
        #     yield "" # Щоб тип AsyncGenerator[str, None] був валідним

# Приклад, як може виглядати реальний клас Subscription після імпорту частин:
# @strawberry.type
# class Subscription(
#     NotificationSubscriptions,
#     TaskSubscriptions,
# ):
#     pass
# --- Кінець заглушки ---

# Експортувати Subscription, тільки якщо він дійсно використовується.
# Якщо підписки не плануються, краще закоментувати цей клас та експорт,
# а також відповідну частину в `graphql/schema.py`.
__all__ = [
    "Subscription",
]
