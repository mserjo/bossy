# backend/app/src/config/settings.py
# -*- coding: utf-8 -*-
"""
Цей модуль відповідає за завантаження та валідацію налаштувань додатку.
Використовується Pydantic Settings для зчитування конфігурації з змінних середовища
та/або .env файлу. Це забезпечує централізоване та типізоване управління конфігурацією.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, AmqpDsn, HttpUrl, Field, model_validator, EmailStr # Додано EmailStr
from typing import List, Optional, Union, Literal, Dict, Any
from enum import Enum
import os
from pathlib import Path # Додано Path

class EnvironmentEnum(str, Enum):
    """Перелік можливих середовищ виконання додатку."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class AppSettings(BaseSettings):
    """
    Клас для зберігання основних налаштувань додатку.
    """
    APP_NAME: str = "Bossy"
    APP_VERSION: str = "0.1.0"
    DESCRIPTION: Optional[str] = "Бонусна система в межах групи (нагороди/бонуси/штрафи)."
    DEBUG: bool = Field(default=False, description="Режим відладки. НЕ ВИКОРИСТОВУВАТИ В PRODUCTION!")
    ENVIRONMENT: EnvironmentEnum = Field(default=EnvironmentEnum.DEVELOPMENT, description="Середовище виконання (development, staging, production, testing)")
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent, description="Базовий каталог проекту (backend).") # backend/app

    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="Список дозволених хостів (для Django/FastAPI middleware)")
    BACKEND_CORS_ORIGINS: List[Union[str, HttpUrl]] = Field(default=[], description="Список дозволених джерел для CORS (URL)")

    API_V1_STR: str = "/api/v1"
    GRAPHQL_API_STR: str = "/graphql"

    RATE_LIMIT_ENABLE: bool = Field(default=True, description="Чи ввімкнено Rate Limiting")
    RATE_LIMIT_TIMES: int = Field(default=100, ge=1, description="Кількість запитів")
    RATE_LIMIT_SECONDS: int = Field(default=60, ge=1, description="За період в секундах")

    # Налаштування використання опціональних сервісів
    USE_REDIS: bool = Field(default=True, description="Чи використовувати Redis для кешування та/або черг.")
    USE_CELERY: bool = Field(default=True, description="Чи використовувати Celery для фонових завдань.")
    USE_ELASTICSEARCH: bool = Field(default=True, description="Чи використовувати Elasticsearch для пошуку.")
    USE_FIREBASE: bool = Field(default=True, description="Чи використовувати Firebase (наприклад, для FCM).")

    FRONTEND_URL: HttpUrl = Field(default="http://localhost:3000", description="Базовий URL фронтенд додатку")

    SECRET_KEY: str = Field(default="your-default-secret-key-for-development", description="Секретний ключ додатку. ПОВИНЕН БУТИ ЗМІНЕНИЙ В PRODUCTION!")

    # Налаштування для .env файлу. Pydantic-settings шукає .env у поточному каталозі або батьківських.
    # Якщо .env файл знаходиться, наприклад, в корені проекту `bossy/.env`,
    # а додаток запускається з `bossy/backend/`, то шлях має бути `../.env`.
    # Або можна покласти .env в `backend/.env`.
    # Для простоти, якщо .env в `backend/`, то `env_file=".env"` спрацює при запуску з `backend/`.
    # Якщо запускати з `bossy/`, то `env_file="backend/.env"`.
    # `SettingsConfigDict` в Pydantic v2 автоматично шукає `.env`.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

class AuthSettings(BaseSettings):
    """Налаштування автентифікації та авторизації."""
    SECRET_KEY: str = Field(..., description="Секретний ключ для криптографічних операцій (JWT, хешування паролів тощо)")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, description="Час життя access токена в хвилинах")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, description="Час життя refresh токена в днях")
    JWT_ALGORITHM: str = Field(default="HS256", description="Алгоритм підпису JWT токенів")

    SUPERUSER_EMAIL: EmailStr = Field(default="odin@example.com", description="Email супер-адміністратора")
    SUPERUSER_PASSWORD: str = Field(..., description="Пароль супер-адміністратора (встановлюється через змінну середовища)")

    # Налаштування для хешування паролів (якщо використовуються passlib contexts)
    # PASSWORD_HASH_SCHEMES: List[str] = Field(default_factory=lambda: ["bcrypt"], description="Схеми хешування паролів")
    # BCRYPT_ROUNDS: int = Field(default=12, description="Кількість раундів для bcrypt")

    model_config = SettingsConfigDict(env_prefix='AUTH_', env_file=".env", env_file_encoding='utf-8', extra='ignore')


