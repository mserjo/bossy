# backend/app/main.py
# -*- coding: utf-8 -*-
# # Головний модуль FastAPI програми Kudos (Virtus).
# #
# # Цей файл визначає та конфігурує основний екземпляр FastAPI (`app`),
# # який є точкою входу для ASGI-сервера (наприклад, Uvicorn).
# # Тут налаштовуються:
# # - Події життєвого циклу програми (startup/shutdown) за допомогою `lifespan`.
# #   - При старті: ініціалізація логування, підключення до Redis,
# #     опціональне створення таблиць БД (для розробки).
# #   - При завершенні: закриття з'єднань (наприклад, Redis).
# # - Middleware, зокрема CORS для обробки запитів з різних джерел.
# # - Глобальні обробники винятків для кастомних (`AppException`) та загальних помилок.
# # - Підключення основних маршрутизаторів API.
# # - Кореневий ендпоінт для перевірки стану або базової інформації.
# #
# # Екземпляр `app` ре-експортується з `backend.app.__init__.py`.

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager # Для нового стилю lifespan подій у FastAPI (з FastAPI 0.90.0+)

# Абсолютні імпорти з проекту
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import setup_logging, get_logger # get_logger для логування в цьому модулі
from backend.app.src.config.redis import get_redis_client, close_redis_client
# from backend.app.src.config.database import create_db_and_tables # Розкоментуйте, якщо потрібно створювати таблиці при старті (НЕ для продакшену)
from backend.app.src.core.exceptions import AppException

# TODO: Імпортувати головний маршрутизатор API, коли він буде створений в api/v1/api_router.py
# from backend.app.src.api.v1.api_router import api_router as api_v1_router
# from backend.app.src.api.admin.admin_router import admin_router # Приклад для адмін-панелі, якщо буде

# Ініціалізація логера для цього модуля (main.py)
# Важливо: setup_logging() має бути викликана до першого активного використання get_logger()
# в інших модулях, якщо вони імпортуються на рівні модуля і одразу логують.
# У цьому файлі ми викликаємо setup_logging() в lifespan події "startup".
logger = get_logger(__name__) # Отримуємо логер для main.py (назва логера буде 'main')

# --- Обробники подій життєвого циклу програми (Lifespan Events) ---
@asynccontextmanager
async def lifespan(current_app: FastAPI):
    """
    Асинхронний контекстний менеджер для подій життєвого циклу FastAPI.
    Код перед `yield` виконується при старті програми (startup).
    Код після `yield` виконується при завершенні програми (shutdown).
    """
    # --- Startup ---
    # Використовуємо print для найпершого повідомлення, оскільки логер може ще не бути повністю налаштований
    # або його вивід може бути перенаправлено/відключено на цьому етапі.
    print(f"Виконується запуск програми '{settings.PROJECT_NAME}'...")

    # 1. Налаштування системи логування
    setup_logging() # Застосовуємо конфігурацію логування з logging.py
    logger.info(f"Запуск програми '{settings.PROJECT_NAME}' в середовищі '{settings.ENVIRONMENT}' з рівнем логування '{settings.LOGGING_LEVEL}'.")

    # TODO i18n: Інтегрувати систему інтернаціоналізації:
    # 1. Додати middleware для визначення та встановлення локалі для кожного запиту
    #    (наприклад, використовуючи `get_user_locale` з `core.i18n` та `request.state`).
    # 2. Забезпечити доступ до функції перекладу `_()` в ендпоінтах
    #    (можливо, через залежність або контекст запиту).
    # 3. Ініціалізувати систему i18n (завантажити переклади JSON) при старті, якщо потрібно (наприклад, кешувати їх).
    #    Можливо, це вже обробляється в `core.i18n._()` при першому запиті до локалі.

    # 2. Ініціалізація та перевірка з'єднання з Redis
    try:
        await get_redis_client() # Ініціалізує та перевіряє з'єднання з Redis
        logger.info("Клієнт Redis успішно ініціалізовано та підключено.")
    except Exception as e:
        logger.error(f"Не вдалося ініціалізувати або підключитися до Redis під час запуску: {e}", exc_info=True)
        # Залежно від критичності Redis для роботи програми, тут можна або продовжити роботу з попередженням,
        # або завершити програму, якщо Redis є обов'язковою залежністю.
        # Наприклад: raise RuntimeError(f"Не вдалося підключитися до Redis ({e}), запуск програми скасовано.") from e

    # 3. Створення таблиць бази даних (ТІЛЬКИ для розробки/тестування, якщо не використовуються міграції Alembic)
    # УВАГА: У продакшен-середовищі для управління схемою БД слід ВИКЛЮЧНО використовувати Alembic.
    # Розкоментуйте наступні рядки, якщо це потрібно для локальної розробки або CI/CD для тестів,
    # але переконайтеся, що це не виконується в продакшені (наприклад, через умову `if settings.ENVIRONMENT == "development":`).
    if settings.ENVIRONMENT == "development": # Приклад умови
        try:
            logger.info("Спроба створення таблиць бази даних (тільки для середовища розробки)...")
            # Імпорт тут, щоб уникнути потенційних циклічних залежностей на рівні модуля,
            # особливо якщо `database.py` імпортує щось, що залежить від `main.app`.
            from backend.app.src.config.database import create_db_and_tables
            await create_db_and_tables(drop_first=False) # drop_first=True для повного перестворення
            logger.info("Таблиці бази даних перевірено/створено (якщо вони не існували).")
        except Exception as e:
            logger.error(f"Помилка під час створення таблиць бази даних у середовищі розробки: {e}", exc_info=True)

    logger.info(f"Програма '{settings.PROJECT_NAME}' успішно запущена та готова до роботи.")

    yield # Точка переходу; після цього виконується код при завершенні програми (shutdown)

    # --- Shutdown ---
    logger.info(f"Початок процесу завершення роботи програми '{settings.PROJECT_NAME}'...")

    # 1. Закриття з'єднання з Redis (якщо воно було ініціалізоване)
    await close_redis_client()
    # `close_redis_client` вже логує результат, тому тут додаткове логування не потрібне.

    logger.info(f"Програма '{settings.PROJECT_NAME}' успішно завершила роботу.")


