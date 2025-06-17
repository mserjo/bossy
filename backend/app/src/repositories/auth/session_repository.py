# backend/app/src/repositories/auth/session_repository.py
"""
Репозиторій для моделі "Сесія Користувача" (UserSession).

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
# Абсолютний імпорт моделі UserSession та схеми UserSessionCreate
from backend.app.src.models.auth.session import UserSession
from backend.app.src.schemas.auth.session import UserSessionCreate
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Для UserSessionUpdateSchema, якщо оновлення не передбачено, можна використати PydanticBaseModel.
# Назва схеми оновлена для узгодженості, хоча вона залишається порожньою.
class UserSessionUpdateSchema(PydanticBaseModel):
    pass


class SessionRepository(BaseRepository[UserSession, UserSessionCreate, UserSessionUpdateSchema]):
    """
    Репозиторій для управління записами сесій користувачів (`UserSession`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи, специфічні для сесій.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `UserSession`.
        """
        super().__init__(model=UserSession)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_session_token(self, session: AsyncSession, session_token: str) -> Optional[UserSession]: # Renamed session_key to session_token
        """
        Отримує один запис сесії за її унікальним токеном.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            session_token (str): Токен сесії для пошуку.

        Returns:
            Optional[UserSession]: Екземпляр моделі `UserSession`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання UserSession за session_token: {session_token[:20]}...")
        stmt = select(self.model).where(self.model.session_token == session_token) # Changed from session_key to session_token
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні UserSession за session_token: {e}", exc_info=True)
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
            f"Видалення прострочених UserSession для user_id: {'всіх' if user_id is None else user_id}"
        )
        stmt = sqlalchemy_delete(self.model).where(self.model.expires_at < datetime.now(timezone.utc))
        if user_id is not None:
            stmt = stmt.where(self.model.user_id == user_id)

        try:
            async with session.begin_nested() if session.in_transaction() else session.begin():
                result = await session.execute(stmt)
            rowcount = result.rowcount
            logger.info(
                f"Видалено {rowcount} прострочених UserSession"
                f"{' для користувача ID ' + str(user_id) if user_id else ' для всіх користувачів'}."
            )
            return rowcount
        except Exception as e:
            logger.error(f"Помилка при видаленні прострочених UserSession: {e}", exc_info=True)
            # TODO: Розглянути підняття специфічного виключення
            return 0


if __name__ == "__main__":
    # Демонстраційний блок для SessionRepository.
    logger.info("--- Репозиторій Сесій Користувачів (SessionRepository) ---")

    logger.info("Для тестування SessionRepository потрібна асинхронна сесія SQLAlchemy.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {UserSession.__name__}.")
    logger.info(f"  Очікує схему створення: {UserSessionCreate.__name__}")
    logger.info(f"  Очікує схему оновлення: {UserSessionUpdateSchema.__name__} (зараз порожня)")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_session_token(session_token: str)") # Оновлено назву методу
    logger.info("  - remove_expired_sessions(user_id: Optional[int] = None)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
