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
- Налаштування глобальних обробників винятків.
"""

import asyncio
from typing import TYPE_CHECKING, Any, Dict

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter # type: ignore

# Імпорт конфігурацій та логгера
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import logger # Використовуємо logger з loguru
from backend.app.src.config.database import (
    # init_db, # Зазвичай не потрібен, якщо є Alembic
    get_async_session,
    close_db_connection,
    connect_to_db,
)
from backend.app.src.config.redis import init_redis_pool, close_redis_pool, get_redis_client
# from backend.app.src.config.celery_app import get_celery_app # TODO: Розкоментувати, коли Celery буде налаштовано

# Імпорт роутерів
from backend.app.src.api.router import router as main_api_router # Головний агрегований REST API роутер
from backend.app.src.api.graphql.schema import schema as graphql_schema # Головна GraphQL схема
from backend.app.src.api.graphql.context import get_graphql_context # Функція для отримання GraphQL контексту

# Імпорт сервісів
from backend.app.src.services.system.initialization_service import InitializationService

# Імпорт для обробників подій, якщо вони винесені (поки не використовуються)
# from backend.app.src.core.events import create_start_app_handler, create_stop_app_handler

if TYPE_CHECKING:
    from redis.asyncio import Redis as AsyncRedisClient # type: ignore
    # Це для уникнення циклічного імпорту, якщо FastAPI/Request потрібні в redis.py для типів

# Створення екземпляру FastAPI
# Використовуємо title, version, description з settings.app
# Також додано openapi_tags для кращої документації OpenAPI.
# URL для OpenAPI, Swagger UI (docs) та ReDoc вмикаються/вимикаються залежно від режиму DEBUG.
openapi_tags_metadata = [
    {
        "name": "System",
        "description": "Системні ендпоінти, включаючи перевірку стану та ініціалізацію.",
    },
    {
        "name": "v1",
        "description": "Ендпоінти API версії 1. Детальна специфікація знаходиться в підключеному роутері v1.",
    },
    {
        "name": "graphql",
        "description": "GraphQL API. Дозволяє гнучкі запити до даних.",
    },
    # TODO: Додати інші теги для основних груп ендпоінтів API v1 по мірі їх реалізації
    # Наприклад: "Auth", "Users", "Groups", "Tasks" і т.д.
    # Ці теги можна також визначати безпосередньо в APIRouter для кожної групи ендпоінтів.
]

app = FastAPI(
    title=settings.app.APP_NAME,
    version=settings.app.APP_VERSION,
    description=settings.app.DESCRIPTION,
    debug=settings.app.DEBUG,
    openapi_url=f"{settings.app.API_V1_STR}/openapi.json" if not settings.app.DEBUG else "/openapi.json",
    docs_url="/docs" if settings.app.DEBUG else None,
    redoc_url="/redoc" if settings.app.DEBUG else None,
    openapi_tags=openapi_tags_metadata
)

# Налаштування CORS
# Використовуємо BACKEND_CORS_ORIGINS з settings.app.
# Якщо список origins порожній, CORS middleware не додається.
if settings.app.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.app.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"], # Дозволяє всі стандартні HTTP методи
        allow_headers=["*"], # Дозволяє всі стандартні HTTP заголовки
    )
    logger.info(f"CORS middleware додано. Дозволені origins: {settings.app.BACKEND_CORS_ORIGINS}")
else:
    logger.warning(
        "CORS middleware не додано, оскільки `BACKEND_CORS_ORIGINS` не налаштовано в `settings.app`. "
        "Це може бути проблемою для frontend додатків, що працюють на інших доменах/портах."
    )

# Middleware для логування HTTP запитів та відповідей
# Це забезпечує додаткове логування через Loguru на рівні FastAPI,
# доповнюючи стандартне логування Uvicorn.
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next: Any) -> Any:
    """
    Middleware для логування деталей кожного HTTP запиту та відповіді.
    Логує метод, шлях, рядок запиту (якщо є) та статус відповіді.
    У разі винятку під час обробки запиту, логує помилку.
    """
    # Формуємо рядок з параметрами запиту, якщо вони є
    query_params = f"?{request.url.query}" if request.url.query else ""
    logger.info(f"Вхідний запит: {request.method} {request.url.path}{query_params}")
    try:
        response = await call_next(request)
        logger.info(f"Відповідь для {request.method} {request.url.path}{query_params}: Статус {response.status_code}")
        return response
    except Exception as e:
        # Логуємо виняток, який стався під час обробки запиту,
        # перед тим як він буде оброблений глобальними обробниками винятків.
        logger.exception(f"Помилка під час обробки запиту: {request.method} {request.url.path}{query_params}")
        raise e # Важливо повторно кинути виняток


# Обробники подій життєвого циклу FastAPI
@app.on_event("startup")
async def startup_event() -> None:
    """
    Обробник події запуску додатку (startup event).
    Виконується один раз при старті сервера FastAPI.
    Ініціалізує підключення до бази даних, Redis, Celery (якщо використовуються)
    та виконує початкове наповнення системи даними (довідники, системні користувачі).
    """
    logger.info(f"Додаток '{settings.app.APP_NAME}' версії {settings.app.APP_VERSION} запускається...")
    logger.info(f"Середовище: {settings.app.ENVIRONMENT.value}, Режим відладки: {settings.app.DEBUG}")

    # 1. Ініціалізація підключення до бази даних PostgreSQL
    await connect_to_db() # Створює SQLAlchemy async engine
    logger.info("Підключення до бази даних PostgreSQL встановлено (engine створено).")
    # Зауваження: створення таблиць (еквівалент `Base.metadata.create_all(bind=engine)`)
    # зазвичай виконується через Alembic міграції (`alembic upgrade head`).
    # Тому `init_db()` тут закоментовано.
    # # await init_db()

    # 2. Ініціалізація підключення до Redis (якщо увімкнено та налаштовано)
    if settings.app.USE_REDIS:
        if settings.redis and settings.redis.REDIS_URL:
            app.state.redis = await init_redis_pool(str(settings.redis.REDIS_URL))
            logger.info(f"Підключення до Redis ({settings.redis.REDIS_URL}) встановлено (пул створено).")
            try:
                redis_client_instance: "AsyncRedisClient" = await get_redis_client(request=None, app_state=app.state) # type: ignore
                if await redis_client_instance.ping():
                    logger.info("Redis ping успішний. З'єднання з Redis активне.")
                else:
                    logger.warning("Redis ping не повернув очікуваного результату, але не кинув виняток.")
            except ConnectionRefusedError:
                 logger.error(f"Помилка підключення до Redis: ConnectionRefusedError. Перевірте, чи запущено Redis сервер за адресою {settings.redis.REDIS_URL} та чи доступний він.")
            except Exception as e:
                logger.error(f"Не вдалося виконати ping до Redis або інша помилка Redis: {e}", exc_info=True)
        else:
            app.state.redis = None
            logger.warning("Redis увімкнено (settings.app.USE_REDIS=True), але налаштування Redis (settings.redis) або REDIS_URL відсутні. Підключення до Redis пропущено.")
    else:
        app.state.redis = None
        logger.info("Використання Redis вимкнено (settings.app.USE_REDIS=False). Підключення до Redis пропущено.")

    # 3. Ініціалізація Celery (якщо увімкнено та налаштовано)
    if settings.app.USE_CELERY:
        # TODO: Розкоментувати та реалізувати, коли Celery буде інтегровано.
        # Потрібно буде імпортувати `get_celery_app` та налаштувати його.
        if settings.celery and settings.celery.CELERY_BROKER_URL:
        #     app.state.celery_app = get_celery_app()
            logger.info(f"Celery (теоретично) налаштовано. Broker: {settings.celery.CELERY_BROKER_URL}") # Заглушка
        else:
        #     app.state.celery_app = None
            logger.warning("Celery увімкнено (settings.app.USE_CELERY=True), але налаштування Celery (settings.celery) або CELERY_BROKER_URL відсутні. Ініціалізація Celery пропущена.")
    else:
        # app.state.celery_app = None
        logger.info("Використання Celery вимкнено (settings.app.USE_CELERY=False). Ініціалізація Celery пропущена.")

    # TODO: Додати аналогічні перевірки для Elasticsearch та Firebase, коли їх ініціалізація буде додана.
    # if settings.app.USE_ELASTICSEARCH:
    #   if settings.elasticsearch and settings.elasticsearch.ELASTICSEARCH_HOSTS:
    #     # Ініціалізація Elasticsearch
    #   else: logger.warning(...)
    # else: logger.info(...)
    #
    # if settings.app.USE_FIREBASE:
    #   if settings.firebase and settings.firebase.FIREBASE_CREDENTIALS_PATH:
    #     # Ініціалізація Firebase
    #   else: logger.warning(...)
    # else: logger.info(...)


    # 4. Перевірка та ініціалізація початкових даних системи (довідники, системні користувачі)
    logger.info("Запуск перевірки та ініціалізації початкових даних системи...")
    # Використовуємо асинхронний генератор сесій `get_async_session`
    # для забезпечення коректного управління сесіями.
    async for session in get_async_session():
        try:
            initialization_service = InitializationService(session)
            init_results = await initialization_service.run_full_initialization()
            # Явний коміт після всіх операцій сервісу ініціалізації в рамках однієї сесії.
            # Це важливо, якщо `run_full_initialization` не робить коміти самостійно.
            await session.commit()
            logger.info(f"Результати ініціалізації системних даних: {init_results}")
        except Exception as e:
            # У разі помилки під час ініціалізації, відкочуємо транзакцію
            await session.rollback()
            logger.error(f"Помилка під час ініціалізації системних даних: {e}", exc_info=True)
            # Тут можна вирішити, чи слід додатку падати при помилці ініціалізації,
            # чи продовжувати роботу з попередженням.
            # Наприклад, можна кинути виняток: raise SystemError(f"Failed to initialize system data: {e}")
        finally:
            # Завжди закриваємо сесію, отриману з генератора.
            await session.close()
    logger.info("Перевірка та ініціалізація початкових даних системи завершена.")

    logger.info(f"Додаток '{settings.app.APP_NAME}' успішно запущено та готовий до роботи.")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Обробник події зупинки додатку (shutdown event).
    Виконується один раз при зупинці сервера FastAPI.
    Закриває активні з'єднання з базою даних, Redis тощо.
    """
    logger.info(f"Додаток '{settings.app.APP_NAME}' зупиняється...")

    # 1. Закриття підключення до Redis (якщо воно було ініціалізовано та використовується)
    if settings.app.USE_REDIS and hasattr(app.state, 'redis') and app.state.redis:
        await close_redis_pool(app.state.redis)
        logger.info("Підключення до Redis закрито.")
    elif settings.app.USE_REDIS:
        logger.info("Redis було увімкнено (USE_REDIS=True), але не було активного підключення для закриття.")
    else:
        logger.info("Використання Redis вимкнено (USE_REDIS=False). Закриття підключення до Redis пропущено.")


    # 2. Закриття підключення до бази даних PostgreSQL
    await close_db_connection() # Закриває пул з'єднань SQLAlchemy
    logger.info("Підключення до бази даних PostgreSQL закрито.")

    # 3. Зупинка Celery (якщо використовується, було ініціалізовано та потрібно)
    if settings.app.USE_CELERY:
        # TODO: Реалізувати логіку зупинки Celery, якщо потрібно.
        # if hasattr(app.state, 'celery_app') and app.state.celery_app:
        #     # app.state.celery_app.control.shutdown() # Приклад
        #     logger.info("Celery (теоретично) зупинено.") # Заглушка
        # else:
        #     logger.info("Celery було увімкнено (USE_CELERY=True), але не було активного екземпляру для зупинки.")
        logger.info("Celery (теоретично) зупинено (заглушка).") # Поки що просто логуємо
    else:
        logger.info("Використання Celery вимкнено (USE_CELERY=False). Зупинка Celery пропущена.")

    # TODO: Додати аналогічні перевірки для Elasticsearch та Firebase.

    logger.info(f"Додаток '{settings.app.APP_NAME}' успішно зупинено.")


