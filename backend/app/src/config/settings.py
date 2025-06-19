# backend/app/src/config/settings.py
# -*- coding: utf-8 -*-
"""Конфігурація додатку FastAPI.

Цей модуль відповідає за завантаження, валідацію та зберігання всіх налаштувань програми.
Налаштування завантажуються зі змінних середовища, які можуть бути визначені
безпосередньо або за допомогою файлу `.env`. Бібліотека Pydantic використовується для валідації
та типізації налаштувань, забезпечуючи їх коректність під час запуску програми.

Основні групи налаштувань:
- Загальні параметри програми (назва, режим налагодження, середовище).
- Параметри підключення до бази даних PostgreSQL (асинхронний та синхронний URL).
- Параметри підключення до Redis.
- Налаштування JWT автентифікації (секретні ключі, алгоритм, час життя токенів).
- Налаштування CORS (Cross-Origin Resource Sharing).
- Параметри для початкового суперкористувача.
- Налаштування шляхів для статичних файлів та завантажень.
- Параметри для відправки електронної пошти (SMTP).
- Конфігурація системи логування (рівень, файли, ротація).

Використання:
Після ініціалізації, екземпляр `settings` цього модуля містить усі
доступні налаштування і може бути імпортований в інші частини програми
через `from backend.app.src.config import settings`.
"""
import json # Для обробки BACKEND_CORS_ORIGINS у форматі JSON-рядка
from pathlib import Path
from typing import Any, List, Optional, Union

from dotenv import load_dotenv
from pydantic import (AnyHttpUrl, EmailStr, PostgresDsn, RedisDsn,
                        ValidationInfo, field_validator)
from pydantic_settings import BaseSettings, SettingsConfigDict
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# --- Визначення шляху до файлу .env ---
# Пріоритет: спочатку шукаємо .env у директорії `backend/`, потім у корені проекту.
# Це дозволяє мати локальний .env для розробки в `backend/`, який не комітиться,
# та загальний .env на рівні проекту для CI/CD або інших середовищ.
# Директорія `backend/`
BACKEND_DIR_PATH = Path(__file__).resolve().parent.parent.parent.parent
# Директорія, що містить `backend/` (корінь проекту)
PROJECT_ROOT_PATH = BACKEND_DIR_PATH.parent

dotenv_path_backend = BACKEND_DIR_PATH / ".env"
dotenv_path_project_root = PROJECT_ROOT_PATH / ".env"

# Визначаємо, який .env файл використовувати
if dotenv_path_backend.exists():
    DOTENV_PATH: Optional[Path] = dotenv_path_backend
elif dotenv_path_project_root.exists():
    DOTENV_PATH = dotenv_path_project_root
else:
    DOTENV_PATH = None # .env файл не знайдено

# Завантаження змінних середовища з .env файлу, якщо він знайдений.
# `override=True` означає, що змінні з .env файлу перезапишуть системні змінні середовища.
# Це зручно для локальної розробки. Для продакшену часто `override=False` або .env не використовується.
if DOTENV_PATH:
    logger.info("Завантаження змінних середовища з файлу: %s (override=True)", DOTENV_PATH)
    load_dotenv(dotenv_path=DOTENV_PATH, override=True)
else:
    logger.info("Файл .env не знайдено. Налаштування будуть завантажені тільки зі змінних середовища.")


