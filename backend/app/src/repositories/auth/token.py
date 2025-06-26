# backend/app/src/repositories/auth/token.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `RefreshTokenModel`.
Надає методи для створення, отримання, оновлення (відкликання) та видалення
refresh токенів в базі даних.
"""

from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy import select, update, delete # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.auth.token import RefreshTokenModel
from backend.app.src.schemas.auth.token import RefreshTokenSchema # Використовуємо для типізації, хоча CRUD не через схеми
from backend.app.src.repositories.base import BaseRepository

# Для refresh токенів схеми Create/Update можуть бути не потрібні в BaseRepository,
# оскільки створення/оновлення токенів має специфічну логіку.
# Тому можемо не передавати CreateSchemaType, UpdateSchemaType, або передати BaseModel.
from pydantic import BaseModel as PydanticBaseModel

class RefreshTokenRepository(BaseRepository[RefreshTokenModel, PydanticBaseModel, PydanticBaseModel]): # Використовуємо PydanticBaseModel як заглушки
    """
    Репозиторій для роботи з refresh токенами (`RefreshTokenModel`).
    """

    async def get_by_hashed_token(self, db: AsyncSession, *, hashed_token: str) -> Optional[RefreshTokenModel]:
        """
        Отримує refresh токен за його захешованим значенням.

        :param db: Асинхронна сесія бази даних.
        :param hashed_token: Захешований токен для пошуку.
        :return: Об'єкт RefreshTokenModel або None, якщо токен не знайдено.
        """
        statement = select(self.model).where(self.model.hashed_token == hashed_token)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_all_for_user(self, db: AsyncSession, *, user_id: uuid.UUID) -> List[RefreshTokenModel]:
        """
        Отримує всі активні (не відкликані та не прострочені) refresh токени для користувача.

        :param db: Асинхронна сесія бази даних.
        :param user_id: Ідентифікатор користувача.
        :return: Список об'єктів RefreshTokenModel.
        """
        statement = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_revoked == False, # SQLAlchemy порівнює з False, а не is False
            self.model.expires_at > datetime.utcnow() # Або func.now() для часу БД
        )
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def create_refresh_token(
        self, db: AsyncSession, *,
        user_id: uuid.UUID,
        hashed_token: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None # Приймаємо IP як рядок
    ) -> RefreshTokenModel:
        """
        Створює новий запис refresh токена в базі даних.

        :param db: Асинхронна сесія бази даних.
        :param user_id: ID користувача.
        :param hashed_token: Захешований токен.
        :param expires_at: Час закінчення дії токена.
        :param user_agent: User-Agent клієнта.
        :param ip_address: IP-адреса клієнта.
        :return: Створений об'єкт RefreshTokenModel.
        """
        db_obj = self.model(
            user_id=user_id,
            hashed_token=hashed_token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
            is_revoked=False # Новий токен не відкликаний
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def revoke_token(self, db: AsyncSession, *, token_obj: RefreshTokenModel, reason: Optional[str] = None) -> RefreshTokenModel:
        """
        Відкликає вказаний refresh токен.

        :param db: Асинхронна сесія бази даних.
        :param token_obj: Об'єкт RefreshTokenModel для відкликання.
        :param reason: Причина відкликання (опціонально).
        :return: Оновлений об'єкт RefreshTokenModel.
        """
        token_obj.is_revoked = True
        token_obj.revoked_at = datetime.utcnow() # Або func.now()
        if reason:
            token_obj.revocation_reason = reason

        db.add(token_obj)
        await db.commit()
        await db.refresh(token_obj)
        return token_obj

    async def revoke_all_tokens_for_user(self, db: AsyncSession, *, user_id: uuid.UUID, reason: Optional[str] = "user_logout_all_sessions") -> int:
        """
        Відкликає всі активні refresh токени для вказаного користувача.
        Корисно для функції "вийти з усіх пристроїв".

        :param db: Асинхронна сесія бази даних.
        :param user_id: Ідентифікатор користувача.
        :param reason: Причина відкликання.
        :return: Кількість відкликаних токенів.
        """
        statement = (
            update(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.is_revoked == False,
                self.model.expires_at > datetime.utcnow()
            )
            .values(
                is_revoked=True,
                revoked_at=datetime.utcnow(),
                revocation_reason=reason
            )
        )
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore

    async def delete_expired_and_revoked_tokens(self, db: AsyncSession, *, before_date: Optional[datetime] = None) -> int:
        """
        Видаляє прострочені та давно відкликані refresh токени.
        Використовується для очищення бази даних.

        :param db: Асинхронна сесія бази даних.
        :param before_date: Якщо вказано, видаляє відкликані токени,
                            які були відкликані до цієї дати.
                            Якщо None, видаляє лише прострочені.
        :return: Кількість видалених токенів.
        """
        delete_conditions = [self.model.expires_at < datetime.utcnow()]
        if before_date:
            delete_conditions.append(
                (self.model.is_revoked == True) & (self.model.revoked_at < before_date) # type: ignore
            )

        # Складаємо умови через OR
        final_condition = delete_conditions[0]
        if len(delete_conditions) > 1:
            from sqlalchemy import or_ # type: ignore
            final_condition = or_(*delete_conditions)

        statement = delete(self.model).where(final_condition)
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore

    # Метод `get(id)` з BaseRepository може використовуватися для отримання токена за його ID (jti).
    # Метод `delete(id)` з BaseRepository може використовуватися для видалення конкретного токена за ID.

refresh_token_repository = RefreshTokenRepository(RefreshTokenModel)

# TODO: Узгодити використання `datetime.utcnow()` та `func.now()` від SQLAlchemy.
#       `func.now()` генерує час на стороні БД, що може бути кращим для консистентності.
#       `datetime.utcnow()` генерує час на стороні додатку.
#       Для полів типу `expires_at`, `revoked_at` це може мати значення.
#       Поки що залишено `datetime.utcnow()`, але варто розглянути `func.now()`.
# TODO: Перевірити типи для `ip_address` (INET в моделі, str в схемі/параметрах).
#       SQLAlchemy зазвичай обробляє це коректно, але варто пам'ятати.
#       В `create_refresh_token` ip_address приймається як `str`.
#
# Все виглядає добре. Репозиторій надає необхідні методи для управління refresh токенами.
# Використання `PydanticBaseModel` як заглушок для Create/Update схем в Generic-типі
# `BaseRepository` є прийнятним, оскільки цей репозиторій має власні методи
# для створення (`create_refresh_token`) та оновлення (`revoke_token`),
# які не покладаються на стандартні `obj_in` схеми.
