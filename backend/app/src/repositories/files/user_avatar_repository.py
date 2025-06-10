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
from backend.app.src.schemas.files.avatar import UserAvatarCreateSchema, \
    UserAvatarUpdateSchema  # UserAvatarUpdateSchema може бути простою


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class UserAvatarRepository(BaseRepository[UserAvatar, UserAvatarCreateSchema, UserAvatarUpdateSchema]):
    """
    Репозиторій для управління аватарами користувачів (`UserAvatar`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    методи для отримання аватара користувача та встановлення активного аватара.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `UserAvatar`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=UserAvatar)

    async def get_by_user_id(self, user_id: int) -> Optional[UserAvatar]:
        """
        Отримує запис UserAvatar для вказаного користувача.
        Оскільки user_id є унікальним, повертає один запис або None.

        Args:
            user_id (int): ID користувача.

        Returns:
            Optional[UserAvatar]: Екземпляр моделі `UserAvatar`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(self.model.user_id == user_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_avatar_for_user(self, user_id: int) -> Optional[UserAvatar]:
        """
        Отримує активний аватар для вказаного користувача.

        Args:
            user_id (int): ID користувача.

        Returns:
            Optional[UserAvatar]: Екземпляр моделі `UserAvatar`, що є активним, або None.
        """
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_active == True
        )
        # Додатково можна завантажити file_record: .options(selectinload(self.model.file_record))
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_active_avatar(self, user_id: int, file_record_id: int) -> UserAvatar:
        """
        Встановлює новий активний аватар для користувача.
        Якщо існує попередній активний аватар для цього користувача, він деактивується.
        Якщо запис UserAvatar для цієї пари user_id/file_record_id вже існує,
        він активується. В іншому випадку створюється новий запис.

        Args:
            user_id (int): ID користувача.
            file_record_id (int): ID запису файлу (`FileRecord`), який стає новим аватаром.

        Returns:
            UserAvatar: Актуальний (створений або оновлений) екземпляр `UserAvatar`.
        """
        # 1. Деактивувати всі поточні активні аватари для цього користувача
        #    (хоча за логікою моделі з unique=True на user_id, такий має бути лише один)
        update_stmt = (
            sqlalchemy_update(self.model)
            .where(self.model.user_id == user_id, self.model.is_active == True)
            .values(is_active=False, updated_at=datetime.now(timezone.utc))  # Оновлюємо updated_at вручну
            .execution_options(synchronize_session=False)
        # Не синхронізувати сесію, щоб уникнути конфліктів перед комітом
        )
        await self.db_session.execute(update_stmt)

        # 2. Перевірити, чи існує запис UserAvatar для цієї пари user_id/file_record_id
        existing_avatar_stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.file_record_id == file_record_id
        )
        existing_avatar_result = await self.db_session.execute(existing_avatar_stmt)
        db_obj = existing_avatar_result.scalar_one_or_none()

        if db_obj:
            # Якщо запис існує, активуємо його та оновлюємо час
            db_obj.is_active = True
            # `updated_at` з TimestampedMixin має оновитися автоматично при коміті,
            # але для явного контролю можна встановити тут, якщо onupdate не спрацює як очікувалось
            # для `add` існуючого об'єкта. Краще покладатися на onupdate=func.now() в моделі.
            # setattr(db_obj, "updated_at", datetime.now(timezone.utc)) # Для явного оновлення, якщо потрібно
            self.db_session.add(db_obj)
        else:
            # Якщо запис не існує, створюємо новий
            # Схема UserAvatarCreateSchema очікує user_id, file_record_id, is_active
            create_schema = UserAvatarCreateSchema(
                user_id=user_id,
                file_record_id=file_record_id,
                is_active=True
            )
            # Використовуємо метод create з BaseRepository, який вже робить add, commit, refresh
            # Однак, нам потрібен один commit в кінці, тому змінимо логіку.
            db_obj = self.model(**create_schema.model_dump())
            self.db_session.add(db_obj)

        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        # logger.info(f"Встановлено активний аватар ID {file_record_id} для користувача ID {user_id}.")
        return db_obj


if __name__ == "__main__":
    # Демонстраційний блок для UserAvatarRepository.
    print("--- Репозиторій Аватарів Користувачів (UserAvatarRepository) ---")

    print("Для тестування UserAvatarRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {UserAvatar.__name__}.")
    print(f"  Очікує схему створення: {UserAvatarCreateSchema.__name__}")
    print(
        f"  Очікує схему оновлення: {UserAvatarUpdateSchema.__name__} (може бути простою, оскільки оновлюється переважно is_active)")

    print("\nСпецифічні методи:")
    print("  - get_by_user_id(user_id: int) -> Optional[UserAvatar]")
    print("  - get_active_avatar_for_user(user_id: int) -> Optional[UserAvatar]")
    print("  - set_active_avatar(user_id: int, file_record_id: int) -> UserAvatar")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