class Settings(BaseSettings):
    """Клас для зберігання всіх налаштувань програми.

    Налаштування завантажуються зі змінних середовища та/або файлу .env.
    Pydantic `BaseSettings` забезпечує валідацію даних та приведення типів.
    """

    # --- Загальні налаштування програми ---
    PROJECT_NAME: str = "Kudos Backend"
    DEBUG: bool = False  # Режим налагодження. Впливає на логування, показ помилок тощо.
    ENVIRONMENT: str = "development" # Середовище виконання (наприклад, development, staging, production)
    API_V1_STR: str = "/api/v1" # Префікс для API версії 1

    # ВАЖЛИВО: Секретний ключ для підписів кукі, сесій, CSRF токенів та інших потреб безпеки.
    # ПОТРІБНО ЗГЕНЕРУВАТИ НАДІЙНИЙ КЛЮЧ ТА ЗБЕРІГАТИ ЙОГО В БЕЗПЕЦІ!
    # Приклад генерації: `openssl rand -hex 32`
    # Цей ключ НЕ ПОВИНЕН мати значення за замовчуванням у продакшені; він має бути встановлений через змінну середовища.
    SECRET_KEY: str # Немає значення за замовчуванням, має бути встановлено в середовищі

    # --- Налаштування бази даних (PostgreSQL) ---
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "112233"
    POSTGRES_DB: str = "bossy"
    # Асинхронний URL для підключення до бази даних (автоматично збирається)
    DATABASE_URL: Optional[PostgresDsn] = None
    # Синхронний URL для Alembic (офлайн режим) та інших синхронних операцій
    SYNC_DATABASE_URL: Optional[PostgresDsn] = None
    ECHO_SQL: bool = False # Чи логувати SQL запити SQLAlchemy (встановлюється в True, якщо DEBUG=True, в database.py)
    DB_POOL_SIZE: int = 10 # Розмір пулу з'єднань БД
    DB_MAX_OVERFLOW: int = 20 # Максимальна кількість додаткових з'єднань понад DB_POOL_SIZE

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Збирає URL для асинхронного підключення до PostgreSQL, якщо він не наданий явно."""
        if isinstance(v, str):
            return v
        values = info.data # Pydantic v2 надає доступ до даних через info.data
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg", # Використовуємо асинхронний драйвер asyncpg
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB', '').lstrip('/')}",
        ))

    @field_validator("SYNC_DATABASE_URL", mode="before")
    @classmethod
    def assemble_sync_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Збирає URL для синхронного підключення до PostgreSQL (для Alembic)."""
        if isinstance(v, str):
            return v
        values = info.data
        return str(PostgresDsn.build(
            scheme="postgresql", # Використовуємо стандартний синхронний драйвер (psycopg2)
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB', '').lstrip('/')}",
        ))

    # --- Налаштування Redis ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    # URL для підключення до Redis (автоматично збирається)
    REDIS_URL: Optional[RedisDsn] = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Збирає URL для підключення до Redis, якщо він не наданий явно."""
        if isinstance(v, str):
            return v
        values = info.data
        scheme = "redis"
        # Pydantic RedisDsn автоматично додасть пароль, якщо він є у URL
        # redis://:password@host:port/db
        if values.get("REDIS_PASSWORD"):
            return str(RedisDsn(f"{scheme}://:{values.get('REDIS_PASSWORD')}@{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"))
        return str(RedisDsn(f"{scheme}://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"))

    # --- Налаштування використання Redis та Celery ---
    USE_REDIS: bool = True  # Чи використовувати Redis (для кешування, черг тощо)
    USE_CELERY: bool = False # Чи використовувати Celery для фонових завдань (за замовчуванням False)

    # --- Налаштування JWT автентифікації ---
    # ВАЖЛИВО: Секретний ключ для генерації JWT токенів.
    # ПОТРІБНО ЗГЕНЕРУВАТИ НАДІЙНИЙ КЛЮЧ ТА ЗБЕРІГАТИ ЙОГО В БЕЗПЕЦІ!
    # Приклад генерації: `openssl rand -hex 32`
    JWT_SECRET_KEY: str # Немає значення за замовчуванням
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 1 # 1 день
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7 # 7 днів
    JWT_ISSUER: str = "your.domain.com"  # TODO: Замінити на реальний домен видавця
    JWT_AUDIENCE: str = "your.domain.com" # TODO: Замінити на реальну аудиторію

    # --- Налаштування для Refresh Token Cookie ---
    REFRESH_TOKEN_COOKIE_KEY: str = "refreshToken" # Ключ (назва) cookie для refresh token
    REFRESH_TOKEN_COOKIE_SECURE: bool = True      # Чи встановлювати Secure прапорець для cookie (True для HTTPS)
    REFRESH_TOKEN_COOKIE_SAMESITE: str = "lax"    # SameSite атрибут для cookie ('lax', 'strict', 'none')
    # REFRESH_TOKEN_EXPIRE_SECONDS вже є (неявно через REFRESH_TOKEN_EXPIRE_DAYS)

    # --- Налаштування CORS (Cross-Origin Resource Sharing) ---
    # Дозволяє запити з вказаних джерел.
    # Для розробки можна використовувати `["*"]` (будь-яке джерело), але це небезпечно для продакшену.
    # Для продакшену ОБОВ'ЯЗКОВО вкажіть конкретні дозволені джерела.
    BACKEND_CORS_ORIGINS: List[Union[AnyHttpUrl, str]] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Обробляє значення `BACKEND_CORS_ORIGINS`, перетворюючи рядок у список."""
        if isinstance(v, list):
            return v # Якщо вже список, повертаємо як є
        if isinstance(v, str):
            # Якщо рядок виглядає як список JSON (наприклад, "['http://localhost:3000']"), пробуємо розпарсити
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    logger.warning(
                        "Не вдалося розпарсити BACKEND_CORS_ORIGINS як JSON-рядок: '%s'. "
                        "Спробуємо розділити за комами.", v
                    )
            # Розділяємо рядок за комами, видаляючи зайві пробіли
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        # Якщо тип не підтримується, викликаємо помилку
        raise ValueError(
            "BACKEND_CORS_ORIGINS має бути списком URL-адрес або рядком, "
            "розділеним комами (можливо, у форматі JSON-списку)."
        )

    # --- Налаштування початкового суперкористувача ---
    FIRST_SUPERUSER_EMAIL: EmailStr = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "SuperSecretPassword1!" # TODO: Змінити для продакшену або вимагати встановлення через env

    # --- Налаштування системних користувачів (якщо потрібні) ---
    # SYSTEM_USER_ODIN_EMAIL: EmailStr = "odin@system.yourdomain"
    # SYSTEM_USER_SHADOW_EMAIL: EmailStr = "shadow@system.yourdomain"

    # --- Налаштування шляхів та файлів ---
    # Корінь проекту (директорія, що містить `backend/`)
    PROJECT_ROOT_DIR: Path = PROJECT_ROOT_PATH
    # Корінь додатка (backend/app/src/)
    APP_SOURCE_ROOT_DIR: Path = Path(__file__).resolve().parent.parent
    STATIC_FILES_DIR: Path = APP_SOURCE_ROOT_DIR / "static"
    UPLOADED_FILES_DIR: Path = STATIC_FILES_DIR / "uploads" # Директорія для завантажених файлів
    MAX_FILE_SIZE_MB: int = 10 # Максимальний розмір файлу для завантаження (в мегабайтах)

    # --- Налаштування електронної пошти (SMTP) ---
    # Для активації відправки пошти, встановіть SMTP_ENABLED=True та інші параметри SMTP.
    SMTP_ENABLED: bool = False
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False # Якщо ваш сервер використовує SSL замість TLS на окремому порті (наприклад, 465)
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[EmailStr] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None # Email адреса відправника за замовчуванням
    EMAILS_FROM_NAME: Optional[str] = PROJECT_NAME # Ім'я відправника листів за замовчуванням

    # --- Налаштування логування ---
    LOGGING_LEVEL: str = "INFO" # Рівень логування: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_TO_FILE: bool = False # Чи зберігати логи у файл. Рекомендовано False для Docker (логи в stdout).
    LOG_DIR: Path = PROJECT_ROOT_DIR / "logs" # Директорія для файлів логів (якщо LOG_TO_FILE=True).
    LOG_APP_FILE: str = "app.log" # Назва файлу для логів програми
    LOG_ERROR_FILE: str = "error.log" # Назва файлу для логів помилок
    LOG_MAX_BYTES: int = 1024 * 1024 * 10 # Максимальний розмір файлу логів (10MB)
    LOG_BACKUP_COUNT: int = 5 # Кількість резервних копій файлів логів

    # Конфігурація моделі Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=str(DOTENV_PATH) if DOTENV_PATH and DOTENV_PATH.exists() else None,
        env_file_encoding='utf-8',
        extra='ignore', # Ігнорувати зайві поля в .env або змінних середовища
        case_sensitive=False, # Чутливість до регістру імен змінних середовища (False - нечутливі)
    )

