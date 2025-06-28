# backend/app/main.py
# -*- coding: utf-8 -*-
"""
Головний файл запуску FastAPI додатку.

Цей файл відповідає за:
- Створення екземпляру FastAPI додатку.
- Конфігурацію middleware (CORS, логування запитів тощо).
- Підключення обробників подій життєвого циклу додатку (startup, shutdown).
- Реєстрацію головного API роутера для REST ендпоінтів.
- Реєстрацію GraphQL схеми для GraphQL ендпоінтів.
- Визначення базових ендпоінтів, наприклад, для перевірки стану системи (health check).
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
# TODO: Розкоментувати, коли файли будуть створені
# from backend.app.src.api.router import router as api_router_v1
# from backend.app.src.api.graphql.schema import schema as graphql_schema
# from backend.app.src.config.settings import settings
# from backend.app.src.config.logging import get_logger
# from backend.app.src.core.events import create_start_app_handler, create_stop_app_handler
# from backend.app.src.services.system.initialization import (
#     initialize_system_data,
#     check_initial_data
# )

# logger = get_logger(__name__) # TODO: Розкоментувати

# Створення екземпляру FastAPI
# TODO: Додати title, version, description з конфігураційного файлу settings
app = FastAPI(
    title="Bossy Backend",
    version="0.1.0",
    description="API для бонусної системи Bossy"
)

# Налаштування CORS
# TODO: Винести origins в конфігураційний файл settings
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000", # Для Flutter Web в режимі розробки
    # Додати інші дозволені origins за потреби
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Дозволяє запити з вказаних джерел
    allow_credentials=True, # Дозволяє передачу cookies
    allow_methods=["*"], # Дозволяє всі HTTP методи
    allow_headers=["*"], # Дозволяє всі HTTP заголовки
)

# TODO: Додати middleware для логування запитів, якщо потрібно окреме від Uvicorn
# @app.middleware("http")
# async def log_requests_middleware(request: Request, call_next):
#     logger.info(f"Request: {request.method} {request.url}")
#     response = await call_next(request)
#     logger.info(f"Response status: {response.status_code}")
#     return response

# Обробники подій життєвого циклу
# TODO: Розкоментувати та реалізувати функції, коли відповідні сервіси будуть готові
# app.add_event_handler("startup", create_start_app_handler(app))
# app.add_event_handler("shutdown", create_stop_app_handler(app))

# @app.on_event("startup")
# async def startup_event():
#     """
#     Обробник події запуску додатку.
#     Виконується один раз при старті сервера.
#     """
#     logger.info("Додаток запускається...")
#     # Перевірка та ініціалізація початкових даних
#     # await check_initial_data() # Перевіряє, чи існують базові дані (довідники, системні користувачі)
#     # await initialize_system_data() # Створює базові дані, якщо їх немає
#     logger.info("Перевірка та ініціалізація початкових даних завершена.")
#     # TODO: Додати інші дії, які потрібно виконати при старті,
#     # наприклад, підключення до БД, Redis, Celery (якщо не зроблено в іншому місці)

# @app.on_event("shutdown")
# async def shutdown_event():
#     """
#     Обробник події зупинки додатку.
#     Виконується один раз при зупинці сервера.
#     """
#     logger.info("Додаток зупиняється...")
#     # TODO: Додати дії, які потрібно виконати при зупинці,
#     # наприклад, закриття з'єднань з БД, звільнення ресурсів

# Підключення роутерів
# TODO: Розкоментувати, коли роутери будуть створені та наповнені
# app.include_router(api_router_v1, prefix=settings.API_V1_STR, tags=["v1"])
# logger.info(f"API v1 роутер підключено за префіксом: {settings.API_V1_STR}")

# Підключення GraphQL
# TODO: Розкоментувати, коли GraphQL схема буде готова
# from strawberry.fastapi import GraphQLRouter
# graphql_app = GraphQLRouter(graphql_schema, graphiql=settings.DEBUG)
# app.include_router(graphql_app, prefix="/graphql", tags=["graphql"])
# logger.info("GraphQL роутер підключено за префіксом: /graphql")


# Ендпоінт для перевірки стану системи (health check)
@app.get(
    "/health",
    tags=["System"],
    summary="Перевірка стану системи",
    description="Повертає статус 200 OK, якщо система працює справно.",
    status_code=status.HTTP_200_OK,
)
async def health_check() -> JSONResponse:
    """
    Перевіряє працездатність сервісу.
    """
    # logger.info("Запит на перевірку стану системи /health") # TODO: Розкоментувати
    return JSONResponse(content={"status": "OK"})

# TODO: Додати обробку глобальних винятків, якщо потрібно кастомна логіка
# from fastapi import HTTPException
# @app.exception_handler(HTTPException)
# async def http_exception_handler(request: Request, exc: HTTPException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.detail, "custom_message": "Це кастомне повідомлення про помилку"},
#     )

if __name__ == "__main__":
    # Цей блок виконується, тільки якщо файл запускається напряму.
    # Зазвичай, для запуску FastAPI додатку використовується Uvicorn.
    # uvicorn main:app --reload
    import uvicorn
    # logger.info("Запуск додатку через uvicorn (режим розробки)...") # TODO: Розкоментувати
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

# TODO: Додати документацію для OpenAPI (теги, опис тощо)
# TODO: Перевірити відповідність всім вимогам з technical-task.md та code-style.md
# TODO: Налаштувати інтеграцію з Celery, Redis, Firebase, Elasticsearch, якщо вони використовуються
# (це може бути зроблено через обробники подій startup/shutdown або окремі конфігураційні модулі)
"""
Приклад структури:
- FastAPI app instance
- Middleware (CORS, logging, etc.)
- Event handlers (startup, shutdown)
  - Database connection
  - Redis connection
  - Celery setup
  - Initial data seeding
- Routers
  - API v1 router
  - GraphQL router
- Health check endpoint
- Global exception handlers (optional)
"""
