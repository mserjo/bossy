# backend/app/src/services/auth/session.py
# -*- coding: utf-8 -*-
"""
Сервіс для управління сесіями користувачів.

Надає функціонал для створення, отримання, валідації та інвалідації
користувацьких сесій (використовуючи модель UserSession та схему UserSessionResponse),
а також для очищення прострочених сесій.
"""
from typing import List, Optional # Type видалено
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Оновлено імпорт
from sqlalchemy.orm import selectinload

# Виправлені повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.auth.session import UserSession  # Модель SQLAlchemy для сесії користувача
from backend.app.src.models.auth.user import User  # Модель SQLAlchemy для користувача
from backend.app.src.schemas.auth.session import UserSessionResponse, UserSessionCreate # Імпорт актуальних схем

from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)
from backend.app.src.config import settings  # Для доступу до конфігурацій, наприклад DEFAULT_SESSION_DURATION_DAYS

# Тривалість сесії за замовчуванням береться з налаштувань.
# DEFAULT_SESSION_DURATION_DAYS = 30  # Дні - видалено, використовуємо settings


class UserSessionService(BaseService):
    """
    Сервіс для управління сесіями користувачів, якщо використовується механізм сесій зі збереженням стану.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізація сервісу сесій користувачів.

        :param db_session: Асинхронна сесія бази даних.
        """
        super().__init__(db_session)
        logger.info("UserSessionService ініціалізовано.")

    async def create_session(
            self,
            user_id: int,
            user_agent: Optional[str] = None,
            ip_address: Optional[str] = None,
            duration_days: Optional[int] = None
    ) -> UserSessionResponse:
        """
        Створює нову сесію користувача та зберігає її в базі даних.

        :param user_id: ID користувача (int), для якого створюється сесія.
        :param user_agent: Рядок User-Agent клієнта.
        :param ip_address: IP-адреса клієнта.
        :param duration_days: Тривалість сесії в днях. Якщо None, використовується DEFAULT_SESSION_DURATION_DAYS.
        :return: Об'єкт UserSessionResponse (Pydantic схема) для створеної сесії.
        :raises ValueError: Якщо користувача не знайдено. # i18n
        """
        logger.debug(f"Створення нової сесії для користувача ID: {user_id}...")

        user = await self.db_session.get(User, user_id)
        if not user:
            logger.error(f"Користувача з ID '{user_id}' не знайдено. Неможливо створити сесію.")
            raise ValueError(f"Користувача з ID '{user_id}' не знайдено.")  # i18n # type: ignore

        session_duration_days_to_use = duration_days if duration_days is not None else settings.DEFAULT_SESSION_DURATION_DAYS
        session_token_uuid = uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(days=session_duration_days_to_use)

        new_session_db = UserSession(
            session_token=str(session_token_uuid), # Зберігаємо UUID як рядок
            user_id=user_id,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            last_active_at=datetime.now(timezone.utc)
            # Додаткові поля для UserSession не вимагаються згідно з поточним technical_task.txt.
        )

        self.db_session.add(new_session_db)
        await self.commit()
        await self.db_session.refresh(new_session_db)

        logger.info(
            f"Сесію успішно створено для користувача ID '{user_id}' з токеном сесії (UUID): {new_session_db.session_token}")
        return UserSessionResponse.model_validate(new_session_db)

    async def get_session_by_token(self, session_token: UUID) -> Optional[UserSessionResponse]:
        """
        Отримує сесію користувача за її токеном.
        Перевіряє термін дії та валідність. Оновлює `last_active_at`.
        Видаляє сесію, якщо вона прострочена.

        :param session_token: Токен сесії (UUID).
        :return: Об'єкт UserSessionResponse, якщо знайдено та валідний, інакше None.
        """
        logger.debug(f"Спроба отримання сесії за токеном (UUID): {session_token}")

        stmt = select(UserSession).options(selectinload(UserSession.user)).where(
            UserSession.session_token == str(session_token) # Порівнюємо з рядковим представленням UUID
        )
        session_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if not session_db:
            logger.warning(f"Сесію з токеном (UUID) '{session_token}' не знайдено.")
            return None

        if session_db.expires_at < datetime.now(timezone.utc):
            logger.info(
                f"Термін дії токена сесії '{session_token}' для користувача ID '{session_db.user_id}' закінчився {session_db.expires_at.isoformat()}. Видалення.")
            await self.db_session.delete(session_db)
            await self.commit()
            # API шар, що викликає цей сервіс, має обробити повернення None і повідомити клієнта про прострочену сесію.
            return None

        session_db.last_active_at = datetime.now(timezone.utc)
        self.db_session.add(session_db)
        await self.commit()

        logger.info(
            f"Токен сесії (UUID) '{session_token}' валідовано для користувача ID '{session_db.user_id}'. Поле 'last_active_at' оновлено.")
        return UserSessionResponse.model_validate(session_db)

    async def invalidate_session(self, session_token: UUID, user_id: Optional[int] = None) -> bool:
        """
        Інвалідує/видаляє конкретну сесію користувача за її токеном.
        Якщо надано user_id, переконується, що сесія належить цьому користувачеві.

        :param session_token: Токен сесії (UUID) для інвалідації.
        :param user_id: Опціональний ID користувача (int), для перевірки належності сесії.
        :return: True, якщо сесію знайдено та інвалідовано, інакше False.
        """
        logger.debug(f"Спроба інвалідації токена сесії (UUID): {session_token} для користувача ID: {user_id or 'будь-який'}")

        stmt = select(UserSession).where(UserSession.session_token == str(session_token)) # Порівняння з рядком
        if user_id:
            stmt = stmt.where(UserSession.user_id == user_id)

        session_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if not session_db:
            logger.warning(
                f"Токен сесії (UUID) '{session_token}' не знайдено або не належить користувачеві '{user_id}'. Неможливо інвалідувати.")
            return False

        await self.db_session.delete(session_db)
        await self.commit()
        logger.info(
            f"Токен сесії (UUID) '{session_token}' для користувача ID '{session_db.user_id}' успішно інвалідовано (видалено).")
        return True

    async def list_user_sessions(self, user_id: int, skip: int = 0, limit: int = 100) -> List[UserSessionResponse]:
        """
        Перелічує всі активні (не прострочені) сесії для даного користувача.
        Сортування за `last_active_at` у спадаючому порядку.

        :param user_id: ID користувача (int).
        :param skip: Кількість сесій для пропуску (пагінація).
        :param limit: Максимальна кількість сесій для повернення.
        :return: Список об'єктів UserSessionResponse (Pydantic схеми) активних сесій.
        """
        logger.debug(f"Перелік активних сесій для користувача ID: {user_id}, пропустити={skip}, ліміт={limit}")

        now = datetime.now(timezone.utc)
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.expires_at > now
        ).order_by(UserSession.last_active_at.desc()).offset(skip).limit(limit)
        # Критерії сортування (last_active_at desc) та фільтрації (тільки активні) відповідають technical_task.txt.

        sessions_db = (await self.db_session.execute(stmt)).scalars().all()

        response_list = [UserSessionResponse.model_validate(s) for s in sessions_db]
        logger.info(f"Отримано {len(response_list)} активних сесій (UserSessionResponse) для користувача ID '{user_id}'.")
        return response_list

    async def invalidate_all_user_sessions(self, user_id: int, exclude_session_token: Optional[UUID] = None) -> int:
        """
        Інвалідує/видаляє всі сесії для даного користувача, опціонально виключаючи один токен сесії.
        Корисно для функції "вийти з усіх інших пристроїв".

        :param user_id: ID користувача (int), чиї сесії потрібно інвалідувати.
        :param exclude_session_token: Токен сесії (UUID), який потрібно залишити активним.
        :return: Кількість інвалідованих сесій.
        """
        logger.info(f"Інвалідація всіх сесій для користувача ID: {user_id}, виключаючи токен (UUID): {exclude_session_token}")

        stmt_select = select(UserSession.id).where(UserSession.user_id == user_id)
        if exclude_session_token:
            stmt_select = stmt_select.where(UserSession.session_token != str(exclude_session_token)) # Порівняння з рядком

        ids_to_delete_result = await self.db_session.execute(stmt_select)
        ids_to_delete = [row[0] for row in ids_to_delete_result.fetchall()]

        if not ids_to_delete:
            logger.info(
                f"Не знайдено сесій для інвалідації для користувача ID '{user_id}' (виключаючи: {exclude_session_token}).")
            return 0

        delete_stmt = UserSession.__table__.delete().where(UserSession.id.in_(ids_to_delete))
        await self.db_session.execute(delete_stmt)
        await self.commit()

        count = len(ids_to_delete)
        logger.info(f"Успішно інвалідовано {count} сесій для користувача ID '{user_id}'.")
        return count

    async def cleanup_expired_sessions(self) -> int:
        """
        Видаляє всі прострочені сесії з бази даних.
        Це завдання для обслуговування, може виконуватися періодично фоновим процесом.

        :return: Кількість видалених прострочених сесій.
        """
        logger.info("Очищення прострочених сесій користувачів...")
        now = datetime.now(timezone.utc)

        select_expired_stmt = select(UserSession.id).where(UserSession.expires_at < now)
        expired_ids_result = await self.db_session.execute(select_expired_stmt)
        expired_ids = [row[0] for row in expired_ids_result.fetchall()]

        count = 0
        if expired_ids:
            delete_stmt = UserSession.__table__.delete().where(UserSession.id.in_(expired_ids))
            await self.db_session.execute(delete_stmt)
            await self.commit()
            count = len(expired_ids)
            logger.info(f"Успішно очищено {count} прострочених сесій користувачів.")
        else:
            logger.info("Не знайдено прострочених сесій користувачів для очищення.")
        return count


logger.debug("UserSessionService клас визначено та завантажено.")
