# backend/app/src/config/database.py
# -*- coding: utf-8 -*-
"""
Налаштування підключення до бази даних для FastAPI програми Kudos.

Цей модуль відповідає за конфігурацію SQLAlchemy для асинхронної роботи з базою даних.
Він включає:
- Створення асинхронного `engine` SQLAlchemy на основі `DATABASE_URL` з налаштувань.
- Створення `SessionLocal` - фабрики для асинхронних сесій бази даних (`AsyncSession`).
- Визначення базового класу `Base` для декларативних моделей SQLAlchemy.
- Функцію-залежність `get_db` для FastAPI, яка надає сесію бази даних для кожного запиту
  та забезпечує її коректне закриття.
- Допоміжну функцію `create_db_and_tables` для створення таблиць (рекомендується
  використовувати міграції Alembic для продакшн середовищ).

Використання:
- `engine` використовується `SessionLocal` та Alembic для міграцій.
- `SessionLocal` використовується `get_db` для створення сесій.
- `Base` є батьківським класом для всіх моделей даних SQLAlchemy.
- `get_db` інжектується в ендпоінти FastAPI для взаємодії з БД.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import AsyncGenerator

# Абсолютний імпорт налаштувань
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import get_logger # Імпорт логера

# Отримання логера для цього модуля
logger = get_logger(__name__)

# --- Налаштування SQLAlchemy Engine ---
# `engine` є центральним об'єктом доступу до бази даних для SQLAlchemy.
# Він налаштовується за допомогою URL бази даних, отриманого з конфігураційних налаштувань.
# `create_async_engine` використовується для забезпечення асинхронної роботи, сумісної з `asyncio`.
engine = create_async_engine(
    str(settings.DATABASE_URL),  # DATABASE_URL з settings.py, перетворений на рядок.
    pool_pre_ping=True,      # Вмикає тестування з'єднань перед їх використанням з пулу. Допомагає уникнути проблем з "мертвими" з'єднаннями.
    echo=settings.DEBUG,       # Якщо DEBUG=True в налаштуваннях, SQLAlchemy логуватиме всі SQL-запити. Корисно для налагодження.
    # Додаткові параметри пулу з'єднань (розкоментуйте та налаштуйте за потреби):
    # pool_size=10,            # Кількість з'єднань, які тримаються відкритими в пулі.
    # max_overflow=20,         # Максимальна кількість з'єднань, які можуть бути створені понад `pool_size`.
    # pool_recycle=3600,       # Час в секундах, після якого з'єднання автоматично перестворюється (наприклад, 3600 для 1 години).
    # pool_timeout=30,         # Час в секундах, протягом якого очікується вільне з'єднання з пулу перед виникненням помилки.
)

# --- Фабрика сесій SQLAlchemy ---
# `SessionLocal` є фабрикою для створення екземплярів `AsyncSession`.
# Кожен екземпляр `AsyncSession` представляє окрему сесію (транзакцію) з базою даних.
SessionLocal = sessionmaker(
    autocommit=False,        # Вимикає автоматичний коміт. Зміни потрібно комітити явно.
    autoflush=False,         # Вимикає автоматичний flush. Зміни відправляються до БД лише при коміті або явному flush.
    bind=engine,             # Прив'язує фабрику сесій до створеного `engine`.
    class_=AsyncSession,     # Використовує `AsyncSession` для асинхронних операцій.
    expire_on_commit=False,  # Встановлено в False, щоб об'єкти залишалися доступними після коміту сесії.
                             # Це важливо для FastAPI, де об'єкти можуть використовуватися після завершення транзакції в запиті.
)

# --- Базовий клас для декларативних моделей SQLAlchemy ---
# Всі моделі даних, що відображають таблиці бази даних, повинні успадковувати цей клас.
# `DeclarativeBase` надає функціональність для визначення моделей та їх зв'язку з таблицями.
class Base(DeclarativeBase):
    """
    Базовий клас для всіх моделей SQLAlchemy.
    Надає декларативну основу для визначення таблиць та їх метаданих.
    """
    pass

# --- Залежність FastAPI для отримання сесії бази даних ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронна функція-залежність для FastAPI, яка надає сесію бази даних (`AsyncSession`)
    для одного HTTP-запиту.

    Ця функція є асинхронним генератором. Вона створює нову сесію перед обробкою запиту,
    передає її у відповідний ендпоінт, а потім гарантує, що сесія буде належним чином
    закрита після завершення запиту. У разі успіху зміни комітяться, у разі помилки – відкочуються.

    Використання:
        @router.post("/")
        async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
            # ... ваш код для роботи з db ...

    Yields:
        AsyncSession: Асинхронна сесія SQLAlchemy для взаємодії з базою даних.
    """
    async with SessionLocal() as session: # Створює нову сесію та гарантує її закриття
        try:
            yield session  # Передає сесію в ендпоінт
            await session.commit() # Якщо в ендпоінті не було помилок, комітить транзакцію
        except Exception:
            await session.rollback() # У разі виникнення помилки в ендпоінті, відкочує транзакцію
            raise # Передає виняток далі для обробки FastAPI
        finally:
            # Хоча `async with` вже закриває сесію, явний close тут не завадить для деяких сценаріїв,
            # але зазвичай він не потрібен при використанні `async with SessionLocal() as session:`.
            # Для `sqlalchemy.orm.sessionmaker` з `AsyncSession` контекстний менеджер `async with`
            # сам обробляє `close()`. Залишено для ясності або специфічних випадків.
            await session.close() # Остаточно закриває сесію