# Підключення роутерів
# Головний агрегований REST API роутер підключається з префіксом "/api".
# Це означає, що всі ендпоінти, визначені в `main_api_router` (включаючи ті,
# що підключені до нього, наприклад, v1 роутер з префіксом settings.app.API_V1_STR),
# будуть доступні через `/api/...`.
# Наприклад, якщо API_V1_STR = "/v1", то ендпоінти v1 будуть на `/api/v1/...`.
app.include_router(main_api_router, prefix="/api") # Загальний префікс для всіх REST API
logger.info(f"Головний REST API роутер підключено з префіксом: /api.")
logger.info(f"Очікуваний префікс для API v1 (відносно /api): {settings.app.API_V1_STR}")

# Підключення GraphQL API
# Використовуємо GraphQL схему, імпортовану з `src.api.graphql.schema`,
# та функцію для отримання контексту `get_graphql_context`.
# GraphiQL UI (інтерактивний редактор запитів) вмикається залежно від `settings.app.DEBUG`.
graphql_app_router = GraphQLRouter(
    schema=graphql_schema,
    graphiql=settings.app.DEBUG,
    context_getter=get_graphql_context
)
app.include_router(
    graphql_app_router,
    prefix=settings.app.GRAPHQL_API_STR, # Префікс для GraphQL, наприклад, "/graphql"
    tags=["graphql"] # Тег для групування в OpenAPI документації
)
logger.info(f"GraphQL роутер підключено. Префікс: {settings.app.GRAPHQL_API_STR}. GraphiQL UI: {settings.app.DEBUG}")