# Створення єдиного екземпляра налаштувань, який буде використовуватися у всьому додатку.
# Це дозволяє завантажити та валідувати налаштування один раз при старті.
settings = Settings()

# Створення директорій для логів та завантажених файлів, якщо їх не існує
# та якщо відповідні опції увімкнені.
if settings.LOG_TO_FILE:
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Директорію для логів перевірено/створено: %s", settings.LOG_DIR.resolve())

# Директорія для завантажених файлів створюється завжди, оскільки вона може знадобитися.
settings.UPLOADED_FILES_DIR.mkdir(parents=True, exist_ok=True)
logger.info("Директорію для завантажених файлів перевірено/створено: %s", settings.UPLOADED_FILES_DIR.resolve())


# Блок для демонстрації завантажених налаштувань при прямому запуску файлу.
if __name__ == "__main__":
    logger.info("Використовується .env файл: %s", DOTENV_PATH if DOTENV_PATH else "Не знайдено або не використовується")
    if DOTENV_PATH:
        logger.info("Чи існує .env файл за вказаним шляхом: %s", DOTENV_PATH.exists())

    logger.info("--- Завантажені налаштування програми (`settings`) ---")
    # Виводимо значення, приховуючи чутливі дані, такі як паролі та секретні ключі.
    for key, value in settings.model_dump().items():
        is_sensitive = any(
            sensitive_keyword in key.lower()
            for sensitive_keyword in ("password", "secret", "token", "key", "dsn", "url")
        )
        # Для DATABASE_URL та REDIS_URL показуємо тільки частину без креданлів, якщо це можливо
        if key in ("DATABASE_URL", "SYNC_DATABASE_URL") and isinstance(value, PostgresDsn):
            display_value = f"{value.scheme}://{value.username}:******@{value.host}:{value.port or ''}{value.path}"
        elif key == "REDIS_URL" and isinstance(value, RedisDsn):
            display_value = f"{value.scheme}://******@{value.host}:{value.port or ''}/{value.path}"
        elif is_sensitive and isinstance(value, str):
            display_value = f"{value[:2]}******{value[-2:]}" if len(value) > 4 else "******"
        elif is_sensitive and value is not None: # Catches non-string sensitive values
            display_value = "******"
        elif key in ("REFRESH_TOKEN_COOKIE_KEY", "REFRESH_TOKEN_COOKIE_SECURE", "REFRESH_TOKEN_COOKIE_SAMESITE"):
            # Ці поля не є чутливими, відображаємо їх як є
            display_value = value
        else: # Default for non-sensitive or already handled sensitive values
            display_value = value

        logger.info("%s: %s", key, display_value)

    logger.info("Повний шлях до директорії проекту (PROJECT_ROOT_DIR): %s", settings.PROJECT_ROOT_DIR.resolve())
    logger.info("Повний шлях до директорії вихідного коду додатка (APP_SOURCE_ROOT_DIR): %s", settings.APP_SOURCE_ROOT_DIR.resolve())
    logger.info("Повний шлях до директорії статичних файлів (STATIC_FILES_DIR): %s", settings.STATIC_FILES_DIR.resolve())
    logger.info("Повний шлях до директорії завантажених файлів (UPLOADED_FILES_DIR): %s", settings.UPLOADED_FILES_DIR.resolve())
    logger.info("Повний шлях до директорії логів (LOG_DIR, якщо LOG_TO_FILE=True): %s", settings.LOG_DIR.resolve() if settings.LOG_TO_FILE else "Не використовується")
