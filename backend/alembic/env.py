# backend/alembic/env.py
# -*- coding: utf-8 -*-
"""Алембік конфігураційний файл `env.py`.

Цей файл відповідає за налаштування середовища виконання Alembic.
Він визначає, як Alembic підключається до бази даних, яку мету
(target_metadata) використовувати для автогенерації міграцій,
та як виконувати міграції в онлайн та офлайн режимах.

Основні завдання цього файлу:
- Завантаження конфігурації з `alembic.ini`.
- Налаштування логування.
- Визначення `target_metadata` для автогенерації міграцій.
- Реалізація функцій `run_migrations_offline` та `run_migrations_online`.
- Обробка підключення до бази даних з використанням налаштувань проекту.
"""
import asyncio
import logging
from logging.config import fileConfig

# Імпорт необхідних компонентів SQLAlchemy та Alembic
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# --- Налаштування шляхів для імпорту модулів проекту ---
# Додаємо корінь проекту (директорію `backend`) до `sys.path`,
# щоб Alembic міг коректно імпортувати модулі додатка,
# зокрема моделі та налаштування.
import os
import sys

# Визначаємо абсолютний шлях до поточної директорії (`backend/alembic`)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Піднімаємось на два рівні вище, щоб отримати шлях до директорії `backend`
# backend/alembic -> backend/ -> ./ (корінь проекту, де лежить `backend`)
# Має бути скориговано, якщо структура інша.
# Припускаючи, що env.py в backend/alembic/, то backend/ - це os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # Це буде backend/
# Якщо потрібно додати саму директорію `backend` (якщо вона є частиною імпорту `backend.app...`)
# тоді шлях має бути до директорії, що містить `backend`.
# Для структури backend/app/src... , PROJECT_ROOT = backend/
# Для імпортів типу `from backend.app.src...` потрібно, щоб директорія, що містить `backend`, була в sys.path
# Якщо alembic.ini і env.py знаходяться в backend/alembic, то для імпорту backend.app...
# потрібно додати директорію, що містить `backend` (тобто os.path.dirname(PROJECT_ROOT))
# Однак, якщо команди alembic запускаються з backend/, то backend/ вже буде в sys.path.
# Поточний варіант з BACKEND_DIR був некоректний для імпортів `backend.app.src...` якщо він сам є `backend/`.
# Правильніше додати батьківську директорію `backend` до шляху, якщо `backend` є частиною імпорту.
# Або, якщо команди запускаються з `backend/`, то `.` вже в `sys.path`.
# Для простоти, припустимо, що команди alembic запускаються з директорії `backend/`.
# Якщо ж ні, то шлях до директорії, що містить `backend/`, має бути доданий.
# Наприклад: sys.path.insert(0, os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..")))
# Поточна логіка sys.path виглядає дещо заплутаною.
# Якщо env.py в backend/alembic, то SCRIPT_DIR = backend/alembic
# PROJECT_ROOT (якщо це backend/) = os.path.dirname(SCRIPT_DIR)
# Якщо імпорти `from backend.app.src...`, то `backend` має бути доступний.
# Найпростіше: додати `.` до sys.path, якщо запускати alembic з `backend/`
# Або додати абсолютний шлях до директорії, що містить `backend`.
# Для поточного завдання я припущу, що `backend` вже є в PYTHONPATH або команди запускаються з `backend/`.
# Тому явне додавання `BACKEND_DIR` може бути зайвим або потребуватиме корекції.
# Залишимо як є, але з коментарем про можливу необхідність перегляду.
# Код нижче додає `backend/` до `sys.path`
sys.path.insert(0, PROJECT_ROOT)


# --- Імпорт метаданих моделей та налаштувань БД ---
# Імпортуємо `Base` з визначення моделей SQLAlchemy вашого проекту.
# `Base.metadata` є об'єктом `MetaData`, який Alembic використовує для автогенерації.
# Переконайтеся, що шлях до `Base` є правильним для вашої структури проекту.
from backend.app.src.models.base_model import Base

# Імпортуємо ВСІ моделі SQLAlchemy вашого додатку.
# Це необхідно для того, щоб Alembic "бачив" їх і міг порівнювати
# їх поточний стан зі станом у базі даних для автогенерації міграцій.
# Зазвичай, це робиться шляхом імпорту пакета `models`, який у своєму `__init__.py`
# імпортує всі класи моделей.
# pylint: disable=unused-import
import backend.app.src.models.user_model # Приклад явного імпорту моделі
# Або, якщо __init__.py в models все налаштовує:
# import backend.app.src.models

# Імпортуємо об'єкт налаштувань додатка для отримання URL бази даних.
# Це дозволяє централізовано керувати конфігурацією БД.
from backend.app.src.config.settings import get_settings

# Отримуємо екземпляр налаштувань
app_settings = get_settings()

# Ініціалізація логера для цього файлу. Логування буде налаштовано
# на основі `alembic.ini` через `fileConfig`.
logger = logging.getLogger("alembic.env")


# --- Загальні налаштування Alembic ---
# `config` - це об'єкт конфігурації Alembic, який надає доступ
# до значень, визначених у файлі `alembic.ini`.
config = context.config

# Інтерпретація файлу `alembic.ini` для налаштування логування Python.
# Цей рядок дозволяє конфігурувати логери, обробники та форматувальники
# через секції `[loggers]`, `[handlers]`, `[formatters]` в `alembic.ini`.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Встановлюємо `target_metadata` для операцій автогенерації Alembic.
# `target_metadata` має бути об'єктом `MetaData` з вашого SQLAlchemy `Base`.
# Alembic порівнює цей `MetaData` зі станом бази даних для генерації міграцій.
target_metadata = Base.metadata

