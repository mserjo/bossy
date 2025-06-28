# backend/app/src/api/graphql/schema.py
# -*- coding: utf-8 -*-
"""
Головний файл GraphQL схеми.

Цей модуль відповідає за визначення та компіляцію головної GraphQL схеми додатку,
використовуючи бібліотеку Strawberry.

Він виконує наступні завдання:
1.  Імпортує кореневі типи `Query` (з `queries/__init__.py`), `Mutation` (з `mutations/__init__.py`)
    та, опціонально, `Subscription` (з `subscriptions/__init__.py`).
2.  Збирає всі необхідні GraphQL типи (ObjectTypes, InputTypes, Enums, Scalars, Interfaces, Unions)
    з підкаталогу `types/` або вони автоматично знаходяться Strawberry, якщо правильно імпортовані
    в резолверах.
3.  Створює та експортує екземпляр скомпільованої схеми `strawberry.Schema`.

Скомпільована схема (`schema`) потім імпортується в `backend.app.src.api.graphql.__init__.py`
для створення екземпляра `GraphQLRouter`, який підключається до FastAPI.
"""

import strawberry

# TODO: Імпортувати кореневі типи Query, Mutation, Subscription, коли вони будуть реалізовані.
# Ці файли (`queries/__init__.py`, `mutations/__init__.py`, `subscriptions/__init__.py`)
# повинні визначати відповідні класи, декоровані `@strawberry.type`.

# from backend.app.src.api.graphql.queries import Query
# from backend.app.src.api.graphql.mutations import Mutation
# # from backend.app.src.api.graphql.subscriptions import Subscription # Якщо використовуються

# TODO: Імпортувати кастомні скаляри та директиви, якщо вони визначені та потрібні на рівні схеми.
# from backend.app.src.api.graphql.scalars import DateTimeScalar, UUIDScalar # Приклад
# from backend.app.src.api.graphql.directives import IsAuthenticatedDirective # Приклад

# --- Заглушки для Query та Mutation, поки вони не реалізовані ---
# Ці заглушки дозволять схемі компілюватися, але не матимуть реальної функціональності.
# Їх потрібно буде замінити на реальні імпорти.

@strawberry.type
class RootQuery:
    """
    Кореневий тип для GraphQL запитів (Queries).
    Містить поля, що дозволяють отримувати дані з сервера.
    """
    @strawberry.field
    def hello_query(self, name: str = "GraphQL User") -> str:
        """Простий запит для перевірки роботи схеми."""
        return f"Hello, {name}! This is a placeholder query."

@strawberry.type
class RootMutation:
    """
    Кореневий тип для GraphQL мутацій (Mutations).
    Містить поля, що дозволяють змінювати дані на сервері.
    """
    @strawberry.mutation
    def example_mutation(self, input_str: str) -> str:
        """Проста мутація для перевірки роботи схеми."""
        return f"Placeholder mutation received: {input_str}. No data was changed."

# @strawberry.type
# class RootSubscription:
#     """
#     Кореневий тип для GraphQL підписок (Subscriptions).
#     Дозволяє клієнтам отримувати оновлення даних в реальному часі.
#     """
#     @strawberry.subscription
#     async def example_subscription(self, target_id: int) -> strawberry.AsyncGenerator[str, None]:
#         """Проста підписка для перевірки."""
#         import asyncio
#         count = 0
#         while count < 5:
#             await asyncio.sleep(1)
#             yield f"Update for {target_id}: event {count}"
#             count += 1
# --- Кінець заглушок ---


# Створення екземпляра схеми Strawberry.
# Замініть `RootQuery` та `RootMutation` на реальні `Query` та `Mutation` після їх імпорту.
schema = strawberry.Schema(
    query=RootQuery, # Замінити на Query
    mutation=RootMutation, # Замінити на Mutation
    # subscription=RootSubscription, # Розкоментувати та замінити на Subscription, якщо потрібно
    # types=[DateTimeScalar, UUIDScalar], # Додати список кастомних скалярів, якщо вони не знаходяться автоматично
    # directives=[IsAuthenticatedDirective], # Додати список кастомних директив
    # extensions=[] # Можна додати розширення, наприклад, для трасування, логування, APM.
)

# from backend.app.src.config.logging import get_logger # TODO: Розкоментувати для логування
# logger = get_logger(__name__)
# logger.info("GraphQL schema compiled successfully using Strawberry.")

# Експорт схеми для використання в `graphql/__init__.py`.
__all__ = [
    "schema",
]

# Важливо:
# - Усі GraphQL типи (UserType, GroupType тощо), що використовуються в полях Query/Mutation/Subscription
#   або як їх аргументи, повинні бути доступні Strawberry під час компіляції схеми.
#   Це зазвичай досягається шляхом їх імпорту в модулях, де визначені Query/Mutation/Subscription,
#   або, для деяких конфігурацій, явним передаванням у параметр `types=[]` конструктора `strawberry.Schema`.
# - Контекст запиту (що містить, наприклад, сесію БД, поточного користувача, даталоадери)
#   буде створений у `context.py` та переданий до `GraphQLRouter` в `graphql/__init__.py` або `app/main.py`.
#   Доступ до контексту в резолверах здійснюється через параметр `info: strawberry.Info`.
# - Даталоадери (`dataloaders.py`) також ініціалізуються та передаються через контекст
#   для вирішення проблеми N+1 запитів.
