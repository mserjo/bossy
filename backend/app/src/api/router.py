# backend/app/src/api/router.py
# -*- coding: utf-8 -*-
"""
Головний агрегатор роутерів для API.

Цей файл відповідає за створення екземпляру `APIRouter` та підключення
до нього всіх версій API (наприклад, v1, v2) та інших головних
складових API, таких як GraphQL ендпоінт.

Основний екземпляр FastAPI додатку (в `app/main.py`) буде включати
цей `api_router` для надання доступу до всіх ендпоінтів API
за певним префіксом (наприклад, `/api`).
"""

from fastapi import APIRouter

# TODO: Імпортувати роутери для конкретних версій API та GraphQL, коли вони будуть створені.
# from backend.app.src.api.v1.router import router as v1_router
# from backend.app.src.api.graphql.schema import graphql_app # Або інший спосіб підключення GraphQL

# Головний роутер для всього API
api_router = APIRouter()

# Підключення роутера для API версії 1
# TODO: Розкоментувати, коли v1_router буде реалізований.
# api_router.include_router(v1_router, prefix="/v1", tags=["API v1"])

# Підключення GraphQL ендпоінту
# TODO: Розкоментувати та адаптувати, коли graphql_app буде реалізований.
# Приклад для Strawberry:
# api_router.include_router(graphql_app, prefix="/graphql", tags=["GraphQL"])
# Приклад для Ariadne (може потребувати іншого підходу, наприклад, монтування ASGI додатку):
# api_router.add_route("/graphql", graphql_app, name="graphql")


# Приклад простого ендпоінту на кореневому рівні API (наприклад, /api/)
@api_router.get("/", tags=["API Root"])
async def read_api_root():
    """
    Кореневий ендпоінт API.
    Надає базову інформацію про API.
    """
    return {
        "message": "Ласкаво просимо до Bossy API!",
        "documentation_v1": "/api/v1/docs",  # TODO: Перевірити актуальність шляху
        "redoc_v1": "/api/v1/redoc",          # TODO: Перевірити актуальність шляху
        "graphql_endpoint": "/api/graphql"   # TODO: Перевірити актуальність шляху
    }

# TODO: Можливо, тут будуть підключатися роутери для зовнішніх API (вебхуків),
# якщо вони не будуть частиною конкретної версії API.
# from backend.app.src.api.external.router import external_router # Припустимо, що такий роутер існує
# api_router.include_router(external_router, prefix="/external", tags=["External API / Webhooks"])


# Цей api_router буде імпортований та підключений в app/main.py:
# from backend.app.src.api.router import api_router
# app.include_router(api_router, prefix="/api")