# --- Створення екземпляра FastAPI ---
# Використовуємо `lifespan` для обробки подій startup/shutdown.
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        f"API для системи винагород та завдань '{settings.PROJECT_NAME}'. "
        f"Поточне середовище: {settings.ENVIRONMENT}."
        # TODO: Додати сюди більш детальний опис API, коли він буде сформований.
    ),
    version=getattr(settings, "PROJECT_VERSION", "0.1.0"), # TODO: Версію краще винести в settings.py або отримувати з git/pyproject.toml
    openapi_url=f"{settings.API_V1_STR}/openapi.json", # Шлях до схеми OpenAPI (JSON)
    docs_url=f"{settings.API_V1_STR}/docs", # Шлях до інтерактивної документації Swagger UI
    redoc_url=f"{settings.API_V1_STR}/redoc", # Шлях до альтернативної документації ReDoc
    lifespan=lifespan # Підключення обробника подій життєвого циклу
)

# --- Налаштування Middleware ---

# CORS (Cross-Origin Resource Sharing) Middleware
# Дозволяє або забороняє запити з інших доменів (браузерна політика безпеки).
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS], # Дозволені джерела (origins)
        allow_credentials=True, # Дозволити передачу кукі та заголовків автентифікації
        allow_methods=["*"],    # Дозволити всі стандартні HTTP методи (GET, POST, PUT, DELETE тощо)
        allow_headers=["*"],    # Дозволити всі заголовки в запитах
    )
    logger.info(f"Middleware CORS налаштовано з дозволеними джерелами: {settings.BACKEND_CORS_ORIGINS}")
else:
    # i18n: Log message for developers
    logger.warning(
        "Middleware CORS не налаштовано (BACKEND_CORS_ORIGINS не визначено або порожній). "
        "Це може бути небезпечно для продакшен-середовищ, якщо фронтенд знаходиться на іншому домені."
    )