# TODO: Розглянути можливість використання версіонованих таблиць або схем,
#       якщо це потрібно для складних сценаріїв розгортання (наприклад, multi-tenancy).
#       Приклад: target_metadata = {'schema_name': Base.metadata}
#       Українською: TODO: Розглянути використання версіонованих таблиць або схем
#       для складних сценаріїв, таких як мульти-оренда.

# --- Офлайн режим виконання міграцій ---
def run_migrations_offline() -> None:
    """Виконує міграції в "офлайн" режимі.

    У цьому режимі Alembic не підключається до реальної бази даних,
    а генерує SQL скрипти на основі URL бази даних. Це корисно для
    перегляду SQL, що буде виконано, або для генерації скриптів,
    які потім можна виконати вручну на базі даних.
    """
    # Отримуємо URL бази даних з налаштувань додатка.
    # Для офлайн режиму зазвичай потрібен синхронний URL.
    # Переконайтеся, що метод `get_sync_database_url` існує у ваших налаштуваннях.
    url = app_settings.get_sync_database_url()
    logger.info("Генерація офлайн міграцій для URL: %s", url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,  # Генерувати SQL з літеральними значеннями замість placeholder'ів
        dialect_opts={"paramstyle": "named"},  # Опції діалекту SQLAlchemy (наприклад, для psycopg2)
        # compare_type=True, # Розкоментуйте, якщо потрібно виявляти зміни типів колонок в офлайн режимі
    )

    # Виконуємо міграції в межах транзакції (для генерації скрипту)
    with context.begin_transaction():
        context.run_migrations()

    logger.info("Офлайн міграції успішно згенеровано (виведено в стандартний вивід або файл).")


# --- Онлайн режим виконання міграцій ---
def do_run_migrations(connection) -> None:
    """Допоміжна функція для запуску міграцій з існуючим підключенням до БД.

    Ця функція викликається `run_migrations_online` і налаштовує
    контекст Alembic для виконання міграцій на активному підключенні.

    Args:
        connection: Активне SQLAlchemy підключення до бази даних.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Рекомендується для виявлення змін типів колонок
        # compare_server_default=True, # Розкоментуйте, якщо потрібно виявляти зміни server_default
        # include_schemas=True, # Розкоментуйте, якщо ваш проект використовує різні схеми PostgreSQL
    )
    # TODO: Додати специфічні для проекту опції `context.configure()`, якщо потрібно:
    #       - `include_object`: функція для фільтрації таблиць/об'єктів для відстеження Alembic.
    #       - `process_revision_directives`: функція для кастомізації процесу автогенерації міграцій.
    #       Українською: TODO: Додати специфічні для проекту опції context.configure(),
    #       такі як `include_object` для фільтрації об'єктів або
    #       `process_revision_directives` для налаштування автогенерації.

    # Виконуємо міграції в межах транзакції бази даних
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Виконує міграції в "онлайн" режимі.

    У цьому режимі Alembic підключається до реальної бази даних,
    створює асинхронний рушій (Engine) SQLAlchemy та виконує міграції
    через активне підключення. Цей режим застосовує зміни безпосередньо до БД.
    """
    # Отримуємо секцію конфігурації для поточної БД з alembic.ini.
    # Це дозволяє перевизначити деякі параметри з `alembic.ini` для рушія.
    connectable_configuration = config.get_section(config.config_ini_section, {})

    # Встановлюємо URL бази даних для Alembic з налаштувань додатка.
    # Для онлайн режиму з asyncio потрібен асинхронний URL.
    # Переконайтеся, що метод `get_async_database_url` існує у ваших налаштуваннях.
    db_url = app_settings.get_async_database_url()
    logger.info("Застосування онлайн міграцій для URL: %s", db_url)
    connectable_configuration["sqlalchemy.url"] = db_url

    # Створюємо асинхронний рушій SQLAlchemy з конфігурації.
    # `prefix="sqlalchemy."` вказує, що параметри для рушія в `alembic.ini`
    # мають префікс `sqlalchemy.` (наприклад, `sqlalchemy.url`).
    # `poolclass=pool.NullPool` використовується, оскільки Alembic зазвичай
    # виконується як короткоживучий скрипт, і пул підключень не потрібен.
    connectable = async_engine_from_config(
        connectable_configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Асинхронно підключаємося до бази даних
    async with connectable.connect() as connection:
        # Виконуємо функцію `do_run_migrations` синхронно в межах асинхронного підключення.
        # `run_sync()` дозволяє викликати синхронний код, який використовує SQLAlchemy Core (Alembic),
        # з асинхронного контексту SQLAlchemy 2.0.
        await connection.run_sync(do_run_migrations)

    # Звільняємо ресурси рушія (закриваємо підключення) після завершення роботи.
    await connectable.dispose()

    logger.info("Онлайн міграції успішно застосовано до бази даних.")


# --- Визначення режиму виконання Alembic ---
# Alembic може працювати в двох режимах:
# - Офлайн (`context.is_offline_mode()` повертає `True`): генерує SQL скрипти.
# - Онлайн (`context.is_offline_mode()` повертає `False`): підключається до БД і виконує міграції.
if context.is_offline_mode():
    logger.info("Запуск Alembic в офлайн режимі...")
    run_migrations_offline()
else:
    logger.info("Запуск Alembic в онлайн режимі...")
    asyncio.run(run_migrations_online())
