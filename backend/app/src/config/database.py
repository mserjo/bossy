from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import AsyncGenerator

from backend.app.src.config.settings import settings

# --- Налаштування SQLAlchemy Engine ---
# Engine є початковою точкою для будь-якої програми SQLAlchemy.
# Він налаштовується за допомогою URL бази даних з налаштувань програми.
# Ми використовуємо `create_async_engine` для сумісності з asyncio.
engine = create_async_engine(
    str(settings.DATABASE_URL),  # Переконайтеся, що DATABASE_URL є рядком
    pool_pre_ping=True,      # Тестувати з'єднання перед їх видачею
    echo=settings.DEBUG,       # Логувати SQL-запити, якщо увімкнено режим DEBUG
    # Додаткове налаштування пулу можна зробити тут, якщо потрібно:
    # pool_size=10,            # Кількість з'єднань, які триматимуться відкритими в пулі з'єднань
    # max_overflow=20,         # Кількість з'єднань, які можна відкрити понад pool_size
    # pool_recycle=3600,       # Перезапускати з'єднання через 1 годину
    # pool_timeout=30,         # Час очікування для отримання з'єднання з пулу
)

# --- Фабрика сесій SQLAlchemy ---
# SessionLocal - це фабрика для створення нових сесій бази даних.
# AsyncSession використовується для асинхронних операцій з базою даних.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, # Уникає проблем з від'єднаними екземплярами після коміту в асинхронному коді
)

# --- Базовий клас для декларативних моделей ---
# Всі моделі SQLAlchemy успадковуватимуться від цього класу Base.
# Це дозволяє SQLAlchemy зіставляти класи Python з таблицями бази даних.
class Base(DeclarativeBase):
    pass

# --- Залежність для FastAPI для отримання сесії бази даних ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Залежність FastAPI, яка надає сесію бази даних для одного запиту.

    Ця функція є асинхронним генератором, який повертає AsyncSession.
    Вона гарантує, що сесія буде належним чином закрита після обробки запиту,
    навіть якщо виникне помилка.

    Yields:
        AsyncSession: Асинхронна сесія SQLAlchemy.
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit() # Застосувати будь-які зміни, зроблені під час запиту
        except Exception:
            await session.rollback() # Відкотити у разі помилки
            raise
        finally:
            await session.close() # Гарантувати, що сесія завжди закрита

# --- Опціонально: Функція для ініціалізації бази даних (створення таблиць) ---
# Зазвичай використовується для середовищ розробки або тестування.
# Для продакшену перевага надається міграціям (наприклад, Alembic).
async def create_db_and_tables():
    """
    Асинхронно створює всі таблиці бази даних, визначені моделями, що успадковують Base.
    У продакшн-середовищі це, як правило, має оброблятися міграціями.
    """
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Розкоментуйте, щоб спочатку видалити всі таблиці (використовуйте з обережністю)
        await conn.run_sync(Base.metadata.create_all)
    print("Таблиці бази даних створено (якщо вони не існували).")

if __name__ == "__main__":
    import asyncio

    async def main():
        print("Спроба створити таблиці бази даних...")
        await create_db_and_tables()
        print("Перевірка з'єднання з базою даних шляхом створення сесії...")
        try:
            async for db_session in get_db():
                print(f"Успішно отримано сесію БД: {db_session}")
                # Тут можна було б виконати простий запит, якби моделі були визначені, наприклад:
                # from sqlalchemy import text
                # result = await db_session.execute(text("SELECT 1"))
                # print(f"Результат тестового запиту: {result.scalar_one()}")
                break # Вийти після однієї сесії
            print("Сесію БД успішно отримано та закрито.")
        except Exception as e:
            print(f"Помилка під час перевірки сесії БД: {e}")

    asyncio.run(main())