# Ендпоінт для перевірки стану системи (health check)
# Цей ендпоінт не має префіксу /api, доступний за шляхом /health.
@app.get(
    "/health",
    tags=["System"], # Групування в OpenAPI
    summary="Перевірка стану та працездатності системи",
    description="Повертає статус 200 OK та повідомлення, якщо система працює справно.",
    status_code=status.HTTP_200_OK, # Очікуваний HTTP статус успішної відповіді
    response_model=Dict[str, str] # Модель відповіді для OpenAPI документації
)
async def health_check() -> Dict[str, str]:
    """
    Перевіряє базову працездатність сервісу.
    Може бути розширений для перевірки залежностей (БД, Redis тощо).
    """
    logger.info("Запит на перевірку стану системи: /health")
    # TODO: Розширити перевірку стану, наприклад, пінгувати БД, Redis, якщо потрібно.
    # Приклад:
    # db_ping_ok = False
    # async for session in get_async_session():
    #     try:
    #         await session.execute(text("SELECT 1"))
    #         db_ping_ok = True
    #     except Exception:
    #         db_ping_ok = False
    #     finally:
    #         await session.close()
    # if not db_ping_ok:
    #     return {"status": "unhealthy", "message": "Database connection failed"}
    return {"status": "OK", "message": f"{settings.app.APP_NAME} is healthy and running!"}

