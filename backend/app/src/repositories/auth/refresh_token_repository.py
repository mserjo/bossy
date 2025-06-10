# backend/app/src/repositories/auth/refresh_token_repository.py
"""
Репозиторій для моделі "Токен Оновлення" (RefreshToken).

Цей модуль визначає клас `RefreshTokenRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з токенами оновлення, такі як
отримання токена за його значенням та видалення прострочених токенів.
"""

from typing import Optional, Any
from datetime import datetime, timezone

from sqlalchemy import select, delete as sqlalchemy_delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel as PydanticBaseModel  # Для UpdateSchemaType, якщо не потрібна специфічна схема

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі RefreshToken та схеми RefreshTokenCreateSchema
from backend.app.src.models.auth.token import RefreshToken
from backend.app.src.schemas.auth.token import RefreshTokenCreateSchema


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

# Для RefreshTokenUpdateSchema, якщо оновлення не передбачено, можна використати PydanticBaseModel або Any.
# Або створити порожню схему оновлення, якщо BaseRepository цього вимагає.
class RefreshTokenUpdateSchema(PydanticBaseModel):  # Порожня схема, оскільки токени зазвичай не оновлюються
    pass


class RefreshTokenRepository(BaseRepository[RefreshToken, RefreshTokenCreateSchema, RefreshTokenUpdateSchema]):
    """
    Репозиторій для управління записами токенів оновлення (`RefreshToken`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи, специфічні для токенів оновлення.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `RefreshToken`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=RefreshToken)

    async def get_by_token(self, token_value: str) -> Optional[RefreshToken]:
        """
        Отримує один запис токена оновлення за його рядковим значенням.

        ВАЖЛИВО: Цей метод передбачає, що токени зберігаються у відкритому вигляді.
        У продакшен-середовищі токени слід хешувати перед збереженням,
        і цей метод має шукати за хешем токена.

        Args:
            token_value (str): Рядкове значення токена для пошуку.

        Returns:
            Optional[RefreshToken]: Екземпляр моделі `RefreshToken`, якщо знайдено, інакше None.
        """
        # TODO: Якщо токени хешуються в БД, тут потрібно хешувати token_value перед запитом.
        #       Наприклад: hashed_token = hash_function(token_value)
        #       stmt = select(self.model).where(self.model.token == hashed_token)
        stmt = select(self.model).where(self.model.token == token_value)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def remove_expired_tokens(self, user_id: Optional[int] = None) -> int:
        """
        Видаляє прострочені токени оновлення з бази даних.
        Може видаляти токени для конкретного користувача або всі прострочені токени.

        Args:
            user_id (Optional[int]): Якщо вказано, видаляє прострочені токени лише
                                     для цього користувача. Інакше – для всіх користувачів.

        Returns:
            int: Кількість видалених токенів.
        """
        stmt = sqlalchemy_delete(self.model).where(self.model.expires_at < datetime.now(timezone.utc))
        if user_id is not None:
            stmt = stmt.where(self.model.user_id == user_id)

        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        # logger.info(f"Видалено {result.rowcount} прострочених токенів оновлення"
        #             f"{' для користувача ID ' + str(user_id) if user_id else ''}.")
        return result.rowcount


if __name__ == "__main__":
    # Демонстраційний блок для RefreshTokenRepository.
    print("--- Репозиторій Токенів Оновлення (RefreshTokenRepository) ---")

    print("Для тестування RefreshTokenRepository потрібна асинхронна сесія SQLAlchemy.")
    print(f"Він успадковує методи від BaseRepository для моделі {RefreshToken.__name__}.")
    print(f"  Очікує схему створення: {RefreshTokenCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {RefreshTokenUpdateSchema.__name__} (зараз порожня)")

    print("\nСпецифічні методи:")
    print("  - get_by_token(token_value: str)")
    print("  - remove_expired_tokens(user_id: Optional[int] = None)")

    print("\nВАЖЛИВО: Метод get_by_token потребує адаптації, якщо токени зберігаються хешованими.")
    print("Примітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")

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
    #         # print(f"Створено токен: {created_token}")
    #         #
    #         # expired_count = await repo.remove_expired_tokens()
    #         # print(f"Видалено прострочених токенів: {expired_count}")
    # import asyncio
    # asyncio.run(demo_refresh_token_repo())
