# backend/alembic/env.py
# -*- coding: utf-8 -*-
# # Файл конфігурації Alembic `env.py`.
# # Цей файл відповідає за налаштування середовища виконання Alembic для проекту.
# # Він визначає, як Alembic підключається до бази даних, яку мету (`target_metadata`)
# # використовувати для автогенерації міграцій, та як виконувати міграції
# # в онлайн (з підключенням до БД) та офлайн (генерація SQL скриптів) режимах.
# # Особливу увагу приділено налаштуванню для асинхронної роботи з SQLAlchemy.

import asyncio
import logging
from logging.config import fileConfig

# Налаштування логера для цього файлу (буде керуватися fileConfig з alembic.ini)
logger = logging.getLogger("alembic.env")

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config  # Для асинхронного рушія SQLAlchemy

from alembic import context  # Об'єкт контексту Alembic

# --- Налаштування шляхів Python ---
# Додаємо корінь 'backend' до sys.path, щоб Alembic міг знайти модулі додатка,
# такі як моделі SQLAlchemy та конфігурацію.
import os
import sys

# SCRIPT_DIR вказує на директорію, де знаходиться цей файл (тобто `backend/alembic/`).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# BACKEND_DIR повинен вказувати на директорію `backend/`.
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
    # i18n: Log message - Added BACKEND_DIR to sys.path
    logger.debug(f"Додано {BACKEND_DIR} до sys.path для Alembic.")


# --- Імпорт метаданих моделей та налаштувань БД ---
# Імпортуємо централізований декларативний базовий клас `Base` з `models.base`.
# `Base.metadata` є об'єктом `MetaData`, який Alembic використовує для автогенерації міграцій.
from backend.app.src.models.base import Base  # Імпорт централізованого Base

# Імпортуємо ВСІ моделі SQLAlchemy вашого додатку.
# Це необхідно для того, щоб Alembic "бачив" їх і міг порівнювати
# їх поточний стан зі станом у базі даних для автогенерації міграцій.
# Переконайтеся, що __init__.py в директорії models (або її підмодулях)
# імпортує всі класи моделей, або імпортуйте їх тут явно.
# i18n: Log message - Importing models for Alembic
logger.debug("Імпорт моделей SQLAlchemy для Alembic...")
import backend.app.src.models  # Це завантажить всі моделі, якщо models/__init__.py їх імпортує

# Імпортуємо об'єкт налаштувань додатка для отримання URL бази даних.
# TODO: Перевірити та узгодити шлях імпорту settings, якщо він відрізняється.
from backend.app.src.core.config import settings as app_settings  # Припускаємо, що settings - це об'єкт Pydantic Settings

# Базова функція-заглушка для інтернаціоналізації рядків (якщо потрібна в коментарях або логах)
def _(text: str) -> str:
    # У реальному проекті тут може бути інтеграція з gettext або іншою системою i18n.
    return text


# --- Загальні налаштування Alembic ---
# Це об'єкт конфігурації Alembic, який отримує доступ до значень з alembic.ini.
config = context.config

# Інтерпретація файлу конфігурації для логування Python (зазвичай alembic.ini).
# Цей рядок дозволяє налаштувати логування Alembic через секції [loggers], [handlers], [formatters] в alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Встановлюємо `target_metadata` для операцій автогенерації Alembic.
# Це має бути об'єкт `MetaData` з вашого SQLAlchemy Base, що містить визначення всіх таблиць.
target_metadata = Base.metadata
# i18n: Log message - Target metadata set for Alembic
logger.debug(_("Метадані для Alembic (target_metadata) встановлено."))

# TODO: Розглянути можливість використання версіонованих таблиць або схем,
#       якщо це потрібно для складних сценаріїв розгортання.
#       (наприклад, target_metadata = {'schema_name': Base.metadata} для роботи з конкретною схемою)
#       Або можна налаштувати `include_schemas=True` в `context.configure` для онлайн режиму.

# --- Офлайн режим виконання міграцій ---
def run_migrations_offline() -> None:
    """
    Виконує міграції в "офлайн" режимі.

    У цьому режимі Alembic не підключається до реальної бази даних,
    а генерує SQL скрипти на основі URL бази даних. Це корисно для
    перегляду SQL, що буде виконано, або для генерації скриптів,
    які потім можна виконати вручну (наприклад, DBA).
    """
    # Отримуємо URL бази даних з налаштувань додатка.
    # Для офлайн режиму потрібен синхронний URL (без префіксу +asyncpg тощо).
    url = app_settings.get_db_url_sync()  # Метод для отримання синхронного URL з Pydantic Settings
    # i18n: Log message - Configuring Alembic for offline mode with URL
    logger.info(_("Налаштування Alembic для офлайн режиму з URL: %s") % url)
    context.configure(
        url=url,  # URL бази даних
        target_metadata=target_metadata,  # Метадані для порівняння
        literal_binds=True,  # Генерувати SQL з літеральними значеннями замість placeholder'ів (для SQL скриптів)
        dialect_opts={"paramstyle": "named"},  # Опції діалекту SQLAlchemy
        # compare_type=True # Дозволяє виявляти зміни типів колонок (може бути корисним, але вимагає уваги)
    )

    # Виконуємо міграції в межах транзакції (для генерації скриптів це не так критично, але є хорошою практикою)
    # i18n: Log message - Beginning offline migration generation
    logger.debug(_("Початок генерації офлайн міграцій..."))
    with context.begin_transaction():
        context.run_migrations()
    # i18n: Log message - Offline migrations finished (output to script)
    logger.info(_("Офлайн міграції успішно згенеровано (виведено в стандартний вивід або файл)."))


