# backend/app/src/config/database.py
# -*- coding: utf-8 -*-
# # Модуль конфігурації бази даних для FastAPI програми Kudos (Virtus).
# #
# # Відповідає за налаштування SQLAlchemy для асинхронних операцій з базою даних.
# # Включає створення асинхронного рушія (`engine`), фабрики сесій (`SessionLocal`)
# # та залежності FastAPI (`get_db`) для надання сесій базі даних.
# #
# # Важливо: декларативний базовий клас `Base` для моделей SQLAlchemy повинен бути
# # визначений в одному централізованому місці (наприклад, `backend.app.src.models.base.py`)
# # та імпортований сюди, а також в `alembic/env.py` та в усі файли моделей.

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker #, DeclarativeBase # DeclarativeBase буде імпортовано
from typing import AsyncGenerator

# Абсолютний імпорт налаштувань та логера
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)

# --- Налаштування SQLAlchemy Engine ---
# `engine` є центральним об'єктом доступу до бази даних для SQLAlchemy.
# Він налаштовується за допомогою URL бази даних, отриманого з конфігураційних налаштувань.
# `create_async_engine` використовується для забезпечення асинхронної роботи, сумісної з `asyncio`.
# i18n: Log message - Creating SQLAlchemy async engine
logger.debug(f"Створення асинхронного рушія SQLAlchemy для URL: {settings.DATABASE_URL}")
engine = create_async_engine(
    str(settings.DATABASE_URL),  # DATABASE_URL з settings.py, перетворений на рядок.
    pool_pre_ping=True,      # Вмикає тестування з'єднань перед їх використанням з пулу. Допомагає уникнути проблем з "мертвими" з'єднаннями.
    echo=settings.DEBUG,       # Якщо DEBUG=True в налаштуваннях, SQLAlchemy логуватиме всі SQL-запити. Корисно для налагодження.
    # Додаткові параметри пулу з'єднань (розкоментуйте та налаштуйте за потреби):
    # pool_size=10,            # Кількість з'єднань, які тримаються відкритими в пулі (дефолт 5 для asyncpg).
    # max_overflow=20,         # Максимальна кількість з'єднань, які можуть бути створені понад `pool_size` (дефолт 10).
    # pool_recycle=3600,       # Час в секундах, після якого з'єднання автоматично перестворюється (наприклад, 3600 для 1 години).
    # pool_timeout=30,         # Час в секундах, протягом якого очікується вільне з'єднання з пулу перед виникненням помилки.
)

# --- Фабрика сесій SQLAlchemy ---
# `SessionLocal` є фабрикою для створення екземплярів `AsyncSession`.
# Кожен екземпляр `AsyncSession` представляє окрему сесію (транзакцію) з базою даних.
# i18n: Log message - Configuring SQLAlchemy session factory (SessionLocal)
logger.debug("Налаштування фабрики сесій SQLAlchemy (SessionLocal) для AsyncSession.")
SessionLocal = sessionmaker(
    autocommit=False,        # Вимикає автоматичний коміт. Зміни потрібно комітити явно (`await session.commit()`).
    autoflush=False,         # Вимикає автоматичний flush. Зміни відправляються до БД лише при коміті або явному `await session.flush()`.
    bind=engine,             # Прив'язує фабрику сесій до створеного асинхронного `engine`.
    class_=AsyncSession,     # Використовує `AsyncSession` для асинхронних операцій.
    expire_on_commit=False,  # Встановлено в False, щоб об'єкти SQLAlchemy залишалися доступними (не "відкріпленими") після коміту сесії.
                             # Це важливо для FastAPI, де об'єкти можуть використовуватися після завершення транзакції в запиті.
)

# --- Базовий клас для декларативних моделей SQLAlchemy ---
# Всі моделі даних, що відображають таблиці бази даних, повинні успадковувати цей клас.
# `DeclarativeBase` надає функціональність для визначення моделей та їх зв'язку з таблицями.
# class Base(DeclarativeBase): # Закоментовано згідно завдання
#     """
#     Базовий клас для всіх моделей SQLAlchemy.
#     Надає декларативну основу для визначення таблиць та їх метаданих.
#     """
#     pass
# TODO: (Важливо) Визначення декларативного базового класу `Base` було тут закоментовано.
# `Base` має бути визначений в одному централізованому місці (рекомендовано в `backend.app.src.models.base.py`)
# і потім імпортований сюди, в `alembic/env.py` та в усі файли моделей.
# Це буде виправлено під час рев'ю директорії моделей.
# Приклад необхідного імпорту (буде розкоментовано та скориговано пізніше):
# from backend.app.src.models.base import Base

