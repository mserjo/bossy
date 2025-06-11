# backend/alembic/env.py
# -*- coding: utf-8 -*-
"""
Файл конфігурації Alembic `env.py`.

Цей файл відповідає за налаштування середовища виконання Alembic.
Він визначає, як Alembic підключається до бази даних, яку мету
(target_metadata) використовувати для автогенерації міграцій,
та як виконувати міграції в онлайн та офлайн режимах.
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config  # Для асинхронного рушія SQLAlchemy

from alembic import context  # Об'єкт контексту Alembic

# --- Налаштування шляхів ---
# Додаємо корінь додатка до sys.path, щоб Alembic міг знайти модулі додатка.
# Це важливо, якщо env.py або моделі імпортують щось з `backend.app.src`.
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# ALEMBIC_DIR = SCRIPT_DIR (директорія alembic)
# APP_SRC_DIR = os.path.dirname(ALEMBIC_DIR) (директорія src)
# APP_DIR = os.path.dirname(APP_SRC_DIR) (директорія app)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))  # Директорія backend/

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# --- Імпорт метаданих моделей та налаштувань БД ---
# Імпортуємо Base з конфігурації бази даних SQLAlchemy вашого проекту.
# Base.metadata є об'єктом MetaData, який Alembic використовує для автогенерації.
from backend.app.src.models.base_model import Base  # Припускаємо, що Base визначено тут
# from backend.app.src.core.database import Base # Або тут, залежно від структури

# Імпортуємо ВСІ моделі SQLAlchemy вашого додатку.
# Це необхідно для того, щоб Alembic "бачив" їх і міг порівнювати
# їх поточний стан зі станом у базі даних для автогенерації міграцій.
# Переконайтеся, що __init__.py в директорії models (або її підмодулях)
# імпортує всі класи моделей, або імпортуйте їх тут явно.
import backend.app.src.models  # Це завантажить всі моделі, якщо models/__init__.py їх імпортує

# Імпортуємо об'єкт налаштувань додатка для отримання URL бази даних.
from backend.app.src.core.config import settings as app_settings  # Припускаємо, що settings - це об'єкт Pydantic


# Базова функція-заглушка для інтернаціоналізації рядків (якщо потрібна в коментарях)
def _(text: str) -> str:
    return text


# --- Загальні налаштування Alembic ---
# Це об'єкт конфігурації Alembic, який отримує доступ до значень з alembic.ini.
config = context.config

# Інтерпретація файлу конфігурації для логування Python.
# Цей рядок дозволяє налаштувати логування Alembic через alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Встановлюємо `target_metadata` для операцій автогенерації Alembic.
# Це має бути об'єкт `MetaData` з вашого SQLAlchemy Base.
target_metadata = Base.metadata


# TODO: Розглянути можливість використання версіонованих таблиць або схем,
#       якщо це потрібно для складних сценаріїв розгортання.
#       (наприклад, target_metadata = {'schema_name': Base.metadata})

# --- Офлайн режим виконання міграцій ---
def run_migrations_offline() -> None:
    """
    Виконує міграції в "офлайн" режимі.

    У цьому режимі Alembic не підключається до реальної бази даних,
    а генерує SQL скрипти на основі URL бази даних. Це корисно для
    перегляду SQL, що буде виконано, або для генерації скриптів,
    які потім можна виконати вручну.
    """
    # Отримуємо URL бази даних з налаштувань додатка.
    # Для офлайн режиму потрібен синхронний URL.
    url = app_settings.get_db_url_sync()  # Метод для отримання синхронного URL
    # i18n: Log message - Running migrations in offline mode
    context.configure(
        url=url,  # URL бази даних
        target_metadata=target_metadata,  # Метадані для порівняння
        literal_binds=True,  # Генерувати SQL з літеральними значеннями замість placeholder'ів
        dialect_opts={"paramstyle": "named"},  # Опції діалекту SQLAlchemy
        # compare_type=True # Дозволяє виявляти зміни типів колонок (може бути корисним)
    )

    # Виконуємо міграції в межах транзакції
    with context.begin_transaction():
        context.run_migrations()
    # i18n: Log message - Offline migrations finished (output to script)
    logger.info(_("Офлайн міграції згенеровано (виведено в стандартний вивід або файл)."))


# --- Онлайн режим виконання міграцій ---
def do_run_migrations(connection) -> None:
    """
    Допоміжна функція для запуску міграцій з існуючим підключенням до БД.
    Використовується `run_migrations_online`.

    Args:
        connection: Активне SQLAlchemy підключення.
    """
    # Налаштовуємо контекст Alembic для використання існуючого підключення.
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Рекомендується для виявлення змін типів колонок
        # compare_server_default=True, # Розглянути, якщо потрібно виявляти зміни server_default
        # include_schemas=True, # Якщо використовуються різні схеми PostgreSQL
    )
    # TODO: Додати специфічні для проекту опції `context.configure()`, якщо потрібно:
    #       - `include_object`: функція для фільтрації таблиць/об'єктів, які Alembic має відстежувати.
    #       - `process_revision_directives`: для кастомізації процесу автогенерації.

    # Виконуємо міграції в межах транзакції
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Виконує міграції в "онлайн" режимі.

    У цьому режимі Alembic підключається до реальної бази даних,
    створює рушій (Engine) та виконує міграції через активне підключення.
    """
    # Отримуємо секцію конфігурації для поточної БД з alembic.ini (зазвичай [alembic])
    # або використовуємо порожній словник, якщо секція не знайдена.
    connectable_configuration = config.get_section(config.config_ini_section, {})

    # Встановлюємо URL бази даних для Alembic з налаштувань додатка.
    # Для онлайн режиму з asyncio потрібен асинхронний URL.
    connectable_configuration["sqlalchemy.url"] = app_settings.get_db_url_async()  # Метод для отримання async URL

    # Створюємо асинхронний рушій SQLAlchemy з конфігурації.
    connectable = async_engine_from_config(
        connectable_configuration,  # Використовуємо модифіковану конфігурацію
        prefix="sqlalchemy.",  # Префікс для ключів SQLAlchemy в конфігурації
        poolclass=pool.NullPool,  # Використовуємо NullPool, оскільки Alembic керує підключеннями сам
        # і для короткоживучих скриптів пул не завжди потрібен.
    )

    # Асинхронно підключаємося до БД
    async with connectable.connect() as connection:
        # Виконуємо функцію do_run_migrations синхронно в межах асинхронного підключення.
        # run_sync() дозволяє викликати синхронний код, який використовує SQLAlchemy Core (Alembic),
        # з асинхронного контексту.
        await connection.run_sync(do_run_migrations)

    # Звільняємо ресурси рушія після завершення роботи.
    await connectable.dispose()
    # i18n: Log message - Online migrations finished
    logger.info(_("Онлайн міграції успішно застосовано до бази даних."))


# --- Визначення режиму виконання ---
# Alembic може працювати в двох режимах:
# - Офлайн: генерує SQL скрипти без підключення до БД.
# - Онлайн: підключається до БД і виконує міграції.
if context.is_offline_mode():
    # i18n: Log message - Running in offline mode
    logger.info(_("Запуск Alembic в офлайн режимі..."))
    run_migrations_offline()
else:
    # i18n: Log message - Running in online mode
    logger.info(_("Запуск Alembic в онлайн режимі..."))
    asyncio.run(run_migrations_online())  # Використовуємо asyncio.run для запуску асинхронної функції
