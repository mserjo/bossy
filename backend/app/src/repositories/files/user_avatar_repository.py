# backend/app/src/repositories/files/user_avatar_repository.py
"""
Репозиторій для моделі "Аватар Користувача" (UserAvatar).

Цей модуль визначає клас `UserAvatarRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з аватарами користувачів,
зокрема для встановлення активного аватара.
"""

from typing import List, Optional, Tuple, Any
from datetime import datetime, timezone

from sqlalchemy import select, update as sqlalchemy_update
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.files.avatar import UserAvatar
from backend.app.src.schemas.files.avatar import UserAvatarCreateSchema, UserAvatarUpdateSchema  # UserAvatarUpdateSchema може бути простою
from backend.app.src.config import logger # Використання спільного логера


class UserAvatarRepository(BaseRepository[UserAvatar, UserAvatarCreateSchema, UserAvatarUpdateSchema]):
    """
    Репозиторій для управління аватарами користувачів (`UserAvatar`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    методи для отримання аватара користувача та встановлення активного аватара.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `UserAvatar`.
        """
        super().__init__(model=UserAvatar)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_user_id(self, session: AsyncSession, user_id: int) -> Optional[UserAvatar]:
        """
        Отримує запис UserAvatar для вказаного користувача.
        Оскільки user_id є унікальним, повертає один запис або None.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.

        Returns:
            Optional[UserAvatar]: Екземпляр моделі `UserAvatar`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання UserAvatar для user_id: {user_id}")
        stmt = select(self.model).where(self.model.user_id == user_id)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні UserAvatar для user_id {user_id}: {e}", exc_info=True)
            return None

    async def get_active_avatar_for_user(self, session: AsyncSession, user_id: int) -> Optional[UserAvatar]:
        """
        Отримує активний аватар для вказаного користувача.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.

        Returns:
            Optional[UserAvatar]: Екземпляр моделі `UserAvatar`, що є активним, або None.
        """
        logger.debug(f"Отримання активного UserAvatar для user_id: {user_id}")
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_active == True
        )
        # Додатково можна завантажити file_record: .options(selectinload(self.model.file_record))
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні активного UserAvatar для user_id {user_id}: {e}", exc_info=True)
            return None

    async def set_active_avatar(
            self, session: AsyncSession, user_id: int, file_record_id: int
    ) -> Optional[UserAvatar]:
        """
        Встановлює новий активний аватар для користувача.
        Якщо існує попередній активний аватар для цього користувача, він деактивується.
        Якщо запис UserAvatar для цієї пари user_id/file_record_id вже існує,
        він активується. В іншому випадку створюється новий запис.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            file_record_id (int): ID запису файлу (`FileRecord`), який стає новим аватаром.

        Returns:
            Optional[UserAvatar]: Актуальний (створений або оновлений) екземпляр `UserAvatar`, або None у разі помилки.
        """
        logger.debug(f"Встановлення активного аватара file_record_id {file_record_id} для user_id {user_id}")
        try:
            async with session.begin_nested() if session.in_transaction() else session.begin():
                # 1. Деактивувати всі поточні активні аватари для цього користувача
                update_stmt = (
                    sqlalchemy_update(self.model)
                    .where(self.model.user_id == user_id, self.model.is_active == True)
                    .values(is_active=False, updated_at=datetime.now(timezone.utc))
                    .execution_options(synchronize_session=False)
                )
                await session.execute(update_stmt)

                # 2. Перевірити, чи існує запис UserAvatar для цієї пари user_id/file_record_id
                existing_avatar_stmt = select(self.model).where(
                    self.model.user_id == user_id,
                    self.model.file_record_id == file_record_id
                )
                existing_avatar_result = await session.execute(existing_avatar_stmt)
                db_obj = existing_avatar_result.scalar_one_or_none()

                if db_obj:
                    # Якщо запис існує, активуємо його
                    db_obj.is_active = True
                    # updated_at має оновитися через TimestampedMixin
                    session.add(db_obj)
                else:
                    # Якщо запис не існує, створюємо новий
                    create_schema = UserAvatarCreateSchema(
                        user_id=user_id,
                        file_record_id=file_record_id,
                        is_active=True
                    )
                    db_obj = self.model(**create_schema.model_dump())
                    session.add(db_obj)

                # `flush` потрібен, щоб отримати ID (якщо новий об'єкт) або для перевірки обмежень.
                await session.flush()
                # `refresh` оновлює `db_obj` даними з бази даних.
                await session.refresh(db_obj)

            logger.info(f"Встановлено активний аватар file_record_id {file_record_id} для користувача ID {user_id}.")
            return db_obj
        except Exception as e:
            logger.error(
                f"Помилка при встановленні активного аватара для user_id {user_id}: {e}",
                exc_info=True
            )
            # TODO: Розглянути підняття специфічного виключення
        return db_obj


if __name__ == "__main__":
    # Демонстраційний блок для UserAvatarRepository.
    logger.info("--- Репозиторій Аватарів Користувачів (UserAvatarRepository) ---")

    logger.info("Для тестування UserAvatarRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {UserAvatar.__name__}.")
    logger.info(f"  Очікує схему створення: {UserAvatarCreateSchema.__name__}")
    logger.info(
        f"  Очікує схему оновлення: {UserAvatarUpdateSchema.__name__} (може бути простою, оскільки оновлюється переважно is_active)")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_user_id(user_id: int) -> Optional[UserAvatar]")
    logger.info("  - get_active_avatar_for_user(user_id: int) -> Optional[UserAvatar]")
    logger.info("  - set_active_avatar(user_id: int, file_record_id: int) -> UserAvatar")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