# --- Залежність FastAPI для отримання сесії бази даних ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронна функція-залежність FastAPI, яка надає сесію бази даних (`AsyncSession`)
    для одного HTTP-запиту та гарантує її належне закриття.

    Ця функція є асинхронним генератором. Вона створює нову сесію перед обробкою запиту,
    передає її у відповідний ендпоінт (`yield session`), а потім, після завершення роботи ендпоінта,
    намагається закомітити транзакцію. У разі виникнення помилки транзакція відкочується.
    Сесія завжди закривається в блоці `finally`.

    Використання в ендпоінті:
        `db: AsyncSession = Depends(get_db)`

    Yields:
        AsyncSession: Асинхронна сесія SQLAlchemy для взаємодії з базою даних.
    """
    # i18n: Log message - Creating DB session for request
    logger.debug("Створення сесії БД для запиту...")
    async with SessionLocal() as session: # Створює нову сесію та гарантує її автоматичне закриття через контекстний менеджер
        try:
            yield session  # Передає сесію в ендпоінт
            # i18n: Log message - Committing DB session after request
            logger.debug("Коміт сесії БД після успішного запиту.")
            await session.commit() # Якщо в ендпоінті не було помилок, комітить транзакцію
        except Exception as e:
            # i18n: Log message - Rolling back DB session due to exception
            logger.error(f"Помилка під час обробки запиту, відкат сесії БД: {e}", exc_info=settings.DEBUG)
            await session.rollback() # У разі виникнення помилки в ендпоінті, відкочує транзакцію
            raise # Передає виняток далі для обробки FastAPI або кастомним обробником помилок
        # `finally` блок тут не потрібен для `await session.close()`,
        # оскільки `async with SessionLocal() as session:` вже гарантує закриття сесії.

# --- Функція для ініціалізації бази даних (створення таблиць) ---
# ВАЖЛИВО: Ця функція призначена для використання в середовищах розробки або тестування
# для початкового створення таблиць на основі моделей SQLAlchemy.
# Для продакшн-середовищ настійно рекомендується використовувати систему міграцій,
# таку як Alembic, для управління змінами схеми бази даних.
async def create_db_and_tables(drop_first: bool = False): # Додано параметр drop_first
    """
    Асинхронно створює всі таблиці в базі даних, які визначені моделями,
    що успадковують від імпортованого класу `Base`.

    ПОПЕРЕДЖЕННЯ: Цю функцію слід використовувати з обережністю.
    У продакшн-середовищі для управління схемою бази даних
    використовуйте інструменти міграцій (наприклад, Alembic).

    Args:
        drop_first (bool): Якщо True, всі існуючі таблиці (визначені в Base.metadata)
                           будуть видалені перед створенням нових. ВИКОРИСТОВУЙТЕ ОБЕРЕЖНО!
    """
    # TODO: Ця функція залежатиме від правильного імпорту `Base` після його централізації.
    # Поки що вона може не працювати належним чином, якщо `Base` не імпортовано.
    from backend.app.src.models.base import Base # Тимчасовий імпорт для демонстрації, буде виправлено

    # i18n: Log message - Attempting to create database tables
    logger.info(_("Спроба створити таблиці бази даних..."))
    if not Base.metadata.tables:
        logger.warning(_("Метадані Base не містять таблиць. Перевірте імпорт моделей та визначення Base."))
        return

    async with engine.begin() as conn:
        if drop_first:
            # i18n: Log message - Dropping all tables
            logger.warning(_("УВАГА: Видалення всіх таблиць (drop_first=True)..."))
            await conn.run_sync(Base.metadata.drop_all)
            logger.info(_("Всі таблиці успішно видалені."))

        # Створює таблиці на основі метаданих моделей.
        # i18n: Log message - Creating tables
        logger.info(_("Створення таблиць на основі метаданих моделей..."))
        await conn.run_sync(Base.metadata.create_all)
    # i18n: Log message - Database tables successfully created/verified
    logger.info(_("Таблиці бази даних успішно створено/перевірено. Для продакшену використовуйте міграції Alembic."))

# Блок для демонстрації або тестування функціональності цього модуля
if __name__ == "__main__":
    import asyncio

    # Налаштування базового логування для випадку, якщо setup_logging ще не викликано
    # (наприклад, при прямому запуску цього файлу).
    # У реальному застосунку setup_logging() викликається централізовано.
    try:
        from backend.app.src.config.logging import setup_logging
        if settings.LOG_TO_FILE: # Налаштовуємо логування у файл, якщо вказано
            log_file_path = settings.LOG_DIR / f"{Path(__file__).stem}.log" # Лог файл для цього модуля
            setup_logging(log_file_path=log_file_path)
        else:
            setup_logging() # Стандартне логування в консоль
    except ImportError:
        import logging as base_logging
        base_logging.basicConfig(level=base_logging.INFO)
        logger.warning(_("Не вдалося імпортувати setup_logging. Використовується базова конфігурація логування для database.py."))

    async def main_test_db_connection():
        """Тестує створення таблиць та отримання сесії бази даних."""
        logger.info(_("Тестування модуля database.py..."))
        # ВАЖЛИВО: Для тестування create_db_and_tables потрібен імпортований Base.
        # Оскільки Base тут закоментовано, цей виклик може не працювати як очікувалось,
        # доки Base не буде правильно імпортовано з центрального місця.
        # Для безпеки, drop_first=False за замовчуванням.
        await create_db_and_tables(drop_first=False) # Встановіть True, якщо потрібно перестворити таблиці

        logger.info(_("\nПеревірка з'єднання з базою даних шляхом створення тестової сесії..."))
        try:
            db_session_generator = get_db()
            session = await anext(db_session_generator)
            try:
                logger.info(_("Успішно отримано сесію БД: %s") % session)
                # Приклад простого запиту (потребує визначених моделей або використання text)
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1 AS value"))
                logger.info(_("Результат тестового запиту 'SELECT 1': %s") % result.scalar_one_or_none())
                logger.info(_("Тестова сесія успішно відкрита та готова до роботи."))
            finally:
                try:
                    await anext(db_session_generator) # Завершуємо роботу генератора
                except StopAsyncIteration:
                    pass # Очікувано, генератор вичерпано
            logger.info(_("Сесію БД успішно отримано, (імітовано роботу) та закрито."))
        except Exception as e:
            logger.error(_("Помилка під час перевірки сесії БД: %s") % e, exc_info=settings.DEBUG)

    # Запуск тестової функції
    asyncio.run(main_test_db_connection())