# --- Онлайн режим виконання міграцій ---
def do_run_migrations(connection) -> None:
    """
    Допоміжна функція для запуску міграцій з існуючим підключенням до БД.
    Використовується `run_migrations_online`.

    Args:
        connection: Активне SQLAlchemy підключення.
    """
    # i18n: Log message - Configuring Alembic context for online migration
    logger.debug(_("Налаштування контексту Alembic для онлайн міграції..."))
    # Налаштовуємо контекст Alembic для використання існуючого підключення.
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Рекомендується для виявлення змін типів колонок при автогенерації
        # compare_server_default=True, # Розглянути, якщо потрібно виявляти зміни server_default
        # include_schemas=True, # Якщо використовуються різні схеми PostgreSQL (наприклад, public, my_schema)
    )
    # TODO: Додати специфічні для проекту опції `context.configure()`, якщо потрібно:
    #       - `include_object(object, name, type_, reflected, compare_to)`: функція для фільтрації таблиць/об'єктів.
    #       - `process_revision_directives(context, revision, directives)`: для кастомізації процесу автогенерації.

    # Виконуємо міграції в межах транзакції
    # i18n: Log message - Beginning online migration execution
    logger.debug(_("Початок виконання онлайн міграцій..."))
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Виконує міграції в "онлайн" режимі.

    У цьому режимі Alembic підключається до реальної бази даних,
    створює асинхронний рушій (AsyncEngine) та виконує міграції через активне підключення.
    """
    # Отримуємо секцію конфігурації для поточної БД з alembic.ini (зазвичай [alembic])
    # або використовуємо порожній словник, якщо секція не знайдена.
    connectable_configuration = config.get_section(config.config_ini_section, {})

    # Встановлюємо URL бази даних для Alembic з налаштувань додатка.
    # Для онлайн режиму з asyncio потрібен асинхронний URL (наприклад, з префіксом +asyncpg).
    db_url_async = app_settings.get_db_url_async() # Метод для отримання async URL з Pydantic Settings
    connectable_configuration["sqlalchemy.url"] = db_url_async
    # i18n: Log message - Configuring Alembic for online mode with async URL
    logger.info(_("Налаштування Alembic для онлайн режиму з асинхронним URL: %s") % db_url_async)

    # Створюємо асинхронний рушій SQLAlchemy з конфігурації.
    connectable = async_engine_from_config(
        connectable_configuration,  # Використовуємо модифіковану конфігурацію з URL
        prefix="sqlalchemy.",  # Префікс для ключів SQLAlchemy в конфігурації (наприклад, sqlalchemy.url)
        poolclass=pool.NullPool,  # Використовуємо NullPool, оскільки Alembic керує підключеннями сам
                                  # і для короткоживучих скриптів міграції постійний пул не завжди потрібен.
    )

    # Асинхронно підключаємося до БД
    # i18n: Log message - Connecting to database for online migrations
    logger.debug(_("Підключення до бази даних для онлайн міграцій..."))
    async with connectable.connect() as connection:
        # Виконуємо функцію do_run_migrations синхронно в межах асинхронного підключення.
        # run_sync() дозволяє викликати синхронний код, який використовує SQLAlchemy Core (Alembic),
        # з асинхронного контексту підключення.
        await connection.run_sync(do_run_migrations)

    # Звільняємо ресурси рушія після завершення роботи.
    await connectable.dispose()
    # i18n: Log message - Online migrations finished
    logger.info(_("Онлайн міграції успішно застосовано до бази даних."))


# --- Визначення режиму виконання Alembic (офлайн або онлайн) ---
# `context.is_offline_mode()` повертає True, якщо Alembic запущено з командою `alembic revision ... --autogenerate -s <URL>`
# або `alembic upgrade ... --sql`. В іншому випадку (наприклад, `alembic upgrade head`) повертає False.
if context.is_offline_mode():
    # i18n: Log message - Running in offline mode
    logger.info(_("Запуск Alembic в офлайн режимі..."))
    run_migrations_offline()
else:
    # i18n: Log message - Running in online mode
    logger.info(_("Запуск Alembic в онлайн режимі..."))
    asyncio.run(run_migrations_online())  # Використовуємо asyncio.run для запуску асинхронної функції run_migrations_online()