class LoggingSettings(BaseSettings):
    """Налаштування логування."""
    LOG_LEVEL: str = Field(default="INFO", description="Рівень логування (DEBUG, INFO, WARNING, ERROR, CRITICAL)")

    LOG_TO_FILE_ENABLE: bool = Field(default=False, description="Чи ввімкнено логування у файл")
    LOG_FILE_PATH: str = Field(default="logs/app.log", description="Шлях до файлу логів (відносно BASE_DIR або абсолютний)") # Змінено коментар
    LOG_FILE_LEVEL: str = Field(default="INFO", description="Рівень логування для файлу")
    LOG_FILE_ROTATION: str = Field(default="10 MB", description="Ротація файлу (розмір, час, наприклад, '1 week', '00:00')")
    LOG_FILE_RETENTION: str = Field(default="7 days", description="Час зберігання файлів логів ('1 month', '10 files')")
    LOG_FILE_COMPRESSION: Optional[str] = Field(default="zip", description="Формат стиснення старих файлів логів (наприклад, 'zip', 'gz')")

    model_config = SettingsConfigDict(env_prefix='LOG_', env_file=".env", env_file_encoding='utf-8', extra='ignore')


class DatabaseSettings(BaseSettings):
    """Налаштування підключення до бази даних PostgreSQL."""
    POSTGRES_SERVER: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432, ge=1024, le=65535)
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_DB: str = Field(default="bossy_db")

    DATABASE_URL: Optional[PostgresDsn] = Field(default=None) # Має пріоритет, якщо задано

    DB_POOL_SIZE: int = Field(default=5, ge=1)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0)
    DB_ECHO_LOG: bool = Field(default=False)

    @model_validator(mode='before')
    @classmethod
    def assemble_db_connection(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("DATABASE_URL") is None:
            user, password = values.get("POSTGRES_USER"), values.get("POSTGRES_PASSWORD")
            server, port, db_name = values.get("POSTGRES_SERVER"), values.get("POSTGRES_PORT"), values.get("POSTGRES_DB")
            if all([user, password, server, port, db_name]): # Перевірка, чи всі компоненти є
                 values["DATABASE_URL"] = f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db_name}"
            # Якщо якісь компоненти відсутні, DATABASE_URL залишиться None, і це викличе помилку пізніше, якщо БД потрібна.
        return values

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')


