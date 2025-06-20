# backend/app/src/repositories/auth/refresh_token_repository.py
"""
Репозиторій для моделі "Токен Оновлення" (RefreshToken).

Цей модуль визначає клас `RefreshTokenRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з токенами оновлення, такі як
отримання токена за його значенням та видалення прострочених токенів.
"""

from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import select, delete as sqlalchemy_delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel as PydanticBaseModel  # Для UpdateSchemaType, якщо не потрібна специфічна схема

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі RefreshToken та схеми RefreshTokenCreateSchema
from backend.app.src.models.auth.token import RefreshToken
from backend.app.src.schemas.auth.token import RefreshTokenCreateSchema
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Для RefreshTokenUpdateSchema, якщо оновлення не передбачено, можна використати PydanticBaseModel.
# Або створити порожню схему оновлення, якщо BaseRepository цього вимагає.
class RefreshTokenUpdateSchema(PydanticBaseModel):  # Порожня схема, оскільки токени зазвичай не оновлюються
    pass


class RefreshTokenRepository(BaseRepository[RefreshToken, RefreshTokenCreateSchema, RefreshTokenUpdateSchema]):
    """
    Репозиторій для управління записами токенів оновлення (`RefreshToken`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи, специфічні для токенів оновлення.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `RefreshToken`.
        """
        super().__init__(model=RefreshToken)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_token(self, session: AsyncSession, token_value: str) -> Optional[RefreshToken]:
        """
        Отримує один запис токена оновлення за його рядковим значенням.

        ВАЖЛИВО: Цей метод передбачає, що токени зберігаються у відкритому вигляді.
        У продакшен-середовищі токени слід хешувати перед збереженням,
        і цей метод має шукати за хешем токена.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            token_value (str): Рядкове значення токена для пошуку.

        Returns:
            Optional[RefreshToken]: Екземпляр моделі `RefreshToken`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання RefreshToken за значенням токена: {token_value[:20]}...") # Логуємо лише частину токена
        # TODO: Якщо токени хешуються в БД, тут потрібно хешувати token_value перед запитом.
        #       Наприклад: hashed_token = hash_function(token_value)
        #       stmt = select(self.model).where(self.model.token == hashed_token)
        stmt = select(self.model).where(self.model.token == token_value)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні RefreshToken за токеном: {e}", exc_info=True)
            return None


    async def remove_expired_tokens(self, session: AsyncSession, user_id: Optional[int] = None) -> int:
        """
        Видаляє прострочені токени оновлення з бази даних.
        Може видаляти токени для конкретного користувача або всі прострочені токени.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (Optional[int]): Якщо вказано, видаляє прострочені токени лише
                                     для цього користувача. Інакше – для всіх користувачів.

        Returns:
            int: Кількість видалених токенів.
        """
        logger.debug(
            f"Видалення прострочених RefreshToken для user_id: {'всіх' if user_id is None else user_id}"
        )
        stmt = sqlalchemy_delete(self.model).where(self.model.expires_at < datetime.now(timezone.utc))
        if user_id is not None:
            stmt = stmt.where(self.model.user_id == user_id)

        try:
            async with session.begin_nested() if session.in_transaction() else session.begin():
                result = await session.execute(stmt)
                # await session.commit() # Commit керується контекстним менеджером або зовнішньою транзакцією
            rowcount = result.rowcount
            logger.info(
                f"Видалено {rowcount} прострочених токенів оновлення"
                f"{' для користувача ID ' + str(user_id) if user_id else ' для всіх користувачів'}."
            )
            return rowcount
        except Exception as e:
            logger.error(f"Помилка при видаленні прострочених RefreshToken: {e}", exc_info=True)
            # TODO: Розглянути підняття специфічного виключення
            return 0


if __name__ == "__main__":
    # Демонстраційний блок для RefreshTokenRepository.
    logger.info("--- Репозиторій Токенів Оновлення (RefreshTokenRepository) ---")

    logger.info("Для тестування RefreshTokenRepository потрібна асинхронна сесія SQLAlchemy.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {RefreshToken.__name__}.")
    logger.info(f"  Очікує схему створення: {RefreshTokenCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {RefreshTokenUpdateSchema.__name__} (зараз порожня)")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_token(token_value: str)")
    logger.info("  - remove_expired_tokens(user_id: Optional[int] = None)")

    logger.info("\nВАЖЛИВО: Метод get_by_token потребує адаптації, якщо токени зберігаються хешованими.")
    logger.info("Примітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")

    # Концептуальний приклад використання (потребує макетів або реальної сесії)
    # async def demo_refresh_token_repo():
    #     from backend.app.src.config.database import SessionLocal # Для прикладу
    #     async with SessionLocal() as session:
    #         repo = RefreshTokenRepository(session)
    #         # ... тут могли б бути виклики методів ...
    #         # Наприклад, створення токена (потребує User):
    #         # from datetime import timedelta
    #         # new_token_data = RefreshTokenCreateSchema(user_id=1, token="testrefreshtoken", expires_at=datetime.now(timezone.utc) + timedelta(days=7))
    #         # created_token = await repo.create(new_token_data)
    #         # logger.info(f"Створено токен: {created_token}")
    #         #
    #         # expired_count = await repo.remove_expired_tokens()
    #         # logger.info(f"Видалено прострочених токенів: {expired_count}")
    # import asyncio
    # asyncio.run(demo_refresh_token_repo())