# --- Функція для ініціалізації бази даних (створення таблиць) ---
# ВАЖЛИВО: Ця функція призначена для використання в середовищах розробки або тестування
# для початкового створення таблиць на основі моделей SQLAlchemy.
# Для продакшн-середовищ настійно рекомендується використовувати систему міграцій,
# таку як Alembic, для управління змінами схеми бази даних.
async def create_db_and_tables():
    """
    Асинхронно створює всі таблиці в базі даних, які визначені моделями,
    що успадковують від класу `Base`.

    ПОПЕРЕДЖЕННЯ: Цю функцію слід використовувати з обережністю.
    У продакшн-середовищі для управління схемою бази даних
    використовуйте інструменти міграцій (наприклад, Alembic).
    """
    async with engine.begin() as conn:
        # Наступний рядок видалить ВСІ таблиці перед створенням нових.
        # Використовуйте з максимальною обережністю, особливо з реальними даними!
        # await conn.run_sync(Base.metadata.drop_all)

        # Створює таблиці на основі метаданих моделей.
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблиці бази даних успішно створено (якщо вони не існували до цього). "
                "Для продакшену використовуйте міграції Alembic.")

# Блок для демонстрації або тестування функціональності цього модуля
if __name__ == "__main__":
    import asyncio

    # Налаштування базового логування для випадку, якщо setup_logging ще не викликано
    # (наприклад, при прямому запуску цього файлу).
    # У реальному застосунку setup_logging() викликається централізовано.
    try:
        from backend.app.src.config.logging import setup_logging
        setup_logging() # Застосувати конфігурацію логування
    except ImportError:
        import logging as base_logging
        base_logging.basicConfig(level=base_logging.INFO)
        logger.warning("Не вдалося імпортувати setup_logging. Використовується базова конфігурація логування для database.py.")


    async def main_test_db_connection():
        """Тестує створення таблиць та отримання сесії бази даних."""
        logger.info("Спроба створити таблиці бази даних (тільки для розробки/тестування)...")
        await create_db_and_tables()
        logger.info("\nПеревірка з'єднання з базою даних шляхом створення тестової сесії...")
        try:
            # Використовуємо асинхронний генератор для отримання сесії
            db_session_generator = get_db()
            session = await anext(db_session_generator) # Отримуємо сесію
            try:
                logger.info(f"Успішно отримано сесію БД: {session}")
                # Приклад простого запиту (потребує визначених моделей або використання text)
                # from sqlalchemy import text
                # result = await session.execute(text("SELECT 1 AS value"))
                # logger.info(f"Результат тестового запиту 'SELECT 1': {result.scalar_one_or_none()}")
                logger.info("Тестова сесія успішно відкрита та готова до роботи.")
            finally:
                # Гарантуємо закриття генератора, що також викличе commit/rollback/close у get_db
                try:
                    await anext(db_session_generator)
                except StopAsyncIteration:
                    pass # Очікувано, генератор вичерпано
            logger.info("Сесію БД успішно отримано, (імітовано роботу) та закрито.")
        except Exception as e:
            logger.error(f"Помилка під час перевірки сесії БД: {e}", exc_info=True)
            # import traceback # traceback вже включено в exc_info=True
            # traceback.print_exc()

    # Запуск тестової функції
    asyncio.run(main_test_db_connection())
