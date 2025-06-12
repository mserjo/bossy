# backend/app/src/services/auth/token.py
"""
Сервіс для управління JWT (access та refresh) токенами.

Відповідає за генерацію, валідацію токенів, а також за управління
записами refresh-токенів у базі даних, включаючи їх відкликання.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Type # Type не використовується явно, але може бути корисним
from uuid import UUID, uuid4

from jose import JWTError, jwt  # python-jose для обробки JWT
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Оновлено імпорт
from sqlalchemy.orm import selectinload

# Виправлені повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.config.settings import settings  # Доступ до секрету JWT, алгоритму, часу життя токенів
from backend.app.src.schemas.auth.token import TokenResponse  # Pydantic схема для відповіді з токенами
# TODO: (Залишено) Якщо RefreshTokenCreate та RefreshTokenResponse будуть використовуватися для сигнатур методів
#  цього сервісу, розкоментувати та перевірити їх використання. Наразі вони більше стосуються шару API.
# from backend.app.src.schemas.auth.token import RefreshTokenCreate, RefreshTokenResponse
from backend.app.src.models.auth.token import RefreshToken  # Модель SQLAlchemy для refresh-токенів
from backend.app.src.models.auth.user import User  # Модель SQLAlchemy для користувача
from backend.app.src.config import logger  # Використання спільного логера з конфігу


# from backend.app.src.core.exceptions import InvalidTokenTypeError # Має бути визначено в exceptions.py

# Тимчасове визначення кастомної помилки.
# TODO: [Exceptions] Перенести InvalidTokenTypeError до backend/app/src/core/exceptions.py
class InvalidTokenTypeError(ValueError):
    """Кастомна помилка для невірного типу токена."""
    pass


class TokenService(BaseService):
    """
    Сервіс для обробки JWT (access та refresh) токенів: генерація, валідація,
    та управління refresh-токенами, якщо вони зберігаються в базі даних.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("TokenService ініціалізовано.")

    def create_access_token(self,
                            subject: str,
                            expires_delta: Optional[timedelta] = None,
                            scopes: Optional[List[str]] = None,  # Фактично це дозволи (permissions)
                            additional_claims: Optional[Dict[str, Any]] = None
                            ) -> str:
        """
        Генерує новий JWT access-токен.

        :param subject: Суб'єкт токена (наприклад, user_id).
        :param expires_delta: Час життя токена. За замовчуванням ACCESS_TOKEN_EXPIRE_MINUTES.
        :param scopes: Список дозволів (permissions) для токена.
        :param additional_claims: Будь-які інші користувацькі заяви для включення в токен.
        :return: Закодований JWT access-токен.
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode: Dict[str, Any] = {
            "exp": expire,
            "sub": str(subject),
            "type": "access"
        }
        if scopes:
            # Згідно technical_task.txt, назва поля для дозволів - "permissions"
            to_encode["permissions"] = scopes
        if additional_claims:
            to_encode.update(additional_claims)

        jti_claim = str(uuid4())
        to_encode["jti"] = jti_claim

        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        logger.info(
            f"Access-токен створено для суб'єкта '{subject}' з JTI '{jti_claim}'. Термін дії: {expire.isoformat()}")
        return encoded_jwt

    async def create_refresh_token(
            self,
            user_id: UUID,
            expires_delta: Optional[timedelta] = None,
            device_info: Optional[str] = None,
            ip_address: Optional[str] = None  # Додано згідно technical_task.txt
    ) -> str:  # Повертає JTI як рядок
        """
        Генерує новий refresh-токен та зберігає його запис у базі даних.

        :param user_id: ID користувача.
        :param expires_delta: Час життя refresh-токена.
        :param device_info: Інформація про пристрій.
        :param ip_address: IP-адреса, з якої видано токен.
        :return: Рядок JTI refresh-токена.
        :raises ValueError: Якщо користувача не знайдено. # i18n
        """
        if expires_delta:
            expire_at = datetime.now(timezone.utc) + expires_delta
        else:
            expire_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        jti = uuid4()

        user_db = await self.db_session.get(User, user_id)
        if not user_db:
            logger.error(f"Користувача з ID '{user_id}' не знайдено. Неможливо створити refresh-токен.")
            raise ValueError(f"Користувача з ID '{user_id}' не знайдено.")  # i18n

        refresh_token_db = RefreshToken(
            jti=jti,
            user_id=user_id,
            expires_at=expire_at,
            is_revoked=False,
            device_info=device_info,
            ip_address=ip_address  # Додано поле
            # `created_at` та `revoked_at` обробляються моделлю або при відповідних діях.
        )

        self.db_session.add(refresh_token_db)
        await self.commit()

        logger.info(
            f"Refresh-токен (JTI: {jti}) створено для користувача ID '{user_id}'. IP: {ip_address}. Термін дії: {expire_at.isoformat()}")
        return str(jti)

    async def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Валідує access-токен.

        :param token: JWT access-токен для валідації.
        :return: Декодований пейлоад токена, якщо валідний, інакше None.
        :raises InvalidTokenTypeError: Якщо тип токена не 'access'.
        """
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

            if payload.get("type") != "access":
                jti = payload.get("jti")
                logger.warning(
                    f"Надано невірний тип токена ('{payload.get('type')}') для валідації access-токена. JTI: {jti}")
                raise InvalidTokenTypeError(f"Невірний тип токена. Очікувався 'access'. JTI: {jti}")  # i18n

            if "sub" not in payload or "jti" not in payload:
                logger.warning(f"Access-токен не містить обов'язкових полів 'sub' або 'jti'. JTI: {payload.get('jti')}")
                return None  # Або кинути іншу кастомну помилку

            # TODO: Реалізувати перевірку токена у дені-листі Redis згідно `technical_task.txt`.
            #  Потрібні методи: `await self.is_jti_denylisted(jti)` та `await self.add_jti_to_denylist(jti, expires_at)`.
            #  Ця функціональність потребує інтеграції з Redis.
            # jti = payload.get("jti")
            # if jti and await self.is_jti_denylisted(jti):
            #     logger.warning(f"Access-токен JTI '{jti}' знаходиться у дені-листі (був відкликаний).")
            #     return None # Або кинути помилку "токен відкликано"

            logger.info(f"Access-токен успішно валідовано. Суб'єкт: {payload.get('sub')}, JTI: {payload.get('jti')}")
            return payload
        except InvalidTokenTypeError:  # Перехоплення для ре-рейзу, щоб не потрапити в загальний JWTError
            raise
        except JWTError as e:
            logger.warning(f"Валідація access-токена не вдалася: {e}", exc_info=settings.DEBUG)
            return None

    async def process_refresh_token(self, refresh_token_jti_str: str) -> Optional[User]:
        """
        Обробляє refresh-токен. Якщо використовується вже відкликаний токен,
        всі активні refresh-токени для цього користувача будуть відкликані.
        """
        try:
            jti_uuid = UUID(refresh_token_jti_str)
        except ValueError:
            logger.warning(f"Невірний формат JTI для refresh-токена: {refresh_token_jti_str}")
            return None

        stmt = select(RefreshToken).options(selectinload(RefreshToken.user)).where(RefreshToken.jti == jti_uuid)
        token_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if not token_db:
            logger.warning(f"Refresh-токен JTI '{refresh_token_jti_str}' не знайдено в базі даних.")
            return None

        if token_db.is_revoked:
            logger.warning(
                f"Спроба використання вже відкликаного refresh-токена JTI '{refresh_token_jti_str}' користувачем ID '{token_db.user_id}'. "
                "Відкликання всіх refresh-токенів для цього користувача з міркувань безпеки.")
            await self.revoke_all_refresh_tokens_for_user(token_db.user_id)
            await self.commit()  # Переконайтеся, що відкликання всіх токенів закоммічено
            return None

        if token_db.expires_at < datetime.now(timezone.utc):
            logger.warning(
                f"Термін дії refresh-токена JTI '{refresh_token_jti_str}' закінчився {token_db.expires_at.isoformat()}.")
            return None

        token_db.is_revoked = True
        token_db.revoked_at = datetime.now(timezone.utc)
        self.db_session.add(token_db)
        await self.commit()

        logger.info(
            f"Refresh-токен JTI '{refresh_token_jti_str}' успішно оброблено для користувача ID '{token_db.user_id}'. Токен було відкликано.")
        return token_db.user

    async def revoke_refresh_token(self, refresh_token_jti_str: str, user_id: Optional[UUID] = None) -> bool:
        """Відкликає конкретний refresh-токен."""
        logger.debug(
            f"Спроба відкликання refresh-токена JTI: {refresh_token_jti_str} для користувача: {user_id if user_id else 'будь-який'}")
        try:
            jti_uuid = UUID(refresh_token_jti_str)
        except ValueError:
            logger.warning(f"Невірний формат JTI для відкликання: {refresh_token_jti_str}")
            return False

        stmt = select(RefreshToken).where(RefreshToken.jti == jti_uuid)
        if user_id:
            stmt = stmt.where(RefreshToken.user_id == user_id)

        token_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if not token_db:
            logger.warning(
                f"Refresh-токен JTI '{refresh_token_jti_str}' не знайдено або не належить користувачеві '{user_id}'.")
            return False

        if token_db.is_revoked:
            logger.info(f"Refresh-токен JTI '{refresh_token_jti_str}' вже було відкликано раніше.")
            return True

        token_db.is_revoked = True
        token_db.revoked_at = datetime.now(timezone.utc)
        self.db_session.add(token_db)
        await self.commit()
        logger.info(
            f"Refresh-токен JTI '{refresh_token_jti_str}' успішно відкликано для користувача ID '{token_db.user_id}'.")
        return True

    async def revoke_all_refresh_tokens_for_user(self, user_id: UUID, exclude_jti: Optional[UUID] = None) -> int:
        """Відкликає всі активні refresh-токени для даного користувача."""
        logger.info(
            f"Спроба відкликання всіх refresh-токенів для користувача ID: {user_id}, виключаючи JTI: {exclude_jti}")
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        )
        if exclude_jti:
            stmt = stmt.where(RefreshToken.jti != exclude_jti)

        tokens_to_revoke_db = (await self.db_session.execute(stmt)).scalars().all()

        if not tokens_to_revoke_db:
            logger.info(
                f"Не знайдено активних refresh-токенів для користувача ID '{user_id}' для відкликання (виключаючи: {exclude_jti}).")
            return 0

        revoked_at_time = datetime.now(timezone.utc)
        for token_db in tokens_to_revoke_db:
            token_db.is_revoked = True
            token_db.revoked_at = revoked_at_time
            self.db_session.add(token_db)

        # Важливо: commit тут не потрібен, якщо цей метод викликається з іншого методу,
        # який вже має свій commit. Якщо ж викликається самостійно, commit потрібен.
        # Для послідовності, якщо revoke_all_refresh_tokens_for_user викликається з process_refresh_token,
        # то commit в process_refresh_token покриє і ці зміни.
        # Однак, якщо цей метод може бути викликаний окремо (наприклад, адміністратором),
        # то він повинен мати власний commit. Поточна реалізація без власного commit.
        # Для безпеки, додам commit, якщо щось було змінено.
        if tokens_to_revoke_db:
            await self.commit()

        count = len(tokens_to_revoke_db)
        logger.info(f"Успішно відкликано {count} refresh-токенів для користувача ID '{user_id}'.")
        return count

    # TODO: (Залишено) Реалізація дені-листа для JWT access-токенів згідно `technical_task.txt`.
    #  Потребує інтеграції з Redis та визначення методів:
    #  - `async def add_jti_to_denylist(self, jti: str, expires_at: datetime) -> None:`
    #  - `async def is_jti_denylisted(self, jti: str) -> bool:`
    #  Ці методи будуть взаємодіяти з Redis для зберігання JTI відкликаних access-токенів
    #  до моменту їх природного закінчення терміну дії.


logger.debug("TokenService клас визначено та завантажено.")
