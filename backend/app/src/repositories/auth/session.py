# backend/app/src/repositories/auth/session.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `SessionModel`.
Надає методи для створення, отримання, оновлення та видалення
записів про сесії користувачів в базі даних.
"""

from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy import select, update, delete # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.auth.session import SessionModel
# Схеми для сесій зазвичай не використовуються для Create/Update через API,
# але можуть бути корисні для типізації.
from backend.app.src.schemas.auth.session import SessionSchema # Для типізації повернень, якщо потрібно
from backend.app.src.repositories.base import BaseRepository
from pydantic import BaseModel as PydanticBaseModel # Заглушка для Create/Update схем

class SessionRepository(BaseRepository[SessionModel, PydanticBaseModel, PydanticBaseModel]):
    """
    Репозиторій для роботи з сесіями користувачів (`SessionModel`).
    """

    async def get_by_refresh_token_id(self, db: AsyncSession, *, refresh_token_id: uuid.UUID) -> Optional[SessionModel]:
        """
        Отримує сесію за ID пов'язаного refresh токена.

        :param db: Асинхронна сесія бази даних.
        :param refresh_token_id: Ідентифікатор refresh токена.
        :return: Об'єкт SessionModel або None, якщо сесію не знайдено.
        """
        statement = select(self.model).where(self.model.refresh_token_id == refresh_token_id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_all_active_for_user(self, db: AsyncSession, *, user_id: uuid.UUID) -> List[SessionModel]:
        """
        Отримує всі активні сесії для вказаного користувача.

        :param db: Асинхронна сесія бази даних.
        :param user_id: Ідентифікатор користувача.
        :return: Список об'єктів SessionModel.
        """
        statement = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_active == True,
            (self.model.expires_at > datetime.utcnow()) | (self.model.expires_at == None) # Або func.now()
        ).order_by(self.model.last_activity_at.desc()) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def create_session(
        self, db: AsyncSession, *,
        user_id: uuid.UUID,
        user_agent: Optional[str],
        ip_address: Optional[str], # Приймаємо IP як рядок
        refresh_token_id: Optional[uuid.UUID] = None,
        expires_at: Optional[datetime] = None
    ) -> SessionModel:
        """
        Створює новий запис сесії в базі даних.

        :param db: Асинхронна сесія бази даних.
        :param user_id: ID користувача.
        :param user_agent: User-Agent клієнта.
        :param ip_address: IP-адреса клієнта.
        :param refresh_token_id: ID пов'язаного refresh токена (опціонально).
        :param expires_at: Час закінчення дії сесії (опціонально).
        :return: Створений об'єкт SessionModel.
        """
        db_obj = self.model(
            user_id=user_id,
            refresh_token_id=refresh_token_id,
            user_agent=user_agent,
            ip_address=ip_address,
            last_activity_at=datetime.utcnow(), # Або func.now()
            expires_at=expires_at,
            is_active=True
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def deactivate_session(self, db: AsyncSession, *, session_obj: SessionModel) -> SessionModel:
        """
        Деактивує вказану сесію.

        :param db: Асинхронна сесія бази даних.
        :param session_obj: Об'єкт SessionModel для деактивації.
        :return: Оновлений об'єкт SessionModel.
        """
        session_obj.is_active = False
        session_obj.expires_at = datetime.utcnow() # Можна також встановити час закінчення як поточний
        db.add(session_obj)
        await db.commit()
        await db.refresh(session_obj)
        return session_obj

    async def update_last_activity(self, db: AsyncSession, *, session_obj: SessionModel) -> SessionModel:
        """
        Оновлює час останньої активності для сесії.
        """
        session_obj.last_activity_at = datetime.utcnow()
        db.add(session_obj)
        await db.commit()
        await db.refresh(session_obj)
        return session_obj

    async def delete_expired_and_inactive_sessions(self, db: AsyncSession, *, older_than_days: Optional[int] = None) -> int:
        """
        Видаляє прострочені та давно неактивні сесії.

        :param db: Асинхронна сесія бази даних.
        :param older_than_days: Якщо вказано, видаляє неактивні сесії,
                                які були оновлені раніше, ніж ця кількість днів тому.
                                Якщо None, видаляє лише прострочені (`expires_at`).
        :return: Кількість видалених сесій.
        """
        conditions = [self.model.expires_at < datetime.utcnow()] # Прострочені

        if older_than_days is not None:
            from datetime import timedelta
            threshold_date = datetime.utcnow() - timedelta(days=older_than_days)
            conditions.append(
                (self.model.is_active == False) & (self.model.updated_at < threshold_date) # type: ignore
            )

        final_condition = conditions[0]
        if len(conditions) > 1:
            from sqlalchemy import or_ # type: ignore
            final_condition = or_(*conditions)

        statement = delete(self.model).where(final_condition)
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore

session_repository = SessionRepository(SessionModel)

# TODO: Узгодити використання `datetime.utcnow()` та `func.now()`.
# TODO: Розглянути логіку для `expires_at` сесії. Чи має воно бути жорстко
#       пов'язане з `expires_at` відповідного refresh токена, чи може бути незалежним?
#       Якщо пов'язане, то `SessionModel.expires_at` може оновлюватися при оновленні токена.
#
# Все виглядає добре. Репозиторій надає необхідні методи для управління сесіями.
# Як і для RefreshTokenRepository, Create/Update схеми тут менш релевантні для
# прямого використання через API, тому PydanticBaseModel використовується як заглушка.
# Сесії створюються/оновлюються логікою автентифікації.
