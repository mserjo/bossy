# backend/app/src/config/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету конфігурації (`config`).

Цей файл робить доступними основні об'єкти конфігурації та функції
для імпорту з пакету `backend.app.src.config`.

Він експортує головний об'єкт налаштувань `settings`,
а також функції для отримання залежностей (наприклад, сесії БД, клієнта Redis),
та ініціалізації / закриття з'єднань з зовнішніми сервісами.
"""

# Імпорт головного об'єкта налаштувань
from backend.app.src.config.settings import settings

# Імпорт функцій для роботи з базою даних
from backend.app.src.config.database import (
    async_engine,         # Асинхронний SQLAlchemy engine
    AsyncSessionLocal,    # Фабрика асинхронних сесій
    get_async_session,       # Залежність FastAPI для отримання сесії БД (перейменовано з get_db_session)
    connect_to_db,        # Функція для ініціалізації підключення до БД
    close_db_connection,  # Функція для закриття підключення до БД
    check_db_connection,  # Функція для перевірки з'єднання (якщо потрібна)
)

# Імпорт логгера (Loguru logger вже глобально налаштований в logging.py)
from backend.app.src.config.logging import logger

# Імпорт функцій для роботи з Redis (якщо використовується)
from backend.app.src.config.redis import (
    init_redis_pool,      # Функція для ініціалізації пулу/клієнта Redis
    close_redis_pool,     # Функція для закриття пулу/клієнта Redis
    get_redis_client,     # Залежність FastAPI для отримання клієнта Redis
)

# Імпорт екземпляра Celery app (якщо використовується)
from backend.app.src.config.celery import celery_app

# Імпорт функцій для роботи з Firebase (якщо використовується)
from backend.app.src.config.firebase import (
    initialize_firebase_app, # Функція для ініціалізації Firebase Admin SDK
    get_firebase_app,        # Функція для отримання екземпляра Firebase App
    # send_fcm_message,      # Приклад функції (краще в сервісах)
)

# Імпорт функцій для роботи з Elasticsearch (якщо використовується)
from backend.app.src.config.elasticsearch import (
    get_elasticsearch_client,     # Функція для отримання/ініціалізації клієнта ES
    close_elasticsearch_client,   # Функція для закриття клієнта ES
    get_es_client_dependency,     # Залежність FastAPI для отримання клієнта ES
)

# Імпорт налаштувань безпеки та утиліт (якщо вони потрібні для експорту звідси)
from backend.app.src.config.security import (
    pwd_context,              # Passlib CryptContext для хешування паролів
    verify_password,          # Функція для перевірки пароля
    get_password_hash,        # Функція для генерації хешу пароля
    # Константи JWT (SECRET_KEY, ALGORITHM тощо) доступні через `settings.app`
)


# Визначення змінної `__all__` для контролю публічного API пакету `config`.
__all__ = [
    "settings", # Головний об'єкт налаштувань

    # Database
    "async_engine",
    "AsyncSessionLocal",
    "get_async_session", # Перейменовано з get_db_session
    "connect_to_db",
    "close_db_connection",
    "check_db_connection",

    # Logging
    "logger",

    # Redis
    "init_redis_pool",
    "close_redis_pool",
    "get_redis_client",

    # Celery
    "celery_app",

    # Firebase
    "initialize_firebase_app",
    "get_firebase_app",

    # Elasticsearch
    "get_elasticsearch_client",
    "close_elasticsearch_client",
    "get_es_client_dependency",

    # Security
    "pwd_context",
    "verify_password",
    "get_password_hash",
]

# TODO: Переконатися, що всі необхідні об'єкти та функції експортуються.
# На даний момент включені основні елементи для роботи з конфігурацією,
# базою даних, логуванням та іншими потенційними сервісами.
#
# Цей файл слугує єдиною точкою входу для доступу до конфігураційних
# компонентів з інших частин додатку, що спрощує імпорти та управління залежностями.
# Наприклад, замість `from backend.app.src.config.settings import settings`,
# можна буде використовувати `from backend.app.src.config import settings`.
#
# Все виглядає добре.
# `celery_app` може бути `None`, якщо Celery не налаштований.
# Аналогічно для Redis, Firebase, Elasticsearch - відповідні функції/клієнти
# можуть повертати `None` або обробляти відсутність конфігурації.
# Це дозволяє гнучко вмикати/вимикати модулі.
#
# `pwd_context` та функції для паролів експортуються для використання в сервісах автентифікації.
#
# Все готово.
