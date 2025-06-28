# backend/app/src/api/graphql/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'graphql' API.

Цей пакет відповідає за всю логіку, пов'язану з GraphQL API додатку.
Він включає:
- Головну GraphQL схему (очікується у `schema.py`), яка визначає кореневі типи Query, Mutation, Subscription.
- Підпакети для GraphQL типів (`types/`), резолверів запитів (`queries/`),
  мутацій (`mutations/`) та підписок (`subscriptions/`).
- Модулі для створення GraphQL контексту (`context.py`), даталоадерів (`dataloaders.py`),
  кастомних директив (`directives.py`) та скалярів (`scalars.py`), якщо вони потрібні.

Цей файл робить каталог 'graphql' пакетом Python.
Його основна мета - експортувати готовий для FastAPI `GraphQLRouter`
(наприклад, від `strawberry.fastapi`), який використовує скомпільовану схему.
Цей роутер потім монтується в основному FastAPI додатку в `app/main.py`.
"""

# TODO: Імпортувати головну GraphQL схему з `schema.py`, коли вона буде готова.
# from backend.app.src.api.graphql.schema import schema as graphql_main_schema
# from backend.app.src.config.settings import settings # Для керування GraphiQL

# TODO: Імпортувати GraphQLRouter від обраної бібліотеки (наприклад, Strawberry).
# from strawberry.fastapi import GraphQLRouter

# TODO: Створити екземпляр GraphQLRouter.
# graphql_app = GraphQLRouter(
#     graphql_main_schema,
#     graphiql=settings.DEBUG # Дозволити GraphiQL інтерфейс в режимі розробки
# )
# logger.info(f"GraphQL App створено. GraphiQL: {settings.DEBUG}") # Потрібен logger

# TODO: Експортувати `graphql_app` для використання в `app/main.py`.
# __all__ = [
#     "graphql_app",
# ]

# Якщо схема або контекст потребують ініціалізації на рівні пакету,
# це можна зробити тут, але зазвичай це інкапсульовано в `schema.py` або `context.py`.

# На даний момент, поки залежності не створені, файл може залишатися таким.
# При розкоментуванні, переконайтеся, що `schema.py` та `settings.py` існують
# та містять відповідні змінні (`graphql_main_schema`, `settings.DEBUG`).
pass
