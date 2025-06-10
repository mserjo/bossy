"""
Репозиторій для моделі "Сесія Користувача" (Session).

Цей модуль визначає клас `SessionRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з сесіями користувачів, такі як
отримання сесії за її ключем та видалення прострочених сесій.
"""

from typing import Optional, Any
from datetime import datetime, timezone

from sqlalchemy import select, delete as sqlalchemy_delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel as PydanticBaseModel  # Для UpdateSchemaType, якщо не потрібна специфічна схема

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі Session та схеми SessionCreateSchema
from backend.app.src.models.auth.session import Session
from backend.app.src.schemas.auth.session import SessionCreateSchema


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

# Для SessionUpdateSchema, якщо оновлення не передбачено, можна використати PydanticBaseModel або Any.
class SessionUpdateSchema(PydanticBaseModel):  # Порожня схема, оскільки сесії зазвичай не оновлюються таким чином
    pass


class SessionRepository(BaseRepository[Session, SessionCreateSchema, SessionUpdateSchema]):
    """
    Репозиторій для управління записами сесій користувачів (`Session`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи, специфічні для сесій.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `Session`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=Session)

    async def get_by_session_key(self, session_key: str) -> Optional[Session]:
        """
        Отримує один запис сесії за її унікальним ключем.

        Args:
            session_key (str): Ключ сесії для пошуку.

        Returns:
            Optional[Session]: Екземпляр моделі `Session`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(self.model.session_key == session_key)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def remove_expired_sessions(self, user_id: Optional[int] = None) -> int:
        """
        Видаляє прострочені сесії з бази даних.
        Може видаляти сесії для конкретного користувача або всі прострочені сесії.

        Args:
            user_id (Optional[int]): Якщо вказано, видаляє прострочені сесії лише
                                     для цього користувача. Інакше – для всіх користувачів.

        Returns:
            int: Кількість видалених сесій.
        """
        stmt = sqlalchemy_delete(self.model).where(self.model.expires_at < datetime.now(timezone.utc))
        if user_id is not None:
            stmt = stmt.where(self.model.user_id == user_id)

        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        # logger.info(f"Видалено {result.rowcount} прострочених сесій"
        #             f"{' для користувача ID ' + str(user_id) if user_id else ''}.")
        return result.rowcount


if __name__ == "__main__":
    # Демонстраційний блок для SessionRepository.
    print("--- Репозиторій Сесій Користувачів (SessionRepository) ---")

    print("Для тестування SessionRepository потрібна асинхронна сесія SQLAlchemy.")
    print(f"Він успадковує методи від BaseRepository для моделі {Session.__name__}.")
    print(f"  Очікує схему створення: {SessionCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {SessionUpdateSchema.__name__} (зараз порожня)")

    print("\nСпецифічні методи:")
    print("  - get_by_session_key(session_key: str)")
    print("  - remove_expired_sessions(user_id: Optional[int] = None)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
