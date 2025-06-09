# /backend/app/src/config/settings.py
"""
Конфігурація FastAPI програми Kudos.

Цей модуль відповідає за завантаження, валідацію та зберігання всіх налаштувань програми.
Налаштування завантажуються зі змінних середовища, які можуть бути визначені
безпосередньо або за допомогою файлу `.env`. Pydantic використовується для валідації
та типізації налаштувань, забезпечуючи їх коректність під час запуску програми.

Основні групи налаштувань:
- Загальні параметри програми (назва, режим налагодження, середовище).
- Параметри підключення до бази даних PostgreSQL.
- Параметри підключення до Redis.
- Налаштування JWT автентифікації.
- Налаштування CORS.
- Параметри для початкового суперкористувача та системних користувачів.
- Налаштування для зберігання файлів.
- Параметри для відправки електронної пошти (SMTP).
- Конфігурація системи логування.

Використання:
Після ініціалізації, екземпляр `settings` цього модуля містить усі
доступні налаштування і може бути імпортований в інші частини програми.
"""
from pathlib import Path
from typing import List, Optional, Union, Any
from pydantic import PostgresDsn, RedisDsn, field_validator, AnyHttpUrl, EmailStr, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Визначення шляху до файлу .env
# Спочатку шукаємо у backend/.env, потім у kudos/.env (корінь проекту)
dotenv_path_backend = Path(__file__).resolve().parent.parent.parent.parent / ".env" # шлях до backend/.env
dotenv_path_project_root = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env" # шлях до kudos/.env

if dotenv_path_backend.exists():
    dotenv_path = dotenv_path_backend
elif dotenv_path_project_root.exists():
    dotenv_path = dotenv_path_project_root
else:
    dotenv_path = None # .env файл не знайдено

if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path, override=True)