class RedisSettings(BaseSettings):
    """Налаштування підключення до Redis."""
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_DB: int = Field(default=0, ge=0)
    REDIS_URL: Optional[RedisDsn] = Field(default=None) # Має пріоритет

    @model_validator(mode='before')
    @classmethod
    def assemble_redis_url(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("REDIS_URL") is None:
            host, port, db = values.get("REDIS_HOST"), values.get("REDIS_PORT"), values.get("REDIS_DB")
            password = values.get("REDIS_PASSWORD")
            if all([host, port is not None, db is not None]): # port та db можуть бути 0
                if password:
                    values["REDIS_URL"] = f"redis://:{password}@{host}:{port}/{db}"
                else:
                    values["REDIS_URL"] = f"redis://{host}:{port}/{db}"
        return values

    model_config = SettingsConfigDict(env_prefix='REDIS_', env_file=".env", env_file_encoding='utf-8', extra='ignore')


class CelerySettings(BaseSettings):
    """Налаштування Celery."""
    CELERY_BROKER_URL: Optional[Union[AmqpDsn, RedisDsn, str]] = Field(default=None) # Додано str для гнучкості
    CELERY_RESULT_BACKEND_URL: Optional[Union[RedisDsn, PostgresDsn, str]] = Field(default=None)
    CELERY_TASK_ALWAYS_EAGER: bool = Field(default=False, description="Виконувати задачі локально синхронно (для тестів)")

    model_config = SettingsConfigDict(env_prefix='CELERY_', env_file=".env", env_file_encoding='utf-8', extra='ignore')

class FirebaseSettings(BaseSettings):
    FIREBASE_CREDENTIALS_PATH: Optional[str] = Field(None, description="Шлях до файлу Firebase Admin SDK JSON")
    # Можна додати інші налаштування Firebase, якщо потрібно
    model_config = SettingsConfigDict(env_prefix='FIREBASE_', env_file=".env", env_file_encoding='utf-8', extra='ignore')

class ElasticsearchSettings(BaseSettings):
    ELASTICSEARCH_HOSTS: List[Union[HttpUrl, str]] = Field(default_factory=list, description="Список хостів Elasticsearch (наприклад, ['http://localhost:9200'])")
    ELASTICSEARCH_USER: Optional[str] = Field(default=None)
    ELASTICSEARCH_PASSWORD: Optional[str] = Field(default=None)
    # ... інші налаштування ...
    model_config = SettingsConfigDict(env_prefix='ELASTICSEARCH_', env_file=".env", env_file_encoding='utf-8', extra='ignore')


class EmailSettings(BaseSettings):
    """Налаштування для відправки електронної пошти."""
    MAIL_ENABLED: bool = Field(default=True, description="Чи ввімкнено відправку email.")
    MAIL_USERNAME: Optional[str] = Field(default=None)
    MAIL_PASSWORD: Optional[str] = Field(default=None)
    MAIL_FROM: EmailStr = Field(default="noreply@example.com")
    MAIL_FROM_NAME: Optional[str] = Field(default="Bossy App")
    MAIL_PORT: int = Field(default=587)
    MAIL_SERVER: str = Field(default="smtp.example.com")
    MAIL_STARTTLS: bool = Field(default=True)
    MAIL_SSL_TLS: bool = Field(default=False)
    # Для тестування або локальної розробки
    MAIL_USE_CREDENTIALS: bool = Field(default=True) # Чи використовувати MAIL_USERNAME та MAIL_PASSWORD
    MAIL_VALIDATE_CERTS: bool = Field(default=True) # Чи валідувати SSL сертифікати

    # Шаблони (можна залишити тут або винести в окремий клас)
    # EMAIL_TEMPLATES_DIR: Path = Field(default_factory=lambda: Path(AppSettings().BASE_DIR) / "src" / "templates" / "email")
    # EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = Field(default=48)

    model_config = SettingsConfigDict(env_prefix='MAIL_', env_file=".env", env_file_encoding='utf-8', extra='ignore')


class Settings(BaseSettings):
    """Головний клас налаштувань, що агрегує всі інші."""
    app: AppSettings = AppSettings()
    auth: AuthSettings = AuthSettings() # Додано AuthSettings
    logging: LoggingSettings = LoggingSettings()
    db: DatabaseSettings = DatabaseSettings()

    redis: Optional[RedisSettings] = None
    celery: Optional[CelerySettings] = None
    firebase: Optional[FirebaseSettings] = None
    elasticsearch: Optional[ElasticsearchSettings] = None
    email: Optional[EmailSettings] = None # Додано EmailSettings

    @model_validator(mode='before')
    @classmethod
    def init_optional_settings(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # Отримуємо налаштування AppSettings, щоб перевірити прапори USE_...
        # Якщо 'app' ще не створено (наприклад, при першому виклику валідатора),
        # створюємо тимчасовий екземпляр AppSettings.
        app_settings_data = values.get('app', {})
        if isinstance(app_settings_data, AppSettings):
            app_config = app_settings_data
        else:
            # Спробуємо створити AppSettings з даних, які можуть бути в values['app']
            # або пустим словником, якщо 'app' ще немає.
            # Це дозволить Pydantic завантажити змінні середовища для AppSettings.
            app_config = AppSettings(**app_settings_data)


        if app_config.USE_REDIS:
            _redis_settings = RedisSettings()
            if _redis_settings.REDIS_URL:
                values['redis'] = _redis_settings
                # logger.debug("Redis увімкнено та налаштовано.") # Логер тут ще може бути недоступний
            else:
                values['redis'] = None
                # logger.warning("Redis увімкнено (USE_REDIS=True), але REDIS_URL не вдалося визначити. Redis не буде використовуватися.")
        else:
            values['redis'] = None
            # logger.info("Redis вимкнено (USE_REDIS=False).")

        if app_config.USE_CELERY:
            _celery_settings = CelerySettings()
            if _celery_settings.CELERY_BROKER_URL:
                values['celery'] = _celery_settings
                # logger.debug("Celery увімкнено та налаштовано.")
            else:
                values['celery'] = None
                # logger.warning("Celery увімкнено (USE_CELERY=True), але CELERY_BROKER_URL не визначено. Celery не буде використовуватися.")
        else:
            values['celery'] = None
            # logger.info("Celery вимкнено (USE_CELERY=False).")

        if app_config.USE_FIREBASE:
            _firebase_settings = FirebaseSettings()
            if _firebase_settings.FIREBASE_CREDENTIALS_PATH:
                values['firebase'] = _firebase_settings
                # logger.debug("Firebase увімкнено та налаштовано.")
            else:
                values['firebase'] = None
                # logger.warning("Firebase увімкнено (USE_FIREBASE=True), але FIREBASE_CREDENTIALS_PATH не визначено. Firebase не буде використовуватися.")
        else:
            values['firebase'] = None
            # logger.info("Firebase вимкнено (USE_FIREBASE=False).")

        if app_config.USE_ELASTICSEARCH:
            _elasticsearch_settings = ElasticsearchSettings()
            if _elasticsearch_settings.ELASTICSEARCH_HOSTS:
                values['elasticsearch'] = _elasticsearch_settings
                # logger.debug("Elasticsearch увімкнено та налаштовано.")
            else:
                values['elasticsearch'] = None
                # logger.warning("Elasticsearch увімкнено (USE_ELASTICSEARCH=True), але ELASTICSEARCH_HOSTS не визначено. Elasticsearch не буде використовуватися.")
        else:
            values['elasticsearch'] = None
            # logger.info("Elasticsearch вимкнено (USE_ELASTICSEARCH=False).")

        # Ініціалізація EmailSettings
        # Припускаємо, що email завжди потрібен, якщо MAIL_ENABLED=True, незалежно від AppSettings.USE_EMAIL прапорця (якщо такий буде)
        # Або ж можна додати app_config.USE_EMAIL і перевіряти його.
        # Поки що, якщо MAIL_ENABLED=True в EmailSettings, то ініціалізуємо.
        _email_settings = EmailSettings()
        if _email_settings.MAIL_ENABLED:
            if _email_settings.MAIL_SERVER and _email_settings.MAIL_FROM: # Основні поля для роботи
                values['email'] = _email_settings
                # logger.debug("Email увімкнено та налаштовано.")
            else:
                values['email'] = None
                # logger.warning("Email увімкнено (MAIL_ENABLED=True), але MAIL_SERVER або MAIL_FROM не визначено. Email не буде використовуватися.")
        else:
            values['email'] = None
            # logger.info("Email вимкнено (MAIL_ENABLED=False).")

        return values

    model_config = SettingsConfigDict(
        env_file=".env", # Головний .env файл (може бути той самий, що й для підкласів)
        env_nested_delimiter='__', # Для вкладених змінних типу APP__DEBUG=true
        extra='ignore'
    )

settings = Settings()

# Перевірка після завантаження
if settings.db.DATABASE_URL is None:
    # Це може статися, якщо POSTGRES_USER і т.д. не задані, і DATABASE_URL теж.
    # Логер тут ще може бути не повністю налаштований, тому print.
    print("ПОПЕРЕДЖЕННЯ: DATABASE_URL не вдалося зібрати або завантажити. Перевірте конфігурацію БД.")

if settings.app.ENVIRONMENT == EnvironmentEnum.PRODUCTION and settings.app.DEBUG:
    print("ПОПЕРЕДЖЕННЯ БЕЗПЕКИ: Режим DEBUG увімкнено в PRODUCTION середовищі!")
    # Можна кинути виняток або автоматично вимкнути DEBUG.
    # settings.app.DEBUG = False # Не спрацює, бо settings вже створено.

# Примітки щодо конфігурації:
# - Pydantic-settings шукає .env у поточному каталозі запуску та у батьківських.
#   Поточна конфігурація `env_file=".env"` в кожному підкласі та в головному `Settings`
#   означає, що кожен намагається завантажити свій `.env` (або той самий), і Pydantic об'єднає значення.
# - `env_nested_delimiter='__'` в `Settings.model_config` дозволяє задавати вкладені змінні
#   середовища, наприклад `AUTH__SECRET_KEY=mysecret`.
# - `BASE_DIR` в `AppSettings` визначається як каталог `backend/` (шлях: `settings.py` -> `config/` -> `src/` -> `app/` -> `backend/`).
#   Це коректно для визначення шляхів відносно кореня backend-додатку.
# - `SUPERUSER_PASSWORD` в `AuthSettings` позначено як `...` (обов'язкове без дефолту),
#   що означає, воно *повинно* бути надане через змінну середовища `AUTH_SUPERUSER_PASSWORD`.
#   Це важливо для безпеки.
# - `init_optional_settings` тепер більш явно обробляє випадки, коли опціональні сервіси не налаштовані,
#   базуючись на прапорцях `USE_...` з `AppSettings`.
# - Шлях до лог-файлу в `LoggingSettings` може бути відносним до `BASE_DIR`.
