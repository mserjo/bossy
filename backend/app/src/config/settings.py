# backend/app/src/config/settings.py
# -*- coding: utf-8 -*-
# # Модуль конфігурації для FastAPI програми Kudos (Virtus).
# #
# # Відповідає за завантаження, валідацію та зберігання всіх налаштувань програми.
# # Налаштування завантажуються зі змінних середовища та/або файлу `.env`
# # за допомогою Pydantic BaseSettings, що забезпечує їх типізацію та валідацію.
# # Доступ до налаштувань здійснюється через екземпляр `settings` цього модуля.

from pathlib import Path
from typing import List, Optional, Union, Any
from pydantic import PostgresDsn, RedisDsn, field_validator, AnyHttpUrl, EmailStr, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
# from backend.app.src.config.logging import get_logger # Тимчасово закоментовано для уникнення циклічного імпорту

# Отримання логера для цього модуля - ТИМЧАСОВО ЗАКОМЕНТОВАНО
# logger = get_logger(__name__) # Якщо логер потрібен тут, його слід отримувати обережно, щоб уникнути циклічних імпортів.
                               # Зазвичай, конфігураційний модуль не логує сам себе під час ініціалізації.

# Визначення шляху до файлу .env
# Спочатку шукаємо у backend/.env, потім у kudos/.env (корінь проекту)
# Це дозволяє мати .env для розробки в backend/ і .env.prod на рівні вище для Docker.
dotenv_path_backend = Path(__file__).resolve().parent.parent.parent.parent / ".env" # шлях до backend/.env
dotenv_path_project_root = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env" # шлях до kudos/.env

if dotenv_path_backend.exists():
    dotenv_path = dotenv_path_backend
elif dotenv_path_project_root.exists():
    dotenv_path = dotenv_path_project_root
else:
    dotenv_path = None # .env файл не знайдено

if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path, override=True) # override=True дозволяє змінним середовища перезаписувати .env