# --- Глобальні обробники винятків (Exception Handlers) ---

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    Обробник для всіх кастомних винятків, що успадковуються від `AppException`.
    Повертає JSON-відповідь з відповідним статус-кодом та деталями помилки,
    визначеними у самому винятку.
    """
    # i18n: Log message for developers
    logger.warning(
        f"Обробка AppException: Статус={exc.status_code}, Повідомлення='{exc.message}', Деталі для клієнта='{exc.detail}' "
        f"для запиту: {request.method} {request.url.path}",
        exc_info=settings.DEBUG # Додаємо трасування стеку до логів, якщо DEBUG=True, для діагностики
    )
    return JSONResponse(
        status_code=exc.status_code,
        # Для клієнта завжди використовуємо поле `detail` з винятку,
        # оскільки `message` може містити більш технічну інформацію.
        content={"detail": exc.detail if exc.detail is not None else exc.message},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Загальний обробник для всіх інших неперехоплених стандартних винятків Python.
    Логує повну помилку з трасуванням стеку та повертає стандартизовану
    JSON-відповідь зі статусом 500 (Внутрішня помилка сервера).
    """
    # i18n: Log message for developers
    logger.error(
        f"Критична неперехоплена помилка '{type(exc).__name__}' на шляху '{request.url.path}': {exc}",
        exc_info=True # Завжди логуємо повне трасування для невідомих помилок
    )
    # TODO i18n: Translatable user-facing error message. "Виникла непередбачена внутрішня помилка сервера..."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Виникла непередбачена внутрішня помилка сервера. Будь ласка, спробуйте пізніше або зверніться до підтримки."},
    )


# --- Підключення маршрутизаторів (API Routers) ---
# Тут будуть підключатися основні роутери для різних частин API.
# TODO: Розкоментувати та налаштувати, коли маршрутизатори будуть створені.
# Наприклад:
# app.include_router(api_v1_router, prefix=settings.API_V1_STR)
# logger.info(f"Основний маршрутизатор API v1 підключено з префіксом '{settings.API_V1_STR}'.")

# Приклад підключення адмін-роутера (якщо такий буде):
# app.include_router(admin_router, prefix="/admin", tags=["Адміністративна панель"]) # tags - для групування в Swagger UI
# logger.info("Маршрутизатор для адміністративної панелі підключено з префіксом '/admin'.")


# --- Кореневий ендпоінт (Health Check / Info) ---
@app.get("/", summary="Кореневий ендпоінт: стан та інформація про програму", tags=["Загальне"])
async def root():
    """
    Кореневий ендпоінт, який можна використовувати для базової перевірки стану
    (health check) програми або отримання загальної інформації про API.
    """
    # TODO i18n: Translatable message for "message" field. "Ласкаво просимо до API..."
    return {
        "project_name": settings.PROJECT_NAME,
        "version": getattr(settings, "PROJECT_VERSION", "0.1.0"), # Використовуємо версію з налаштувань, якщо є
        "environment": settings.ENVIRONMENT,
        "status": "OK", # Простий індикатор, що програма працює
        "message": f"Ласкаво просимо до API '{settings.PROJECT_NAME}'!",
        "documentation_swagger": app.docs_url, # Посилання на Swagger UI
        "documentation_redoc": app.redoc_url    # Посилання на ReDoc
    }

# Це повідомлення логується один раз при імпорті модуля main, тобто при старті Uvicorn,
# ще до виконання lifespan подій.
logger.info(f"Екземпляр FastAPI '{settings.PROJECT_NAME}' створено та базово налаштовано. Подальша ініціалізація в lifespan.")

# Блок для запуску програми через `python backend/app/main.py` (для локальної розробки).
# УВАГА: Для продакшен-середовищ рекомендується використовувати Gunicorn + Uvicorn worker або інший ASGI-сервер.
if __name__ == "__main__":
    import uvicorn
    # i18n: Log message for developers
    logger.info("Запуск програми FastAPI через Uvicorn (тільки для локальної розробки)...")

    # TODO: Порт та хост можна також винести в `settings.py` для більшої гнучкості.
    # Наприклад: `host=settings.APP_HOST`, `port=settings.APP_PORT`.
    uvicorn.run(
        "backend.app.main:app", # Шлях до екземпляра FastAPI (пакет.модуль:змінна)
        host="0.0.0.0", # Слухати на всіх доступних мережевих інтерфейсах
        port=8000, # Стандартний порт для веб-сервісів (можна змінити)
        reload=True, # Увімкнути автоматичне перезавантаження сервера при зміні коду (для розробки)
        log_level=settings.LOGGING_LEVEL.lower() # Рівень логування для Uvicorn (синхронізуємо з налаштуваннями програми)
    )
