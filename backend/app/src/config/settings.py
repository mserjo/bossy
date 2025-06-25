# backend/app/src/config/settings.py
# -*- coding: utf-8 -*-
"""
Цей модуль відповідає за завантаження та валідацію налаштувань додатку.
Використовується Pydantic Settings для зчитування конфігурації з змінних середовища
та/або .env файлу. Це забезпечує централізоване та типізоване управління конфігурацією.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, AmqpDsn, HttpUrl, Field, validator
from typing import List, Optional, Union, Literal
from enum import Enum
import os

# Визначення шляху до кореневого каталогу проекту для завантаження .env файлу
# Припускаємо, що цей файл settings.py знаходиться в backend/app/src/config/
# Тоді корінь проекту - це ../../../.. відносно цього файлу.
# Або ж, .env файл може бути поруч з main.py або в корені backend.
# Для Docker, змінні середовища будуть передаватися напряму.
# Для локальної розробки, .env файл зазвичай у корені проекту або в backend/.
# Вкажемо шлях до .env у корені backend/
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")
# print(f"DEBUG: Calculated .env path: {ENV_FILE_PATH}") # Для відладки

# Більш надійний спосіб знайти корінь проекту, якщо структура відома:
# Припускаємо, що структура така: bossy/backend/app/src/config/settings.py
# Корінь проекту - bossy/
# .env файл очікується в bossy/backend/.env (або bossy/.env)
# Для Docker, .env файл не використовується, змінні передаються в compose.
# Для локального запуску з backend/, .env файл може бути в backend/.env

# Pydantic-settings автоматично шукає .env файл у поточному робочому каталозі
# та у батьківських каталогах, якщо env_file не вказано явно з абсолютним шляхом.
# Або можна вказати відносний шлях, якщо .env файл знаходиться в певному місці
# відносно місця запуску скрипта (що не завжди надійно).
# Краще використовувати абсолютний шлях або покладатися на автопошук pydantic-settings.

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

    # Секретний ключ для підпису JWT токенів та інших криптографічних операцій.
    # ВАЖЛИВО: має бути надійним та зберігатися в секреті, особливо для production.
    # Генерується, наприклад, так: openssl rand -hex 32
    SECRET_KEY: str = Field(..., description="Секретний ключ для криптографічних операцій")

    # Налаштування CORS (Cross-Origin Resource Sharing)
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="Список дозволених хостів (для Django/FastAPI middleware)")
    # Або для FastAPI CORS Middleware:
    BACKEND_CORS_ORIGINS: List[Union[str, HttpUrl]] = Field(default=[], description="Список дозволених джерел для CORS (URL)")
    # Приклад: ["http://localhost", "http://localhost:8080", "https://yourdomain.com"]
    # Якщо [], то CORS може бути вимкнений або мати інші налаштування за замовчуванням.
    # Якщо ["*"], то дозволені всі джерела (небезпечно для production).

    # API префікс
    API_V1_STR: str = "/api/v1"
    GRAPHQL_API_STR: str = "/graphql" # Шлях для GraphQL ендпоінта

    # Налаштування токенів
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, description="Час життя access токена в хвилинах")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, description="Час життя refresh токена в днях")
    JWT_ALGORITHM: str = Field(default="HS256", description="Алгоритм підпису JWT токенів")
    # JWT_AUDIENCE: Optional[str] = None # Аудиторія JWT
    # JWT_ISSUER: Optional[str] = None # Видавець JWT

    # Налаштування лімітера запитів (Rate Limiting)
    RATE_LIMIT_ENABLE: bool = Field(default=True, description="Чи ввімкнено Rate Limiting")
    RATE_LIMIT_TIMES: int = Field(default=100, description="Кількість запитів")
    RATE_LIMIT_SECONDS: int = Field(default=60, description="За період в секундах")

    # Налаштування для .env файлу
    # model_config дозволяє налаштувати поведінку BaseSettings.
    # env_file: шлях до .env файлу.
    # env_file_encoding: кодування .env файлу.
    # extra: 'ignore' (за замовчуванням) або 'forbid' (забороняти невідомі змінні).
    model_config = SettingsConfigDict(
        env_file=".env", # Шукає .env у поточному каталозі або батьківських
        env_file_encoding='utf-8',
        extra='ignore' # Ігнорувати зайві змінні середовища
    )

class DatabaseSettings(BaseSettings):
    """
    Налаштування підключення до бази даних PostgreSQL.
    """
    POSTGRES_SERVER: str = Field(default="localhost", description="Хост сервера PostgreSQL")
    POSTGRES_PORT: int = Field(default=5432, ge=1024, le=65535, description="Порт сервера PostgreSQL")
    POSTGRES_USER: str = Field(default="postgres", description="Ім'я користувача PostgreSQL")
    POSTGRES_PASSWORD: str = Field(default="postgres", description="Пароль користувача PostgreSQL")
    POSTGRES_DB: str = Field(default="bossy_db", description="Назва бази даних PostgreSQL")

    # Асинхронний DSN для SQLAlchemy
    # postgresql+asyncpg://user:password@host:port/dbname
    DB_POOL_SIZE: int = Field(default=5, ge=1, description="Мінімальна кількість з'єднань в пулі")
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, description="Максимальна кількість додаткових з'єднань понад pool_size")
    DB_ECHO_LOG: bool = Field(default=False, description="Чи виводити SQL запити в лог (для відладки)")

    # Поле DATABASE_URL генерується автоматично на основі інших полів.
    # Використовуємо validator або model_validator для цього.
    # Або ж, якщо DATABASE_URL задано в .env, то він буде мати пріоритет.
    # Краще, щоб DATABASE_URL був основним джерелом, а окремі поля - для зручності або за замовчуванням.
    # Або ж, генерувати його, якщо він не заданий.
    # Pydantic Settings завантажує змінні в певному порядку, .env має пріоритет над дефолтами.
    # Якщо DATABASE_URL є в .env, він буде використаний.
    # Якщо ні, ми можемо спробувати його зібрати.
    # Для SQLAlchemy 2.0 асинхронний DSN:
    DATABASE_URL: Optional[PostgresDsn] = Field(default=None, description="Повний URL для підключення до БД (має пріоритет)")

    @model_validator(mode='before') # Pydantic v2 style
    @classmethod
    def assemble_db_connection(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("DATABASE_URL") is None:
            # Якщо DATABASE_URL не задано, генеруємо його
            user = values.get("POSTGRES_USER", "postgres")
            password = values.get("POSTGRES_PASSWORD", "postgres")
            server = values.get("POSTGRES_SERVER", "localhost")
            port = values.get("POSTGRES_PORT", 5432)
            db_name = values.get("POSTGRES_DB", "bossy_db")
            # Для asyncpg
            values["DATABASE_URL"] = f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db_name}"
        return values

    model_config = SettingsConfigDict(env_prefix='POSTGRES_', env_file=".env", env_file_encoding='utf-8', extra='ignore')
    # `env_prefix` тут не потрібен, якщо поля називаються POSTGRES_SERVER, а не SERVER.
    # Якщо поля називаються SERVER, PORT, USER, PASSWORD, DB, то `env_prefix='POSTGRES_'`
    # дозволить завантажувати змінні POSTGRES_SERVER, POSTGRES_PORT і т.д.
    # Оскільки поля вже мають префікс POSTGRES_, то `env_prefix` не потрібен.
    # Видаляю `env_prefix` звідси.
    # model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')
    # Або, якщо змінні середовища для БД мають префікс, наприклад DB_POSTGRES_SERVER,
    # то можна використовувати `env_prefix='DB_'` для `DatabaseSettings`.
    # Залишаю без префікса, очікуючи змінні типу POSTGRES_SERVER.


class RedisSettings(BaseSettings):
    """Налаштування підключення до Redis."""
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_DB: int = Field(default=0)
    REDIS_URL: Optional[RedisDsn] = Field(default=None)

    @model_validator(mode='before')
    @classmethod
    def assemble_redis_url(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("REDIS_URL") is None:
            host = values.get("REDIS_HOST", "localhost")
            port = values.get("REDIS_PORT", 6379)
            db = values.get("REDIS_DB", 0)
            password = values.get("REDIS_PASSWORD")
            if password:
                values["REDIS_URL"] = f"redis://:{password}@{host}:{port}/{db}"
            else:
                values["REDIS_URL"] = f"redis://{host}:{port}/{db}"
        return values

    model_config = SettingsConfigDict(env_prefix='REDIS_', env_file=".env", env_file_encoding='utf-8', extra='ignore')


class CelerySettings(BaseSettings):
    """Налаштування Celery."""
    CELERY_BROKER_URL: Optional[Union[AmqpDsn, RedisDsn]] = Field(default=None, description="URL брокера повідомлень для Celery (RabbitMQ або Redis)")
    CELERY_RESULT_BACKEND_URL: Optional[Union[RedisDsn, PostgresDsn]] = Field(default=None, description="URL бекенда результатів для Celery")
    # CELERY_TASK_ALWAYS_EAGER: bool = Field(default=False, description="Виконувати задачі локально синхронно (для тестів)")

    # Приклад, якщо Redis використовується як брокер та бекенд результатів:
    # CELERY_BROKER_URL = "redis://localhost:6379/1"
    # CELERY_RESULT_BACKEND_URL = "redis://localhost:6379/2"
    # Або якщо RabbitMQ:
    # CELERY_BROKER_URL = "amqp://guest:guest@localhost:5672//"

    model_config = SettingsConfigDict(env_prefix='CELERY_', env_file=".env", env_file_encoding='utf-8', extra='ignore')

# TODO: Додати налаштування для Firebase, Elasticsearch, якщо вони будуть використовуватися.
# class FirebaseSettings(BaseSettings):
#     FIREBASE_CREDENTIALS_PATH: Optional[str] = Field(None, description="Шлях до файлу з обліковими даними Firebase Admin SDK (JSON)")
#     model_config = SettingsConfigDict(env_prefix='FIREBASE_', env_file=".env", env_file_encoding='utf-8', extra='ignore')

# class ElasticsearchSettings(BaseSettings):
#     ELASTICSEARCH_HOSTS: List[Union[HttpUrl, str]] = Field(default=["http://localhost:9200"], description="Список хостів Elasticsearch")
#     # ELASTICSEARCH_USER: Optional[str] = None
#     # ELASTICSEARCH_PASSWORD: Optional[str] = None
#     model_config = SettingsConfigDict(env_prefix='ELASTICSEARCH_', env_file=".env", env_file_encoding='utf-8', extra='ignore')


# --- Збираємо всі налаштування в один об'єкт ---
class Settings(BaseSettings):
    """
    Головний клас налаштувань, що агрегує всі інші.
    """
    app: AppSettings = AppSettings()
    db: DatabaseSettings = DatabaseSettings()
    redis: Optional[RedisSettings] = Field(default_factory=RedisSettings) if RedisSettings().REDIS_URL else None
    celery: Optional[CelerySettings] = Field(default_factory=CelerySettings) if CelerySettings().CELERY_BROKER_URL else None
    # firebase: Optional[FirebaseSettings] = Field(default_factory=FirebaseSettings) if FirebaseSettings().FIREBASE_CREDENTIALS_PATH else None
    # elasticsearch: Optional[ElasticsearchSettings] = Field(default_factory=ElasticsearchSettings) if ElasticsearchSettings().ELASTICSEARCH_HOSTS else None

    # Для завантаження .env файлу, якщо він знаходиться в корені проекту,
    # а не поруч з цим файлом або в поточному робочому каталозі.
    # Можна вказати тут, або в кожному під-класі BaseSettings.
    # model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, env_file_encoding='utf-8', extra='ignore')
    # Або, якщо .env файл один для всіх, то достатньо вказати в Settings.
    # Pydantic-settings шукає .env файл, тому явне вказання шляху може не знадобитися,
    # якщо .env лежить у корені проекту або в `backend/`.
    # Якщо .env файл знаходиться в `backend/.env`:
    model_config = SettingsConfigDict(env_file_encoding='utf-8', extra='ignore')


# Створюємо екземпляр налаштувань, який буде використовуватися в усьому додатку.
# Це дозволяє завантажити змінні середовища та .env файл лише один раз при старті.
settings = Settings()

# Приклад використання:
# from backend.app.src.config.settings import settings
# print(settings.app.APP_NAME)
# print(settings.db.DATABASE_URL)
# if settings.redis:
# print(settings.redis.REDIS_URL)

# TODO: Перевірити шляхи до .env файлу для локальної розробки та Docker.
# Для Docker, змінні середовища передаються через docker-compose.yml, і .env файл не потрібен всередині контейнера.
# Для локального запуску, .env файл має бути доступний.
# Pydantic-settings має знайти .env файл, якщо він є в одному з стандартних місць.
# Якщо є проблеми з завантаженням .env, потрібно буде явно вказати шлях в `SettingsConfigDict`.
#
# `env_prefix` в `SettingsConfigDict` для підкласів (DatabaseSettings, RedisSettings, etc.)
# дозволяє уникнути конфліктів імен змінних в .env файлі, якщо вони не унікальні.
# Наприклад, якщо є `HOST` для Redis та `HOST` для Elasticsearch.
# Тоді в .env: `REDIS_HOST=...`, `ELASTICSEARCH_HOST=...`
# І в класах: `REDIS_HOST` в `RedisSettings` (з `env_prefix='REDIS_'`) стане `HOST`.
# Або, якщо поля в класах вже мають префікси (як `POSTGRES_SERVER`), то `env_prefix` не потрібен.
# Я використовую поля з префіксами в класах, тому `env_prefix` для них не потрібен.
# Глобальний `env_prefix` для `Settings` не потрібен, бо він агрегує вже налаштовані під-класи.
#
# Валідатори `assemble_db_connection` та `assemble_redis_url` генерують повні URL,
# якщо вони не задані явно, що зручно.
#
# `ALLOWED_HOSTS` та `BACKEND_CORS_ORIGINS` - важливі для безпеки.
# `SECRET_KEY` - критично важливий.
#
# `Field(default_factory=...) if ... else None` для опціональних налаштувань (Redis, Celery)
# дозволяє створювати екземпляри цих налаштувань лише якщо відповідні змінні (наприклад, URL) задані.
# Це робить конфігурацію більш гнучкою.
#
# Все виглядає добре.