# Глобальні обробники винятків
# Ці обробники перехоплюють винятки, що виникають під час обробки запитів,
# та повертають стандартизовані JSON-відповіді.

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Обробляє винятки типу `HTTPException` (стандартні помилки FastAPI).
    Повертає JSON відповідь з кодом статусу, повідомленням та типом помилки.
    Логує HTTP винятки, з детальною інформацією для серверних помилок (5xx).
    """
    log_level = "error" if exc.status_code >= 500 else "warning"
    logger.log(
        log_level,
        f"HTTP виняток: Статус {exc.status_code}, Деталі: '{exc.detail}' для запиту {request.method} {request.url.path}",
        exc_info=True if exc.status_code >= 500 else False # Логуємо stacktrace для 5xx
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code, # Код помилки (ідентичний HTTP статусу)
                "message": exc.detail,   # Повідомлення про помилку
                "type": "http_exception" # Тип помилки
            }
        },
        headers=getattr(exc, "headers", None) # Зберігаємо кастомні заголовки з винятку, якщо вони є
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Обробляє всі інші неперехоплені винятки (нащадки `Exception`).
    Повертає стандартизовану JSON відповідь зі статусом 500 Internal Server Error.
    Завжди логує повний stacktrace для невідомих помилок.
    """
    logger.error(
        f"Неперехоплений внутрішній виняток: {exc.__class__.__name__} ('{str(exc)}') для запиту {request.method} {request.url.path}",
        exc_info=True # Завжди логуємо stacktrace для невідомих серверних помилок
    )
    # Формуємо відповідь. У DEBUG режимі можна додавати більше деталей.
    error_content: Dict[str, Any] = {
        "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "message": "An unexpected internal server error occurred. Please try again later or contact support.",
        "type": "unhandled_server_exception",
    }
    if settings.app.DEBUG:
        error_content["detail"] = f"{exc.__class__.__name__}: {str(exc)}"
        # У DEBUG можна додати traceback, але це може бути занадто багато для JSON відповіді.
        # import traceback
        # error_content["traceback"] = traceback.format_exc().splitlines()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": error_content},
    )