class Settings(BaseSettings):
    """
    Клас для зберігання всіх налаштувань програми.
    Налаштування завантажуються зі змінних середовища та/або файлу .env.
    Pydantic `BaseSettings` забезпечує валідацію даних та приведення типів.
    """

    # --- Загальні налаштування програми ---
    PROJECT_NAME: str = "Kudos" # Назва проекту, використовується в OpenAPI, метаданих тощо.
    DEBUG: bool = False  # Режим налагодження (впливає на вивід помилок, логування). Встановіть False для продакшену.
    ENVIRONMENT: str = "development" # Середовище виконання (наприклад, development, staging, production).
    API_V1_STR: str = "/api/v1" # Базовий префікс для API версії 1.
    # ВАЖЛИВО: Секретний ключ для підписів кукі, сесій, CSRF токенів та інших потреб безпеки.
    # ПОТРІБНО ЗГЕНЕРУВАТИ НАДІЙНИЙ КЛЮЧ (напр. `openssl rand -hex 32`) ТА ЗБЕРІГАТИ ЙОГО В БЕЗПЕЦІ!
    # Цей ключ НЕ ПОВИНЕН мати значення за замовчуванням у відкритому коді для продакшену.
    SECRET_KEY: str # Приклад: "your_strong_random_secret_key_here"

    # --- Налаштування бази даних (PostgreSQL) ---
    POSTGRES_SERVER: str = "localhost" # Адреса (хост) сервера бази даних PostgreSQL.
    POSTGRES_PORT: int = 5432 # Порт сервера бази даних PostgreSQL.
    POSTGRES_USER: str = "postgres" # Ім'я користувача для підключення до бази даних.
    POSTGRES_PASSWORD: str = "password" # Пароль користувача для підключення до бази даних.
    POSTGRES_DB: str = "kudos_db" # Назва бази даних, до якої підключається додаток.
    DATABASE_URL: Optional[PostgresDsn] = None # Асинхронний URL для підключення до БД (автоматично збирається).

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Збирає асинхронний URL для підключення до PostgreSQL, якщо він не наданий явно."""
        if isinstance(v, str): # Якщо DATABASE_URL вже надано, використовуємо його
            return v
        data = info.data if info and hasattr(info, 'data') else {}
        user = data.get("POSTGRES_USER")
        password = data.get("POSTGRES_PASSWORD")
        server = data.get("POSTGRES_SERVER")
        port = data.get("POSTGRES_PORT")
        db_name = data.get("POSTGRES_DB")

        if not all([user, password, server, port, db_name]):
            # TODO i18n: Translatable error message
            raise ValueError(
                "Для DATABASE_URL необхідно встановити POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_SERVER, POSTGRES_PORT, POSTGRES_DB "
                "або надати повний DATABASE_URL."
            )
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg", # Використовуємо асинхронний драйвер asyncpg
            username=user, password=password, host=server, port=int(port),
            path=f"/{db_name.lstrip('/')}"
        ))

    # --- Синхронний URL для Alembic (офлайн режим) та інших синхронних задач ---
    SYNC_DATABASE_URL: Optional[PostgresDsn] = None # Синхронний URL для Alembic.

    @field_validator("SYNC_DATABASE_URL", mode="before")
    @classmethod
    def assemble_sync_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Збирає синхронний URL для підключення до PostgreSQL."""
        if isinstance(v, str):
            return v
        data = info.data if info and hasattr(info, 'data') else {}
        user = data.get("POSTGRES_USER")
        password = data.get("POSTGRES_PASSWORD")
        server = data.get("POSTGRES_SERVER")
        port = data.get("POSTGRES_PORT")
        db_name = data.get("POSTGRES_DB")

        if not all([user, password, server, port, db_name]):
            # Помилка вже буде оброблена валідатором DATABASE_URL.
            # Якщо DATABASE_URL не зміг зібратися, то і цей не зможе.
            # TODO i18n: Translatable error message
            raise ValueError("Неможливо зібрати SYNC_DATABASE_URL: відсутні основні компоненти БД.")
        return str(PostgresDsn.build(
            scheme="postgresql", # Використовуємо стандартний синхронний драйвер (psycopg2 зазвичай)
            username=user, password=password, host=server, port=int(port),
            path=f"/{db_name.lstrip('/')}"
        ))

    # --- Налаштування Redis ---
    REDIS_HOST: str = "localhost" # Адреса сервера Redis.
    REDIS_PORT: int = 6379 # Порт сервера Redis.
    REDIS_DB: int = 0 # Номер бази даних Redis для використання.
    REDIS_PASSWORD: Optional[str] = None # Пароль для Redis (None, якщо пароль не встановлено).
    REDIS_URL: Optional[RedisDsn] = None # URL для підключення до Redis (автоматично збирається).

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Збирає URL для підключення до Redis, якщо він не наданий явно."""
        if isinstance(v, str):
            return v
        data = info.data if info and hasattr(info, 'data') else {}
        host = data.get("REDIS_HOST")
        port = data.get("REDIS_PORT")
        db = data.get("REDIS_DB")
        password = data.get("REDIS_PASSWORD")

        if not host or port is None or db is None: # port та db можуть бути 0, тому перевірка на None
             # TODO i18n: Translatable error message
            raise ValueError("Для REDIS_URL необхідно встановити REDIS_HOST, REDIS_PORT, REDIS_DB або надати повний REDIS_URL.")

        scheme = "redis"
        if password:
            return str(RedisDsn(f"{scheme}://:{password}@{host}:{port}/{db}"))
        return str(RedisDsn(f"{scheme}://{host}:{port}/{db}"))

    # --- Налаштування JWT автентифікації ---
    # ВАЖЛИВО: Секретний ключ для генерації та валідації JWT токенів.
    # ПОТРІБНО ЗГЕНЕРУВАТИ НАДІЙНИЙ КЛЮЧ (напр. `openssl rand -hex 32`) ТА ЗБЕРІГАТИ ЙОГО В БЕЗПЕЦІ!
    # Цей ключ НЕ ПОВИНЕН мати значення за замовчуванням у відкритому коді для продакшену.
    JWT_SECRET_KEY: str # Приклад: "your_strong_random_jwt_secret_key_here"
    JWT_ALGORITHM: str = "HS256" # Алгоритм підпису для JWT (HS256, RS256 тощо).
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 # Час життя Access токена у хвилинах.
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7 # Час життя Refresh токена у днях.
    JWT_ISSUER: str = "kudos.example.com"  # Видавець токена (вкажіть ваш домен або ідентифікатор сервісу).
    JWT_AUDIENCE: str = "kudos.example.com" # Аудиторія токена (вкажіть ваш домен або сервіс, для якого призначений токен).

    # --- Налаштування CORS (Cross-Origin Resource Sharing) ---
    # Дозволяє запити з вказаних джерел (origins).
    # Для розробки можна використовувати ["*"] (будь-яке джерело), але це НЕБЕЗПЕЧНО для продакшену.
    # Для продакшену ОБОВ'ЯЗКОВО вкажіть конкретні дозволені джерела, наприклад:
    # ["https://your-frontend.com", "https://admin.your-frontend.com"]
    BACKEND_CORS_ORIGINS: List[Union[AnyHttpUrl, str]] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Обробляє значення BACKEND_CORS_ORIGINS, перетворюючи рядок у список, якщо необхідно."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if not v.strip(): # Якщо рядок порожній або складається з пробілів
                return [] # Повертаємо порожній список
            # Якщо рядок виглядає як список JSON (наприклад, "['http://localhost:3000']"), пробуємо розпарсити
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    return json.loads(v)
                except json.JSONDecodeError:
                    # Якщо не вдалося розпарсити як JSON, переходимо до розділення комами
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        # TODO i18n: Translatable error message
        raise ValueError("BACKEND_CORS_ORIGINS має бути списком URL-адрес або рядком URL-адрес, розділених комами.")

    # --- Налаштування початкового суперкористувача ---
    FIRST_SUPERUSER_EMAIL: EmailStr = "admin@example.com" # Email початкового суперкористувача.
    FIRST_SUPERUSER_PASSWORD: str = "supersecret" # Пароль початкового суперкористувача (змінити для продакшену!).

    # --- Налаштування системних користувачів ---
    SYSTEM_USER_ODIN_EMAIL: EmailStr = "odin@system.kudos" # Email системного користувача "Odin" (суперадмін).
    SYSTEM_USER_SHADOW_EMAIL: EmailStr = "shadow@system.kudos" # Email системного користувача "Shadow" (для фонових завдань).

    # --- Налаштування сховища файлів ---
    # Корінь проекту (директорія, що містить `backend/`, `frontend/` тощо)
    PROJECT_ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent.parent
    # Корінь вихідного коду додатка (backend/app/src/)
    APP_SOURCE_ROOT_DIR: Path = Path(__file__).resolve().parent.parent
    # Директорія для статичних файлів, що обслуговуються додатком (всередині backend/app/src/static/)
    STATIC_FILES_DIR: Path = APP_SOURCE_ROOT_DIR / "static"
    # Директорія для завантажених користувачами файлів (всередині .../static/uploads/)
    UPLOADED_FILES_DIR: Path = STATIC_FILES_DIR / "uploads"
    MAX_FILE_SIZE_MB: int = 10 # Максимальний розмір файлу для завантаження (в мегабайтах).

    # --- Налаштування електронної пошти (SMTP) ---
    # Для активації відправки пошти, встановіть SMTP_HOST, SMTP_USER, SMTP_PASSWORD.
    SMTP_TLS: bool = True # Використовувати TLS для SMTP (рекомендовано).
    SMTP_PORT: Optional[int] = 587 # Порт SMTP сервера (зазвичай 587 для TLS, 465 для SSL, 25 для нешифрованого).
    SMTP_HOST: Optional[str] = None # Адреса SMTP сервера (наприклад, "smtp.gmail.com").
    SMTP_USER: Optional[EmailStr] = None # Ім'я користувача для автентифікації на SMTP сервері.
    SMTP_PASSWORD: Optional[str] = None # Пароль для автентифікації на SMTP сервері.
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None # Email адреса відправника (з якої надсилатимуться листи).
    EMAILS_FROM_NAME: Optional[str] = PROJECT_NAME # Ім'я відправника листів (за замовчуванням назва проекту).

    # --- Налаштування логування ---
    LOGGING_LEVEL: str = "INFO" # Рівень логування (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    LOG_TO_FILE: bool = False # Чи зберігати логи у файл. Для Docker зазвичай False (логи в stdout/stderr).
    LOG_DIR: Path = PROJECT_ROOT_DIR / "logs" # Директорія для файлів логів (якщо LOG_TO_FILE=True). Знаходиться в корені проекту.
    LOG_APP_FILE: str = "app.log" # Назва файлу для основних логів програми.
    LOG_ERROR_FILE: str = "error.log" # Назва файлу для логів помилок.
    LOG_MAX_BYTES: int = 1024 * 1024 * 10 # Максимальний розмір файлу логів до ротації (тут 10MB).
    LOG_BACKUP_COUNT: int = 5 # Кількість резервних копій файлів логів при ротації.

    model_config = SettingsConfigDict(
        env_file=str(dotenv_path) if dotenv_path else None, # Шлях до .env файлу (або None, якщо не знайдено)
        env_file_encoding='utf-8', # Кодування .env файлу
        extra='ignore', # Ігнорувати зайві поля в .env файлі (не викликати помилку)
        case_sensitive=False # Чутливість до регістру змінних середовища (False - нечутливі)
    )

# Створення єдиного екземпляра налаштувань для всього додатку
settings = Settings()

# Створення директорій для логів та завантажених файлів, якщо їх не існує.
# Це виконується при імпорті модуля, забезпечуючи наявність директорій.
if settings.LOG_TO_FILE:
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADED_FILES_DIR.mkdir(parents=True, exist_ok=True)


# Блок для діагностики та перевірки завантажених налаштувань при прямому запуску файлу.
if __name__ == "__main__":
    print(f"Використовується .env файл: {dotenv_path if dotenv_path else 'Не знайдено'}")
    if dotenv_path:
        print(f"Чи існує .env файл: {dotenv_path.exists()}")
    print("--- Завантажені налаштування програми ---")
    # Виводимо значення, приховуючи чутливі дані
    for key, value in settings.model_dump().items():
        if "password" in key.lower() or "secret" in key.lower() or "key"in key.lower():
            print(f"{key.upper()}: ******")
        else:
            print(f"{key.upper()}: {value}")
    print(f"Повний шлях до директорії завантажених файлів: {settings.UPLOADED_FILES_DIR.resolve()}")
    if settings.LOG_TO_FILE:
        print(f"Повний шлях до директорії логів: {settings.LOG_DIR.resolve()}")
    else:
        print("Логування у файл вимкнено (LOG_TO_FILE=False).")
