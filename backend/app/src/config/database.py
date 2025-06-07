from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import AsyncGenerator

from backend.app.src.config.settings import settings

# --- SQLAlchemy Engine Setup ---
# The engine is the starting point for any SQLAlchemy application.
# It's configured with the database URL from the application settings.
# We use `create_async_engine` for compatibility with asyncio.
engine = create_async_engine(
    str(settings.DATABASE_URL),  # Ensure DATABASE_URL is a string
    pool_pre_ping=True,      # Test connections before handing them out
    echo=settings.DEBUG,       # Log SQL queries if in DEBUG mode
    # Further pool customization can be done here if needed:
    # pool_size=10,            # Number of connections to keep open in the connection pool
    # max_overflow=20,         # Number of connections that can be opened beyond pool_size
    # pool_recycle=3600,       # Recycle connections after 1 hour
    # pool_timeout=30,         # Timeout for getting a connection from the pool
)

# --- SQLAlchemy Session Factory ---
# SessionLocal is a factory for creating new database sessions.
# An AsyncSession is used for asynchronous database operations.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, # Avoids issues with detached instances after commit in async code
)

# --- Base Class for Declarative Models ---
# All SQLAlchemy models will inherit from this Base class.
# It allows SQLAlchemy to map Python classes to database tables.
class Base(DeclarativeBase):
    pass

# --- Dependency for FastAPI to Get Database Session ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session for a single request.

    This function is an asynchronous generator that yields an AsyncSession.
    It ensures that the session is properly closed after the request is handled,
    even if an error occurs.

    Yields:
        AsyncSession: An asynchronous SQLAlchemy session.
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit() # Commit any changes made during the request
        except Exception:
            await session.rollback() # Rollback in case of an error
            raise
        finally:
            await session.close() # Ensure the session is always closed

# --- Optional: Function to Initialize Database (Create Tables) ---
# This is typically used for development or testing setups.
# For production, migrations (e.g., Alembic) are preferred.
async def create_db_and_tables():
    """
    Asynchronously creates all database tables defined by models inheriting from Base.
    This should generally be handled by migrations in a production environment.
    """
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Uncomment to drop all tables first (use with caution)
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created (if they didn't exist).")

if __name__ == "__main__":
    import asyncio

    async def main():
        print("Attempting to create database tables...")
        await create_db_and_tables()
        print("Verifying database connection by creating a session...")
        try:
            async for db_session in get_db():
                print(f"Successfully obtained DB session: {db_session}")
                # You could perform a simple query here if models were defined, e.g.:
                # from sqlalchemy import text
                # result = await db_session.execute(text("SELECT 1"))
                # print(f"Test query result: {result.scalar_one()}")
                break # Exit after one session
            print("DB session obtained and closed successfully.")
        except Exception as e:
            print(f"Error during DB session verification: {e}")

    asyncio.run(main())