if __name__ == "__main__":
    # Цей блок виконується, тільки якщо файл запускається напряму як скрипт
    # (наприклад, `python backend/app/main.py`).
    # Зазвичай, для запуску FastAPI додатку в розробці та на продакшені
    # використовується ASGI сервер, такий як Uvicorn, викликаний з командного рядка:
    # `uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000`
    import uvicorn
    logger.info("Запуск додатку через Uvicorn (режим розробки, викликаний з main.py)...")

    # Визначаємо порт з налаштувань, якщо він там є, інакше використовуємо дефолтний 8000.
    app_port = getattr(settings.app, 'APP_PORT', 8000) # Безпечне отримання атрибуту

    uvicorn.run(
        "backend.app.main:app", # Шлях до екземпляру FastAPI додатку ('module:variable')
        host="0.0.0.0",         # Слухати на всіх доступних мережевих інтерфейсах
        port=app_port,
        log_level=settings.logging.LOG_LEVEL.lower(), # Рівень логування для Uvicorn
        reload=settings.app.DEBUG, # Автоматичне перезавантаження при зміні коду (тільки для DEBUG)
        # log_config=None # Якщо None, Uvicorn використовує свій дефолтний лог-конфіг.
                        # Наш Loguru InterceptHandler має перехоплювати стандартні логи.
                        # Якщо встановити тут кастомний log_config для Loguru,
                        # то треба бути обережним, щоб не було конфліктів.
                        # Поки що залишимо так, щоб Loguru перехоплював стандартні логи.
    )

# TODO: Додати документацію для OpenAPI (теги, опис тощо) - Частково зроблено через openapi_tags_metadata.
#       Потрібно буде додати детальні описи для кожного ендпоінту та схеми даних.
# TODO: Перевірити відповідність всім вимогам з `technical-task.md` та `code-style.md` - Частково зроблено.
#       Коментарі українською, структура файлу, використання логера, тощо.
# TODO: Налаштувати інтеграцію з Celery, Firebase, Elasticsearch, якщо вони будуть активно використовуватися.
#       Це може включати додавання відповідних клієнтів/конфігурацій в `startup` та `shutdown`
#       та створення окремих конфігураційних модулів в `backend.app.src.config`.
# TODO: Розглянути можливість винесення логіки `startup_event` та `shutdown_event` в окремі функції
#       в `backend.app.src.core.events.py` (наприклад, `create_start_app_handler`, `create_stop_app_handler`),
#       якщо ця логіка стане занадто об'ємною та складною. Поки що вона залишена тут для наочності.
# TODO: Для `InitializationService` та `run_full_initialization`: переконатися, що всі операції
#       в базі даних виконуються в рамках однієї транзакції, якщо це критично.
#       Поточна реалізація `get_async_session` як генератора сесій дозволяє це зробити,
#       якщо `initialization_service.run_full_initialization` не робить власних комітів/ролбеків
#       для кожної окремої операції. Явний `session.commit()` та `session.rollback()`
#       в `startup_event` керують транзакцією для всіх операцій сервісу.
