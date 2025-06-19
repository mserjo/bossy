# backend/app/src/config/database.py
# -*- coding: utf-8 -*-
"""Налаштування підключення до бази даних для додатку.

Цей модуль відповідає за конфігурацію SQLAlchemy для асинхронної роботи з базою даних.
Він включає:
- Створення асинхронного `engine` SQLAlchemy на основі `DATABASE_URL` з файлу налаштувань.
- Створення `SessionLocal` - фабрики для асинхронних сесій бази даних (`AsyncSession`).
- Визначення базового класу `Base` для декларативних моделей SQLAlchemy.
- Функцію-залежність (dependency) `get_db_session` для FastAPI, яка надає сесію
  бази даних для кожного запиту та забезпечує її коректне закриття.
- Допоміжну функцію `create_db_and_tables` для створення таблиць на основі моделей
  (рекомендується використовувати міграції Alembic для продуктивних середовищ).

Використання:
- `engine` використовується `SessionLocal` та Alembic (для міграцій).
- `SessionLocal` використовується `get_db_session` для створення сесій в рамках запитів.
- `Base` є батьківським класом для всіх моделей даних SQLAlchemy у проекті.
- `get_db_session` інжектується в ендпоінти FastAPI для взаємодії з базою даних.
"""
import asyncio # Для демонстраційного блоку if __name__ == "__main__"
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Абсолютний імпорт налаштувань та логера
from backend.app.src.config.settings import settings as app_settings # Перейменовано для уникнення конфлікту
from backend.app.src.config.logging import get_logger

logger = get_logger(__name__)

# --- Налаштування SQLAlchemy Engine ---
# `engine` є центральним об'єктом доступу до бази даних для SQLAlchemy.
# Він налаштовується за допомогою URL бази даних, отриманого з конфігураційних налаштувань.
# `create_async_engine` використовується для забезпечення асинхронної роботи, сумісної з `asyncio`.
logger.info("Створення асинхронного рушія SQLAlchemy для URL: %s", app_settings.DATABASE_URL)
engine = create_async_engine(
    str(app_settings.DATABASE_URL),  # DATABASE_URL з settings.py, перетворений на рядок.
    pool_pre_ping=True,      # Вмикає тестування з'єднань перед їх використанням з пулу.
    echo=app_settings.ECHO_SQL, # Використовуємо ECHO_SQL з налаштувань для логування SQL-запитів.
    # Додаткові параметри пулу з'єднань (розкоментуйте та налаштуйте за потреби):
    # pool_size=app_settings.DB_POOL_SIZE, # Кількість з'єднань в пулі
    # max_overflow=app_settings.DB_MAX_OVERFLOW, # Максимальна кількість додаткових з'єднань
    # pool_recycle=3600,       # Час в секундах, після якого з'єднання автоматично перестворюється.
    # pool_timeout=30,         # Час в секундах очікування вільного з'єднання з пулу.
)

# --- Фабрика сесій SQLAlchemy ---
# `SessionLocal` є фабрикою для створення екземплярів `AsyncSession`.
# Кожен екземпляр `AsyncSession` представляє окрему сесію (транзакцію) з базою даних.
SessionLocal = sessionmaker(
    autocommit=False,        # Вимикає автоматичний коміт. Зміни потрібно комітити явно.
    autoflush=False,         # Вимикає автоматичний flush. Зміни надсилаються до БД лише при коміті або явному flush.
    bind=engine,             # Прив'язує фабрику сесій до створеного `engine`.
    class_=AsyncSession,     # Використовує `AsyncSession` для асинхронних операцій.
    expire_on_commit=False,  # Встановлено в False, щоб об'єкти залишалися доступними після коміту сесії.
                             # Це важливо для FastAPI, де об'єкти можуть використовуватися після завершення транзакції.
)
logger.info("Фабрику асинхронних сесій SQLAlchemy (SessionLocal) налаштовано.")

# --- Базовий клас для декларативних моделей SQLAlchemy ---
# Всі моделі даних, що відображають таблиці бази даних, повинні успадковувати цей клас.
# `DeclarativeBase` надає функціональність для визначення моделей та їх зв'язку з таблицями.
class Base(DeclarativeBase):
    """Базовий клас для всіх моделей SQLAlchemy.

    Надає декларативну основу для визначення таблиць та їх метаданих.
    Моделі, успадковані від цього класу, автоматично відстежуються SQLAlchemy
    та використовуються Alembic для генерації міграцій.
    """
    pass

logger.debug("Базовий клас для моделей SQLAlchemy (Base) визначено.")