class Settings(BaseSettings):
    """
    Клас для зберігання всіх налаштувань програми.
    Налаштування завантажуються зі змінних середовища та/або файлу .env.
    Pydantic `BaseSettings` забезпечує валідацію даних та приведення типів.
    """

    # --- Загальні налаштування програми ---
    PROJECT_NAME: str = "Kudos" # Назва проекту
    DEBUG: bool = False  # Режим налагодження (True/False)
    ENVIRONMENT: str = "development" # Середовище виконання (development, staging, production)
    API_V1_STR: str = "/api/v1" # Префікс для API версії 1
    # ВАЖЛИВО: Секретний ключ для підписів кукі, сесій та інших потреб безпеки.
    # ПОТРІБНО ЗГЕНЕРУВАТИ НАДІЙНИЙ КЛЮЧ ТА ЗБЕРІГАТИ ЙОГО В БЕЗПЕЦІ!
    # Приклад генерації: openssl rand -hex 32
    # Цей ключ НЕ ПОВИНЕН мати значення за замовчуванням в продакшені.
    SECRET_KEY: str
    # --- Налаштування бази даних (PostgreSQL) ---
    POSTGRES_SERVER: str = "localhost" # Адреса сервера бази даних
    POSTGRES_PORT: int = 5432 # Порт сервера бази даних
    POSTGRES_USER: str = "postgres" # Ім'я користувача бази даних
    POSTGRES_PASSWORD: str = "password" # Пароль користувача бази даних
    POSTGRES_DB: str = "kudos_db" # Назва бази даних
    DATABASE_URL: Optional[PostgresDsn] = None # URL для підключення до бази даних (автоматично збирається)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Збирає URL для підключення до PostgreSQL, якщо він не наданий явно."""
        if isinstance(v, str): # Якщо DATABASE_URL вже надано, використовуємо його
            return v
        # Отримуємо дані з інших полів моделі для побудови URL
        data = info.data if info and hasattr(info, 'data') else {}
        user = data.get("POSTGRES_USER", "postgres")
        password = data.get("POSTGRES_PASSWORD", "password")
        server = data.get("POSTGRES_SERVER", "localhost")
        port = data.get("POSTGRES_PORT", 5432)
        db_name = data.get("POSTGRES_DB", "kudos_db")

        if not all([user, password, server, db_name]):
            # TODO i18n: Translatable message
            raise ValueError(
                "Необхідно встановити POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_SERVER, POSTGRES_DB "
                "або надати повний DATABASE_URL для підключення до PostgreSQL."
            )

        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg", # Використовуємо асинхронний драйвер asyncpg
            username=user,
            password=password,
            host=server,
            port=int(port), # Порт має бути числом
            path=f"/{db_name.lstrip('/')}", # Шлях до бази даних (видаляємо можливий слеш на початку)
        ))

    # --- Налаштування Redis ---
    REDIS_HOST: str = "localhost" # Адреса сервера Redis
    REDIS_PORT: int = 6379 # Порт сервера Redis
    REDIS_DB: int = 0 # Номер бази даних Redis
    REDIS_PASSWORD: Optional[str] = None # Пароль для Redis (якщо є)
    REDIS_URL: Optional[RedisDsn] = None # URL для підключення до Redis (автоматично збирається)

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Збирає URL для підключення до Redis, якщо він не наданий явно."""
        if isinstance(v, str): # Якщо REDIS_URL вже надано, використовуємо його
            return v
        # Отримуємо дані з інших полів моделі для побудови URL
        data = info.data if info and hasattr(info, 'data') else {}
        host = data.get("REDIS_HOST", "localhost")
        port = data.get("REDIS_PORT", 6379)
        db = data.get("REDIS_DB", 0)
        password = data.get("REDIS_PASSWORD")

        if not host:
            # TODO i18n: Translatable message
            raise ValueError(
                "Необхідно встановити REDIS_HOST або надати повний REDIS_URL для підключення до Redis."
            )

        scheme = "redis"
        if password: # Якщо пароль надано, додаємо його до URL
            return str(RedisDsn(f"{scheme}://:{password}@{host}:{port}/{db}"))
        return str(RedisDsn(f"{scheme}://{host}:{port}/{db}")) # URL без пароля

    # --- Налаштування JWT автентифікації ---
    # ВАЖЛИВО: Секретний ключ для генерації JWT токенів.
    # ПОТРІБНО ЗГЕНЕРУВАТИ НАДІЙНИЙ КЛЮЧ ТА ЗБЕРІГАТИ ЙОГО В БЕЗПЕЦІ!
    # Приклад генерації: openssl rand -hex 32
    # Цей ключ НЕ ПОВИНЕН мати значення за замовчуванням в продакшені.
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256" # Алгоритм шифрування для JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 # Час життя Access токена у хвилинах
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7 # Час життя Refresh токена у днях
    JWT_ISSUER: str = "kudos.example.com"  # Видавець токена (вкажіть ваш домен)
    JWT_AUDIENCE: str = "kudos.example.com" # Аудиторія токена (вкажіть ваш домен або сервіс)

    # --- Налаштування CORS (Cross-Origin Resource Sharing) ---
    # Дозволяє запити з вказаних джерел.
    # Для розробки можна використовувати ["*"] (будь-яке джерело).
    # Для продакшену ОБОВ'ЯЗКОВО вкажіть конкретні дозволені джерела, наприклад:
    # ["https://your-frontend.com", "https://admin.your-frontend.com"]
    BACKEND_CORS_ORIGINS: List[Union[AnyHttpUrl, str]] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Обробляє значення BACKEND_CORS_ORIGINS, перетворюючи рядок у список."""
        if isinstance(v, list): # Якщо вже список, повертаємо як є
            return v
        if isinstance(v, str):
            # Якщо рядок виглядає як список JSON (наприклад, "['http://localhost:3000']"), пробуємо розпарсити
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    return json.loads(v)
                except json.JSONDecodeError:
                    # Якщо не вдалося розпарсити як JSON, переходимо до розділення комами
                    pass
            # Розділяємо рядок за комами, видаляючи зайві пробіли
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        # Якщо тип не підтримується, викликаємо помилку
        # TODO i18n: Translatable message
        raise ValueError("BACKEND_CORS_ORIGINS має бути списком URL-адрес або рядком, розділеним комами.")

    # --- Налаштування початкового суперкористувача ---
    FIRST_SUPERUSER_EMAIL: EmailStr = "admin@example.com" # Email початкового суперкористувача
    FIRST_SUPERUSER_PASSWORD: str = "supersecret" # Пароль початкового суперкористувача (змінити для продакшену)

    # --- Налаштування системних користувачів ---
    SYSTEM_USER_ODIN_EMAIL: EmailStr = "odin@system.kudos" # Email системного користувача Odin (суперадмін)
    SYSTEM_USER_SHADOW_EMAIL: EmailStr = "shadow@system.kudos" # Email системного користувача Shadow (для фонових завдань)

    # --- Налаштування сховища файлів ---
    # Корінь проекту (kudos/) - використовується для логів, якщо LOG_TO_FILE=True
    PROJECT_ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent.parent
    # Корінь додатка (backend/app/src/) - для визначення шляхів до статичних файлів всередині додатка
    APP_SOURCE_ROOT_DIR: Path = Path(__file__).resolve().parent.parent
    STATIC_FILES_DIR: Path = APP_SOURCE_ROOT_DIR / "static" # Директорія для статичних файлів всередині /app/src/
    UPLOADED_FILES_DIR: Path = STATIC_FILES_DIR / "uploads" # Директорія для завантажених файлів всередині /app/src/static/
    MAX_FILE_SIZE_MB: int = 10 # Максимальний розмір файлу для завантаження (в мегабайтах)

    # --- Налаштування електронної пошти (SMTP) ---
    # Для активації відправки пошти, встановіть SMTP_HOST, SMTP_USER, SMTP_PASSWORD.
    SMTP_TLS: bool = True # Використовувати TLS для SMTP
    SMTP_PORT: Optional[int] = 587 # Порт SMTP сервера
    SMTP_HOST: Optional[str] = None # Адреса SMTP сервера
    SMTP_USER: Optional[EmailStr] = None # Ім'я користувача для SMTP
    SMTP_PASSWORD: Optional[str] = None # Пароль для SMTP
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None # Email адреса відправника
    EMAILS_FROM_NAME: Optional[str] = "Kudos System" # Ім'я відправника листів

    # --- Налаштування логування ---
    LOGGING_LEVEL: str = "INFO" # Рівень логування (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_TO_FILE: bool = False # Чи зберігати логи у файл (True/False). Рекомендовано False для Docker, логи в stdout.
    LOG_DIR: Path = PROJECT_ROOT_DIR / "logs" # Директорія для файлів логів (якщо LOG_TO_FILE=True). Знаходиться в корені проекту kudos/logs.
    LOG_APP_FILE: str = "app.log" # Назва файлу для логів програми
    LOG_ERROR_FILE: str = "error.log" # Назва файлу для логів помилок
    LOG_MAX_BYTES: int = 1024 * 1024 * 10 # Максимальний розмір файлу логів (10MB)
    LOG_BACKUP_COUNT: int = 5 # Кількість резервних копій файлів логів

    model_config = SettingsConfigDict(
        env_file=str(dotenv_path) if dotenv_path else None, # Шлях до .env файлу
        env_file_encoding='utf-8', # Кодування .env файлу
        extra='ignore', # Ігнорувати зайві поля в .env
        case_sensitive=False # Чутливість до регістру змінних середовища
    )

settings = Settings()

# Створення директорій для логів та завантажених файлів, якщо їх не існує
if settings.LOG_TO_FILE:
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADED_FILES_DIR.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print(f"Використовується .env файл: {dotenv_path if dotenv_path else 'Не знайдено'}")
    if dotenv_path:
        print(f"Чи існує .env файл: {dotenv_path.exists()}")
    print("--- Завантажені налаштування програми ---")
    # Виводимо значення, приховуючи чутливі дані
    for key, value in settings.model_dump().items():
        if "password" in key.lower() or "secret" in key.lower() or "key" in key.lower():
            print(f"{key}: ******")
        else:
            print(f"{key}: {value}")
    print(f"Повний шлях до директорії завантажених файлів: {settings.UPLOADED_FILES_DIR.resolve()}")
    print(f"Повний шлях до директорії логів: {settings.LOG_DIR.resolve()}")
