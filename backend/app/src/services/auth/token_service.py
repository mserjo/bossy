# backend/app/src/services/auth/token_service.py
# -*- coding: utf-8 -*-
"""
Сервіс для управління JWT токенами (access, refresh) та іншими типами токенів
(наприклад, для підтвердження email, скидання пароля).
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any

from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.config.settings import settings
from backend.app.src.config.logging import logger
from backend.app.src.core.security import (
    ALGORITHM, create_access_token_raw, create_refresh_token_pair,
    get_password_hash, verify_password # verify_password тут для перевірки секретної частини refresh токена
)
from backend.app.src.models.auth.token import RefreshTokenModel
from backend.app.src.repositories.auth.token_repository import RefreshTokenRepository
from backend.app.src.repositories.auth.user_repository import UserRepository # Для отримання користувача
from backend.app.src.core.exceptions import UnauthorizedException, InternalServerError, InvalidTokenException

class TokenService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.refresh_token_repo = RefreshTokenRepository(db_session)
        self.user_repo = UserRepository(db_session) # Може знадобитися для перевірки користувача

    async def generate_access_token(self, user_id: uuid.UUID, user_type_code: str) -> str:
        """Генерує JWT access token."""
        expires_delta = timedelta(minutes=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES)
        token_data = {"sub": str(user_id), "user_type": user_type_code, "scope": "access_token"}
        return create_access_token_raw(data=token_data, expires_delta=expires_delta)

    async def generate_refresh_token_pair_and_store(
        self, user_id: uuid.UUID, user_agent: Optional[str], ip_address: Optional[str]
    ) -> Tuple[str, str, uuid.UUID, datetime]: # refresh_token_str, hashed_refresh_token_payload, jti, expires_at
        """
        Генерує пару refresh токенів (рядок для клієнта та хеш для БД), зберігає хеш.
        Повертає рядок токена для клієнта, хешовану секретну частину, JTI (ID токена в БД) та час закінчення.
        """
        refresh_token_str, hashed_secret_payload, jti_str = create_refresh_token_pair()
        jti = uuid.UUID(jti_str) # Конвертуємо рядок JTI в UUID для ID моделі
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.security.REFRESH_TOKEN_EXPIRE_DAYS)

        await self.refresh_token_repo.create_refresh_token(
            user_id=user_id,
            id=jti, # Використовуємо згенерований JTI як ID
            hashed_token_payload=hashed_secret_payload, # Зберігаємо хеш секретної частини
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address
        )
        return refresh_token_str, hashed_secret_payload, jti, expires_at

    async def generate_and_store_refresh_token(
        self, user_id: uuid.UUID, user_type_code: str, # user_type_code для access_token
        user_agent: Optional[str], ip_address: Optional[str]
    ) -> Tuple[str, str, uuid.UUID, datetime]: # access_token, refresh_token_str, jti, refresh_expires_at
        """
        Комплексний метод: генерує access token та пару refresh токенів, зберігає refresh токен.
        """
        access_token = await self.generate_access_token(user_id=user_id, user_type_code=user_type_code)
        refresh_token_str, _, jti, refresh_expires_at = await self.generate_refresh_token_pair_and_store(
            user_id=user_id, user_agent=user_agent, ip_address=ip_address
        )
        return access_token, refresh_token_str, jti, refresh_expires_at


    async def validate_refresh_token_str_and_get_user_id(
        self, token_str: str, check_if_revoked: bool = True
    ) -> Tuple[uuid.UUID, uuid.UUID]: # user_id, token_id (jti)
        """
        Валідує рядок refresh токена, отриманий від клієнта.
        Формат токена: "jti.secret_payload".
        Повертає user_id та token_id (jti), якщо токен валідний.
        Кидає UnauthorizedException, якщо невалідний.
        """
        try:
            jti_str, secret_payload = token_str.split(".", 1)
            token_id = uuid.UUID(jti_str)
        except (ValueError, AttributeError):
            logger.warning(f"Невалідний формат refresh токена при валідації: {token_str[:20]}...")
            raise InvalidTokenException(detail="Невалідний формат refresh токена.")

        token_db = await self.refresh_token_repo.get_with_user(id=token_id)

        if not token_db:
            logger.warning(f"Refresh токен з ID {token_id} не знайдено в БД.")
            raise InvalidTokenException(detail="Refresh токен не знайдено або недійсний.")

        if not verify_password(secret_payload, token_db.hashed_token_payload):
            logger.warning(f"Невідповідність секретної частини refresh токена ID {token_id}.")
            # TODO: Розглянути логіку безпеки: відкликати всі токени цього користувача
            # await self.revoke_all_user_refresh_tokens(token_db.user_id, exclude_token_id=None)
            raise InvalidTokenException(detail="Refresh токен недійсний (невідповідність).")

        if check_if_revoked and token_db.is_revoked:
            logger.warning(f"Спроба використання відкликаного refresh токена ID {token_id} для користувача {token_db.user_id}.")
            # TODO: Відкликати всі токени цього користувача
            # await self.revoke_all_user_refresh_tokens(token_db.user_id, exclude_token_id=None)
            raise InvalidTokenException(detail="Refresh токен відкликано.")

        if token_db.expires_at < datetime.now(timezone.utc):
            logger.warning(f"Термін дії refresh токена ID {token_id} закінчився ({token_db.expires_at}).")
            # Можна також відкликати його тут, якщо він ще не відкликаний
            if not token_db.is_revoked:
                 await self.revoke_refresh_token_by_id(token_id, "expired")
            raise InvalidTokenException(detail="Термін дії refresh токена закінчився.")

        if not token_db.user or not token_db.user.is_active or token_db.user.is_deleted:
            logger.warning(f"Користувач для refresh токена ID {token_id} неактивний, видалений або не існує.")
            raise InvalidTokenException(detail="Користувач, пов'язаний з токеном, неактивний.")

        # Оновлення last_used_at для токена
        await self.refresh_token_repo.update_last_used(token_id=token_id)

        return token_db.user_id, token_db.id


    async def revoke_refresh_token_by_id(self, token_id: uuid.UUID, reason: Optional[str] = None) -> bool:
        """Відкликає refresh токен за його ID."""
        token_db = await self.refresh_token_repo.get(id=token_id)
        if token_db and not token_db.is_revoked:
            await self.refresh_token_repo.revoke_token(token_obj=token_db, reason=reason)
            logger.info(f"Refresh токен ID {token_id} відкликано. Причина: {reason or 'не вказано'}.")
            # Також деактивувати пов'язану сесію, якщо є
            # if token_db.session_info: # Потрібно завантажити session_info
            #     await SessionRepository(self.db).deactivate_session(session_obj=token_db.session_info)
            return True
        elif token_db and token_db.is_revoked:
            logger.info(f"Refresh токен ID {token_id} вже був відкликаний.")
            return True # Вже відкликаний, вважаємо успіхом
        logger.warning(f"Спроба відкликати неіснуючий refresh токен ID {token_id}.")
        return False

    async def revoke_all_user_refresh_tokens(self, user_id: uuid.UUID, exclude_token_id: Optional[uuid.UUID] = None) -> int:
        """Відкликає всі активні refresh токени для користувача, крім вказаного."""
        count = await self.refresh_token_repo.revoke_all_for_user(user_id=user_id, exclude_token_id=exclude_token_id)
        logger.info(f"Відкликано {count} refresh токенів для користувача ID {user_id}"
                    f"{f' (крім {exclude_token_id})' if exclude_token_id else ''}.")
        return count

    async def _generate_one_time_token(self, email: str, expires_delta: timedelta, token_type: str, extra_claims: Optional[Dict[str, Any]] = None) -> str:
        """Генерує загальний одноразовий токен (для email верифікації, скидання пароля)."""
        to_encode = {"sub": email, "type": token_type}
        if extra_claims:
            to_encode.update(extra_claims)
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode["exp"] = expire
        encoded_jwt = jwt.encode(to_encode, settings.security.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def _verify_one_time_token(self, token: str, expected_type: str) -> Optional[str]:
        """Валідує загальний одноразовий токен та повертає email (sub)."""
        try:
            payload = jwt.decode(token, settings.security.SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != expected_type:
                logger.warning(f"Невірний тип одноразового токена: очікувався '{expected_type}', отримано '{payload.get('type')}'.")
                return None
            email: Optional[str] = payload.get("sub")
            # Перевірка терміну дії вже вбудована в jwt.decode
            return email
        except JWTError as e:
            logger.warning(f"Помилка валідації одноразового токена ({expected_type}): {e}")
            return None

    async def generate_email_verification_token(self, email: str) -> str:
        delta = timedelta(hours=settings.security.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
        return await self._generate_one_time_token(email, delta, "email_verification")

    async def verify_email_verification_token(self, token: str) -> Optional[str]:
        return await self._verify_one_time_token(token, "email_verification")

    async def generate_password_reset_token(self, email: str) -> str:
        delta = timedelta(minutes=settings.security.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        return await self._generate_one_time_token(email, delta, "password_reset")

    async def verify_password_reset_token(self, token: str) -> Optional[str]:
        email = await self._verify_one_time_token(token, "password_reset")
        # TODO: Додатково перевірити, чи токен не був вже використаний (зберігати використані токени в "чорному списку" або БД)
        return email

    async def revoke_password_reset_token(self, token: str) -> None:
        """Інвалідує токен скидання пароля (додає до чорного списку)."""
        # TODO: Реалізувати механізм чорного списку для одноразових токенів (наприклад, в Redis з TTL).
        logger.info(f"Токен скидання пароля '{token[:10]}...' інвалідовано (TODO: реалізувати чорний список).")
        pass