# --- Залежність FastAPI для отримання сесії бази даних ---
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронна функція-залежність FastAPI для отримання сесії бази даних.

    Ця функція є асинхронним генератором (`AsyncGenerator`). Вона створює нову
    асинхронну сесію (`AsyncSession`) перед обробкою запиту, передає її
    у відповідний ендпоінт, а потім гарантує, що сесія буде належним чином
    закрита після завершення запиту.

    У разі успішного виконання операцій в ендпоінті, транзакція комітиться.
    Якщо під час обробки запиту виникає виняток, транзакція відкочується.
    Сесія закривається в будь-якому випадку у блоці `finally`.

    Використання в ендпоінті FastAPI:
    ```python
    from fastapi import APIRouter, Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from backend.app.src.config.database import get_db_session

    router = APIRouter()

    @router.post("/items/")
    async def create_item(item_data: dict, db: AsyncSession = Depends(get_db_session)):
        # ... ваш код для роботи з db (сесією бази даних) ...
        return {"message": "Item created successfully"}
    ```

    Yields:
        AsyncSession: Асинхронна сесія SQLAlchemy для взаємодії з базою даних.
    """
    logger.debug("Запит на нову сесію бази даних.")
    async with SessionLocal() as session:
        try:
            logger.debug("Сесію бази даних (%s) надано запиту.", id(session))
            yield session
            # Якщо не було винятків, комітимо транзакцію
            await session.commit()
            logger.debug("Транзакцію для сесії (%s) успішно закоммічено.", id(session))
        except Exception as e:
            logger.error(
                "Помилка під час обробки запиту з сесією БД (%s): %s. Відкочуємо транзакцію.",
                id(session), e, exc_info=True
            )
            await session.rollback()
            raise # Передаємо виняток далі для стандартної обробки FastAPI
        # `async with SessionLocal() as session:` автоматично закриває сесію,
        # тому явний `await session.close()` у `finally` не потрібен.


# --- Функція для ініціалізації бази даних (створення таблиць) ---
# ВАЖЛИВО: Ця функція призначена для використання в середовищах розробки або тестування
# для початкового створення таблиць на основі моделей SQLAlchemy.
# Для продуктивних середовищ настійно рекомендується використовувати систему міграцій,
# таку як Alembic, для управління змінами схеми бази даних.
async def create_db_and_tables() -> None:
    """Асинхронно створює всі таблиці в базі даних.

    Таблиці створюються на основі метаданих моделей SQLAlchemy,
    що успадковують від класу `Base`.

    ПОПЕРЕДЖЕННЯ: Цю функцію слід використовувати з обережністю, переважно
    для розробки або тестування. У продуктивному середовищі для управління
    схемою бази даних використовуйте інструменти міграцій (наприклад, Alembic).
    Не викликайте цю функцію, якщо у вас вже є дані в таблицях, керованих Alembic.
    """
    logger.info("Спроба створення таблиць бази даних (якщо вони ще не існують)...")
    async with engine.begin() as conn:
        # Наступний рядок видалить ВСІ таблиці перед створенням нових.
        # НЕ ВИКОРИСТОВУЙТЕ В ПРОДАКШЕНІ без чіткого розуміння наслідків!
        # logger.warning("Видалення всіх існуючих таблиць перед створенням нових (drop_all).")
        # await conn.run_sync(Base.metadata.drop_all)

        # Створює таблиці на основі метаданих моделей.
        # Ця операція є безпечною, якщо таблиці вже існують (вона їх не дублює).
        await conn.run_sync(Base.metadata.create_all)
    logger.info(
        "Таблиці бази даних успішно перевірено/створено. "
        "Для управління змінами схеми в продуктивному середовищі використовуйте міграції Alembic."
    )

# Блок для демонстрації або тестування функціональності цього модуля
if __name__ == "__main__":
    # У реальному додатку setup_logging() викликається централізовано при старті.
    # Тут це для демонстрації, якщо файл запускається окремо.
    # Логер вже налаштований на рівні модуля.

    async def main_test_db_connection() -> None:
        """Тестує створення таблиць та отримання сесії бази даних."""
        logger.info("=== Демонстрація налаштувань бази даних ===")
        logger.info("Спроба створити таблиці бази даних (тільки для розробки/тестування)...")
        await create_db_and_tables()

        logger.info("\nПеревірка з'єднання з базою даних шляхом створення тестової сесії...")
        try:
            # Використовуємо асинхронний генератор для отримання сесії
            db_session_generator = get_db_session()
            # Отримуємо сесію з генератора
            session = await anext(db_session_generator)
            try:
                logger.info("Успішно отримано сесію БД: %s", session)
                # Тут можна додати простий запит для перевірки, якщо є моделі
                # from sqlalchemy import text
                # result = await session.execute(text("SELECT 1 AS value"))
                # logger.info("Результат тестового запиту 'SELECT 1': %s", result.scalar_one_or_none())
                logger.info("Тестова сесія успішно відкрита та готова до роботи.")
            finally:
                # Гарантуємо закриття генератора, що також викличе commit/rollback/close у get_db_session
                try:
                    # Імітуємо завершення роботи з сесією, щоб генератор відпрацював блок finally
                    await db_session_generator.asend(None) # або .aclose() в Python 3.10+
                except StopAsyncIteration:
                    # Це очікуваний результат, коли генератор вичерпано
                    pass
            logger.info("Сесію БД успішно отримано, (імітовано роботу) та закрито.")
        except Exception as e: # pylint: disable=broad-except
            logger.error("Помилка під час перевірки сесії БД: %s", e, exc_info=True)

    # Запуск тестової функції
    asyncio.run(main_test_db_connection())
