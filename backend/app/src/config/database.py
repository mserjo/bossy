# backend/app/src/config/database.py
# -*- coding: utf-8 -*-
"""
Цей модуль відповідає за налаштування підключення до бази даних PostgreSQL
з використанням SQLAlchemy 2.0 та асинхронного драйвера asyncpg.
Він створює асинхронний `engine` та фабрику асинхронних сесій `AsyncSessionLocal`.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker # type: ignore
from sqlalchemy.orm import declarative_base # type: ignore
import logging # Для логування SQL запитів, якщо потрібно

# Імпорт налаштувань бази даних з settings.py
from backend.app.src.config.settings import settings

# Отримання URL бази даних з налаштувань
DATABASE_URL = str(settings.db.DATABASE_URL) # Переконуємося, що це рядок

# Створення асинхронного SQLAlchemy engine.
# `create_async_engine` використовується для асинхронної роботи з БД.
# `echo=settings.db.DB_ECHO_LOG` вмикає логування SQL запитів, якщо встановлено в налаштуваннях.
# `pool_size` та `max_overflow` контролюють пул з'єднань.
try:
    async_engine = create_async_engine(
        DATABASE_URL,
        echo=settings.db.DB_ECHO_LOG,
        pool_size=settings.db.DB_POOL_SIZE,
        max_overflow=settings.db.DB_MAX_OVERFLOW,
        # Додаткові параметри для asyncpg, якщо потрібні:
        # connect_args={"server_settings": {"jit": "off"}} # Приклад
    )
    # Налаштування логування для SQLAlchemy, якщо echo=True
    if settings.db.DB_ECHO_LOG:
        # Можна налаштувати рівень логування для sqlalchemy.engine, щоб бачити SQL
        # Це вже робиться через параметр `echo` в `create_async_engine`.
        # Додатково можна налаштувати формат логування, якщо потрібно.
        # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        pass

except Exception as e:
    # Обробка можливих помилок при створенні engine (наприклад, неправильний DATABASE_URL)
    # Логуємо помилку і, можливо, завершуємо роботу додатку, якщо БД критична.
    # На цьому етапі (імпорт модуля) краще просто логувати,
    # а перевірка з'єднання - при старті додатку.
    # from backend.app.src.config.logging import get_logger # Уникаємо циклічного імпорту тут
    # logger = get_logger(__name__)
    # logger.error(f"Помилка створення SQLAlchemy async_engine: {e}")
    print(f"ПОМИЛКА: Не вдалося створити SQLAlchemy async_engine: {e}") # Простий print, бо логгер ще може бути не налаштований
    async_engine = None # Встановлюємо в None, щоб перевірки далі могли це врахувати


# Створення фабрики асинхронних сесій.
# `async_sessionmaker` - це новий спосіб створення сесій в SQLAlchemy 2.0.
# `expire_on_commit=False` зазвичай рекомендується для FastAPI,
# щоб об'єкти залишалися доступними після коміту сесії в межах одного запиту.
if async_engine:
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession, # Використовуємо AsyncSession
        expire_on_commit=False,
        autoflush=False, # Рекомендується False для асинхронних сесій, контроль flush вручну
        autocommit=False # Завжди False для SQLAlchemy ORM сесій
    )
else:
    # Якщо engine не створено, AsyncSessionLocal не може бути ініціалізована.
    # Це призведе до помилок далі, якщо додаток спробує використовувати БД.
    # Потрібна обробка на вищому рівні (наприклад, при старті FastAPI).
    AsyncSessionLocal = None # type: ignore
    print("ПОМИЛКА: AsyncSessionLocal не може бути створена, оскільки async_engine не ініціалізовано.")


# Базовий клас для декларативного визначення моделей SQLAlchemy.
# Всі моделі даних повинні успадковувати цей `Base`.
# Його краще визначати в `models.base`, а тут лише імпортувати, якщо потрібно.
# Оскільки він вже є в `models.base`, тут він не потрібен.
# Base = declarative_base() # Це вже зроблено в backend.app.src.models.base

# Функція-залежність для FastAPI для отримання асинхронної сесії БД.
async def get_db_session() -> AsyncSession:
    """
    Залежність FastAPI для отримання асинхронної сесії бази даних.
    Забезпечує відкриття та закриття сесії для кожного запиту.
    """
    if AsyncSessionLocal is None:
        # Це критична помилка, якщо сесія не може бути створена.
        # Додаток не зможе працювати з БД.
        # from backend.app.src.config.logging import get_logger
        # logger = get_logger(__name__)
        # logger.critical("AsyncSessionLocal не ініціалізована! Неможливо отримати сесію БД.")
        # Можна кинути виняток, щоб FastAPI повернуло помилку 500.
        raise RuntimeError("Помилка конфігурації бази даних: AsyncSessionLocal не ініціалізована.")

    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
        # За замовчуванням, FastAPI не робить commit автоматично.
        # Це має робитися в репозиторіях або сервісах.
        # await session.commit() # НЕ РОБИТИ COMMIT ТУТ!
    except Exception as e:
        # Якщо виникла помилка під час обробки запиту, відкочуємо транзакцію.
        await session.rollback()
        raise e # Перекидаємо виняток далі
    finally:
        # Завжди закриваємо сесію після використання.
        await session.close()

# TODO: Додати функцію для перевірки з'єднання з БД при старті додатку.
# async def check_db_connection():
#     try:
#         async with async_engine.connect() as connection:
#             # Можна виконати простий запит, наприклад, SELECT 1
#             # result = await connection.execute(text("SELECT 1"))
#             # scalar_result = result.scalar_one()
#             # if scalar_result == 1:
#             #     logger.info("Успішне підключення до бази даних.")
#             # else:
#             #     logger.error("Помилка перевірки підключення до бази даних: неочікуваний результат.")
#             pass # Просто спроба підключення
#         logger.info("З'єднання з базою даних успішно перевірено.")
#         return True
#     except Exception as e:
#         logger.error(f"Помилка підключення до бази даних: {e}")
#         return False

# TODO: Подумати про ініціалізацію таблиць (Alembic міграції).
# Створення таблиць зазвичай виконується через Alembic (`alembic upgrade head`).
# Функція `Base.metadata.create_all(bind=engine)` не рекомендується для production
# з Alembic, але може бути корисною для тестів або простої ініціалізації.
# Для асинхронного engine:
# async def create_db_tables():
#     async with async_engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
# Це має викликатися лише якщо таблиці ще не створені (наприклад, при першому запуску).
# Краще покладатися на Alembic.

# Перевірка змінних середовища (чи завантажилися з .env або передані)
if not DATABASE_URL or "None" in DATABASE_URL: # PydanticDsn може стати "None" рядком, якщо не валідне
    # from backend.app.src.config.logging import get_logger
    # logger = get_logger(__name__)
    # logger.warning("DATABASE_URL не встановлено або має некоректне значення. Перевірте змінні середовища або .env файл.")
    print("ПОПЕРЕДЖЕННЯ: DATABASE_URL не встановлено або має некоректне значення. Перевірте змінні середовища або .env файл.")

# Функція для перевірки з'єднання з БД
async def check_db_connection() -> bool:
    """
    Перевіряє з'єднання з базою даних, виконуючи простий запит.
    Повертає True при успішному з'єднанні, інакше False.
    """
    if not async_engine:
        logger.error("Перевірка з'єднання з БД неможлива: async_engine не ініціалізовано.")
        return False
    try:
        async with async_engine.connect() as connection:
            # Виконуємо простий запит, наприклад, SELECT 1
            # Для SQLAlchemy 2.0, text імпортується з sqlalchemy
            from sqlalchemy import text # type: ignore
            await connection.execute(text("SELECT 1"))
        logger.info("З'єднання з базою даних успішно перевірено.")
        return True
    except Exception as e:
        logger.error(f"Помилка підключення до бази даних під час перевірки: {e}", exc_info=True)
        return False

# Все виглядає добре для налаштування асинхронної роботи з БД.
# `get_db_session` - стандартна залежність для FastAPI.
# Важливо, що `commit` та `rollback` обробляються на рівні бізнес-логіки (сервіси/репозиторії),
# а не в самій залежності `get_db_session` (окрім rollback при винятках).
# `expire_on_commit=False` важливе для FastAPI.
# `autoflush=False` та `autocommit=False` - стандартні для SQLAlchemy.
# Обробка помилки створення `async_engine` та `AsyncSessionLocal` додана.
# Логування SQL запитів (`echo`) керується налаштуваннями.
# Пул з'єднань також налаштовується.
#
# Посилання на `Base` з `models.base` не потрібне тут, оскільки цей файл
# відповідає лише за налаштування підключення та сесій.
# `Base` використовується Alembic та при визначенні моделей.
#
# Все готово.
