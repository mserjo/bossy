# backend/app/src/repositories/auth/session_repository.py
"""
Репозиторій для моделі "Сесія Користувача" (Session).

Цей модуль визначає клас `SessionRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з сесіями користувачів, такі як
отримання сесії за її ключем та видалення прострочених сесій.
"""

from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import select, delete as sqlalchemy_delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel as PydanticBaseModel  # Для UpdateSchemaType, якщо не потрібна специфічна схема

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі Session та схеми SessionCreateSchema
from backend.app.src.models.auth.session import Session
from backend.app.src.schemas.auth.session import SessionCreateSchema
from backend.app.src.config import logging # Імпорт logging з конфігурації
# Отримання логера для цього модуля
logger = logging.getLogger(__name__)

# Для SessionUpdateSchema, якщо оновлення не передбачено, можна використати PydanticBaseModel.
class SessionUpdateSchema(PydanticBaseModel):  # Порожня схема, оскільки сесії зазвичай не оновлюються таким чином
    pass


class SessionRepository(BaseRepository[Session, SessionCreateSchema, SessionUpdateSchema]):
    """
    Репозиторій для управління записами сесій користувачів (`Session`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи, специфічні для сесій.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `Session`.
        """
        super().__init__(model=Session)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_session_key(self, session: AsyncSession, session_key: str) -> Optional[Session]:
        """
        Отримує один запис сесії за її унікальним ключем.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            session_key (str): Ключ сесії для пошуку.

        Returns:
            Optional[Session]: Екземпляр моделі `Session`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання Session за session_key: {session_key[:20]}...")
        stmt = select(self.model).where(self.model.session_key == session_key)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні Session за session_key: {e}", exc_info=True)
            return None

    async def remove_expired_sessions(self, session: AsyncSession, user_id: Optional[int] = None) -> int:
        """
        Видаляє прострочені сесії з бази даних.
        Може видаляти сесії для конкретного користувача або всі прострочені сесії.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (Optional[int]): Якщо вказано, видаляє прострочені сесії лише
                                     для цього користувача. Інакше – для всіх користувачів.

        Returns:
            int: Кількість видалених сесій.
        """
        logger.debug(
            f"Видалення прострочених Session для user_id: {'всіх' if user_id is None else user_id}"
        )
        stmt = sqlalchemy_delete(self.model).where(self.model.expires_at < datetime.now(timezone.utc))
        if user_id is not None:
            stmt = stmt.where(self.model.user_id == user_id)

        try:
            async with session.begin_nested() if session.in_transaction() else session.begin():
                result = await session.execute(stmt)
            rowcount = result.rowcount
            logger.info(
                f"Видалено {rowcount} прострочених сесій"
                f"{' для користувача ID ' + str(user_id) if user_id else ' для всіх користувачів'}."
            )
            return rowcount
        except Exception as e:
            logger.error(f"Помилка при видаленні прострочених Session: {e}", exc_info=True)
            # TODO: Розглянути підняття специфічного виключення
            return 0


if __name__ == "__main__":
    # Демонстраційний блок для SessionRepository.
    logger.info("--- Репозиторій Сесій Користувачів (SessionRepository) ---")

    logger.info("Для тестування SessionRepository потрібна асинхронна сесія SQLAlchemy.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {Session.__name__}.")
    logger.info(f"  Очікує схему створення: {SessionCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {SessionUpdateSchema.__name__} (зараз порожня)")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_session_key(session_key: str)")
    logger.info("  - remove_expired_sessions(user_id: Optional[int] = None)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
