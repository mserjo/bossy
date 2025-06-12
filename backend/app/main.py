# backend/app/main.py
# -*- coding: utf-8 -*-
"""
Головний модуль FastAPI програми Kudos.

Цей файл визначає та конфігурує основний екземпляр FastAPI (`app`),
включає маршрутизатори API, налаштовує middleware (наприклад, CORS),
обробники подій життєвого циклу програми (startup, shutdown) та
глобальні обробники винятків.

Саме цей екземпляр `app` ре-експортується з `backend.app.__init__.py`
для запуску ASGI-сервером (наприклад, Uvicorn).
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager # Для нового стилю lifespan подій у FastAPI

# Абсолютні імпорти з проекту
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import setup_logging, get_logger
from backend.app.src.config.redis import get_redis_client, close_redis_client
# from backend.app.src.config.database import create_db_and_tables # Розкоментуйте, якщо потрібно створювати таблиці при старті (НЕ для продакшену)
from backend.app.src.core.exceptions import AppException

# TODO: Імпортувати головний маршрутизатор API, коли він буде створений
# from backend.app.src.api.v1.api_router import api_router as api_v1_router
# from backend.app.src.api.admin.admin_router import admin_router # Приклад для адмін-панелі

# Ініціалізація логера для цього модуля
# Важливо: setup_logging() має бути викликана до першого використання get_logger()
# в інших модулях, якщо вони імпортуються на рівні модуля.
# У цьому випадку, ми викликаємо setup_logging() в lifespan події "startup".
logger = get_logger(__name__) # Отримуємо логер для main.py

# --- Обробники подій життєвого циклу програми (Lifespan Events) ---
@asynccontextmanager
async def lifespan(current_app: FastAPI):
    """
    Асинхронний контекстний менеджер для подій життєвого циклу FastAPI.
    Код перед `yield` виконується при старті програми (startup).
    Код після `yield` виконується при завершенні програми (shutdown).
    """
    # --- Startup ---
    print("Виконується запуск програми Kudos...") # Використовуємо print, бо логер ще може не бути повністю налаштований

    # 1. Налаштування системи логування
    setup_logging() # Застосовуємо конфігурацію логування
    logger.info(f"Запуск програми '{settings.PROJECT_NAME}' в середовищі '{settings.ENVIRONMENT}' з рівнем логування '{settings.LOGGING_LEVEL}'.")

    # 2. Ініціалізація та перевірка з'єднання з Redis
    try:
        await get_redis_client() # Ініціалізує та перевіряє з'єднання
        logger.info("Клієнт Redis успішно ініціалізовано та підключено.")
    except Exception as e:
        logger.error(f"Не вдалося ініціалізувати або підключитися до Redis під час запуску: {e}", exc_info=True)
        # Залежно від критичності Redis, тут можна або продовжити роботу, або завершити програму.
        # Наприклад: raise RuntimeError("Не вдалося підключитися до Redis, запуск програми скасовано.") from e

    # 3. Створення таблиць бази даних (ТІЛЬКИ для розробки/тестування, якщо не використовуються міграції Alembic)
    # УВАГА: У продакшен-середовищі для управління схемою БД слід використовувати Alembic.
    # Розкоментуйте наступні рядки, якщо це потрібно для локальної розробки,
    # але переконайтеся, що це не виконується в продакшені.
    # if settings.ENVIRONMENT == "development":
    #     try:
    #         logger.info("Спроба створення таблиць бази даних (тільки для розробки)...")
    #         from backend.app.src.config.database import create_db_and_tables # Імпорт тут, щоб уникнути циклічних залежностей
    #         await create_db_and_tables()
    #         logger.info("Таблиці бази даних перевірено/створено (якщо вони не існували).")
    #     except Exception as e:
    #         logger.error(f"Помилка під час створення таблиць бази даних: {e}", exc_info=True)

    logger.info("Програма Kudos успішно запущена та готова до роботи.")

    yield # Точка переходу, після якої виконується код завершення (shutdown)

    # --- Shutdown ---
    logger.info("Початок процесу завершення роботи програми Kudos...")

    # 1. Закриття з'єднання з Redis
    await close_redis_client()
    logger.info("З'єднання з Redis закрито.")

    logger.info("Програма Kudos успішно завершила роботу.")


# --- Створення екземпляра FastAPI ---
# Використовуємо lifespan для обробки подій startup/shutdown.
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=f"API для системи винагород та завдань '{settings.PROJECT_NAME}'. Середовище: {settings.ENVIRONMENT}.",
    version="0.1.0", # TODO: Версію можна винести в settings.py або отримувати з git
    openapi_url=f"{settings.API_V1_STR}/openapi.json", # Шлях до схеми OpenAPI
    docs_url=f"{settings.API_V1_STR}/docs", # Шлях до інтерактивної документації Swagger UI
    redoc_url=f"{settings.API_V1_STR}/redoc", # Шлях до альтернативної документації ReDoc
    lifespan=lifespan # Підключення обробника подій життєвого циклу
)

# --- Налаштування Middleware ---

# CORS (Cross-Origin Resource Sharing)
# Дозволяє або забороняє запити з інших доменів.
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS], # Дозволені джерела
        allow_credentials=True, # Дозволити кукі та заголовки автентифікації
        allow_methods=["*"],    # Дозволити всі HTTP методи (GET, POST, PUT, DELETE тощо)
        allow_headers=["*"],    # Дозволити всі заголовки
    )
    logger.info(f"Middleware CORS налаштовано з дозволеними джерелами: {settings.BACKEND_CORS_ORIGINS}")
else:
    logger.warning("Middleware CORS не налаштовано (BACKEND_CORS_ORIGINS порожній). Це може бути небезпечно для продакшену.")


# --- Обробники винятків (Exception Handlers) ---

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    Обробник для кастомних винятків `AppException` та їх нащадків.
    Повертає JSON-відповідь з відповідним статус-кодом та деталями помилки.
    """
    logger.warning(
        f"Обробка AppException: {exc.message} (Статус: {exc.status_code}, Деталі для клієнта: {exc.detail})",
        exc_info=True # Додаємо трасування стеку до логів, якщо це потрібно для діагностики
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail if exc.detail is not None else exc.message},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Загальний обробник для всіх інших неперехоплених винятків.
    Логує повну помилку та повертає стандартизовану JSON-відповідь 500.
    """
    logger.error(
        f"Критична неперехоплена помилка на шляху '{request.url.path}': {exc}",
        exc_info=True # Завжди логуємо повне трасування для невідомих помилок
    )
    # TODO i18n: Translatable message
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Виникла непередбачена внутрішня помилка сервера. Будь ласка, спробуйте пізніше."},
    )


# --- Підключення маршрутизаторів (API Routers) ---
# TODO: Розкоментувати та налаштувати, коли маршрутизатори будуть створені.
# app.include_router(api_v1_router, prefix=settings.API_V1_STR)
# logger.info(f"Маршрутизатор api_v1_router підключено з префіксом '{settings.API_V1_STR}'.")

# Приклад підключення адмін-роутера (якщо є)
# app.include_router(admin_router, prefix="/admin", tags=["Admin"]) # tags - для групування в Swagger UI
# logger.info("Маршрутизатор admin_router підключено з префіксом '/admin'.")


# --- Кореневий ендпоінт (Health Check / Info) ---
@app.get("/", summary="Кореневий ендпоінт програми", tags=["Загальне"])
async def root():
    """
    Кореневий ендпоінт, який можна використовувати для перевірки стану
    (health check) або отримання базової інформації про програму.
    """
    # TODO i18n: Translatable message
    return {
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "status": "OK",
        "message": f"Ласкаво просимо до API '{settings.PROJECT_NAME}'!",
        "documentation_swagger": app.docs_url,
        "documentation_redoc": app.redoc_url
    }

logger.info(f"Екземпляр FastAPI '{settings.PROJECT_NAME}' створено та налаштовано.")

# Для запуску через `python backend/app/main.py` (НЕ рекомендується для продакшену)
if __name__ == "__main__":
    import uvicorn
    logger.info("Запуск програми через Uvicorn (тільки для локальної розробки)...")
    uvicorn.run(
        "backend.app.main:app", # Шлях до екземпляра FastAPI
        host="0.0.0.0",
        port=8000, # TODO: Порт можна винести в settings.py
        reload=True, # Увімкнути автоматичне перезавантаження при зміні коду
        log_level=settings.LOGGING_LEVEL.lower() # Рівень логування для Uvicorn
    )
