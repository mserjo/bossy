# backend/app/src/services/auth/auth_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `AuthService` для обробки логіки автентифікації,
включаючи реєстрацію, вхід, управління токенами та сесіями, відновлення паролю.
"""

from typing import Optional, Tuple, Any
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.auth.login import LoginRequestSchema
from backend.app.src.schemas.auth.user import UserCreateSchema, UserSchema # UserSchema може бути не потрібна тут
from backend.app.src.schemas.auth.token import TokenResponseSchema, TokenPayloadSchema # TokenPayloadSchema може бути для внутрішнього використання
from backend.app.src.schemas.auth.password import PasswordResetRequestSchema, PasswordResetConfirmSchema # Для відновлення паролю
from backend.app.src.repositories.auth.user import UserRepository # Виправлено шлях
from backend.app.src.repositories.auth.token import RefreshTokenRepository # Виправлено шлях
from backend.app.src.repositories.auth.session import SessionRepository # Виправлено шлях
from backend.app.src.services.auth.user_service import UserService
from backend.app.src.services.auth.token_service import TokenService # Для генерації різних типів токенів
# from backend.app.src.services.notifications.email_service import EmailService # Для відправки email
from backend.app.src.config.security import verify_password # create_access_token, create_refresh_token_pair - не використовуються напряму тут
from backend.app.src.core.exceptions import UnauthorizedException, BadRequestException, NotFoundException
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import logger
from backend.app.src.core.constants import STATUS_ACTIVE_CODE, USER_TYPE_SUPERADMIN # Для перевірки статусу

class AuthService:
    """
    Сервіс для обробки автентифікації.
    """
    def __init__(
        self,
        db_session: AsyncSession, # Сервіс тепер приймає сесію
    ):
        self.db = db_session
        self.user_repository = UserRepository(db_session)
        self.refresh_token_repository = RefreshTokenRepository(db_session)
        self.session_repository = SessionRepository(db_session)
        self.user_service = UserService(db_session)
        self.token_service = TokenService(db_session) # Для генерації та валідації різних токенів
        # self.email_service = EmailService() # Для відправки email

    async def register_user(self, *, obj_in: UserCreateSchema) -> UserModel:
        # Перевірка на існування користувача з таким email
        existing_user = await self.user_repository.get_by_email(email=obj_in.email)
        if existing_user:
            logger.warning(f"Спроба реєстрації з існуючим email: {obj_in.email}")
            raise BadRequestException(detail="Користувач з таким email вже існує.")
        # TODO: Додати перевірку на унікальність username, якщо він використовується і є унікальним.

        user = await self.user_service.create_user(obj_in=obj_in) # UserService вже хешує пароль

        # TODO: Відправка email для підтвердження реєстрації
        # verification_token = await self.token_service.generate_email_verification_token(user.email)
        # await self.email_service.send_email_verification_message(user.email, user.name or user.username, verification_token)
        # logger.info(f"Лист для підтвердження email надіслано на {user.email}")

        return user

    async def login(
        self, *, login_data: LoginRequestSchema,
        user_agent: Optional[str], ip_address: Optional[str]
    ) -> TokenResponseSchema:
        user = await self.user_repository.get_by_identifier(identifier=login_data.identifier)

        if not user:
            logger.warning(f"Невдала спроба входу для ідентифікатора: {login_data.identifier} (користувача не знайдено).")
            raise UnauthorizedException(detail="Неправильний ідентифікатор або пароль.")

        if not verify_password(login_data.password, user.hashed_password):
            # TODO: Реалізувати логіку блокування акаунту після N невдалих спроб
            logger.warning(f"Невдала спроба входу для користувача {user.email} (неправильний пароль).")
            raise UnauthorizedException(detail="Неправильний ідентифікатор або пароль.")

        if user.is_deleted:
            logger.warning(f"Спроба входу для видаленого користувача: {user.email}.")
            raise UnauthorizedException(detail="Обліковий запис видалено.")

        if not user.is_active: # Перевірка загальної активності
             logger.warning(f"Спроба входу для неактивного користувача: {user.email} (загальний статус is_active=False).")
             raise UnauthorizedException(detail="Обліковий запис неактивний. Зверніться до адміністратора.")

        # TODO: Додати перевірку статусу з довідника `user.state_id` на відповідність `STATUS_ACTIVE_CODE`
        # if user.state and user.state.code != STATUS_ACTIVE_CODE:
        #     logger.warning(f"Спроба входу для користувача {user.email} зі статусом '{user.state.code}'.")
        #     raise UnauthorizedException(detail=f"Обліковий запис має статус '{user.state.name}'. Вхід заборонено.")

        # TODO: Перевірка, чи не заблокований акаунт (user.locked_until)

        # TODO: Скидання лічильника невдалих спроб при успішному вході

        access_token, refresh_token_str, _, _ = await self.token_service.generate_and_store_refresh_token(
            user_id=user.id,
            user_type_code=user.user_type_code, # Для включення в access token
            user_agent=user_agent,
            ip_address=ip_address
        )

        # Оновлюємо час останнього входу для користувача
        # Це краще робити в транзакції разом зі створенням токена/сесії
        await self.user_repository.update_last_login(user_id=user.id)
        logger.info(f"Користувач {user.email} успішно увійшов до системи.")

        return TokenResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def refresh_access_token(
        self, *, refresh_token_str_from_client: str,
        user_agent: Optional[str], ip_address: Optional[str]
    ) -> TokenResponseSchema:

        validated_user_id, old_token_id = await self.token_service.validate_refresh_token_str_and_get_user_id(
            token_str=refresh_token_str_from_client
        )

        user = await self.user_repository.get(id=validated_user_id)
        if not user or not user.is_active or user.is_deleted:
            logger.warning(f"Спроба оновити токен для неіснуючого, неактивного або видаленого користувача ID: {validated_user_id}")
            raise UnauthorizedException(detail="Користувача не знайдено або обліковий запис неактивний.")

        # Ротація токенів: відкликаємо старий, генеруємо нову пару
        await self.token_service.revoke_refresh_token_by_id(token_id=old_token_id, reason="token_rotation")

        new_access_token, new_refresh_token_str, _, _ = await self.token_service.generate_and_store_refresh_token(
            user_id=user.id,
            user_type_code=user.user_type_code,
            user_agent=user_agent,
            ip_address=ip_address
        )

        logger.info(f"Токени успішно оновлено для користувача {user.email}.")
        return TokenResponseSchema(
            access_token=new_access_token,
            refresh_token=new_refresh_token_str,
            token_type="bearer",
            expires_in=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def logout(self, *, refresh_token_str: str) -> None:
        try:
            validated_user_id, token_id_to_revoke = await self.token_service.validate_refresh_token_str_and_get_user_id(
                token_str=refresh_token_str,
                check_if_revoked=False # Дозволяємо відкликати навіть вже відкликаний (для ідемпотентності)
            )
            if token_id_to_revoke:
                await self.token_service.revoke_refresh_token_by_id(token_id=token_id_to_revoke, reason="user_logout")
                logger.info(f"Refresh токен ID {token_id_to_revoke} для користувача ID {validated_user_id} відкликано при виході.")
                # Також можна деактивувати пов'язану сесію, якщо є
                # await self.session_repository.deactivate_session_by_refresh_token_id(db, refresh_token_id=token_id_to_revoke)
        except UnauthorizedException:
            logger.warning(f"Спроба виходу з недійсним або вже відкликаним refresh токеном: {refresh_token_str[:20]}...")
            # Не кидаємо помилку, просто логуємо, вихід має бути "тихим"
        except Exception as e:
            logger.error(f"Помилка під час виходу з системи (відкликання токена): {e}", exc_info=True)


    async def request_password_reset(self, *, email: str) -> None:
        """Ініціює процес скидання пароля."""
        logger.info(f"Запит на скидання пароля для email: {email}")
        user = await self.user_repository.get_by_email(email=email)
        if user and user.is_active and not user.is_deleted:
            password_reset_token = await self.token_service.generate_password_reset_token(email=user.email)
            # TODO: Реалізувати відправку email з цим токеном
            # await self.email_service.send_password_reset_email(
            #     to_email=user.email,
            #     username=user.name or user.username or user.email,
            #     reset_token=password_reset_token,
            #     token_lifetime_minutes=settings.security.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
            # )
            logger.info(f"Згенеровано токен скидання пароля для {email} (реальна відправка email - TODO).")
        else:
            logger.info(f"Запит на скидання пароля для неіснуючого або неактивного email: {email}. Відповідь не надсилається.")
        # Завжди повертаємо успішний результат, щоб не розкривати існування email

    async def confirm_password_reset(self, *, token: str, new_password: str) -> bool:
        """Підтверджує скидання пароля та встановлює новий пароль."""
        logger.info(f"Спроба підтвердити скидання пароля за допомогою токена: {token[:10]}...")
        email = await self.token_service.verify_password_reset_token(token=token)
        if not email:
            logger.warning("Спроба скинути пароль з недійсним або простроченим токеном.")
            raise BadRequestException(detail="Недійсний або прострочений токен скидання пароля.")

        user = await self.user_repository.get_by_email(email=email)
        if not user or not user.is_active or user.is_deleted:
            logger.error(f"Користувача {email} не знайдено або він неактивний під час підтвердження скидання пароля.")
            raise NotFoundException(detail="Користувача не знайдено або обліковий запис неактивний.")

        await self.user_service.reset_user_password(user=user, new_password=new_password)
        await self.token_service.revoke_password_reset_token(token=token) # Інвалідуємо токен після використання
        logger.info(f"Пароль для користувача {email} успішно скинуто.")
        return True

    async def verify_email(self, *, token: str) -> bool:
        """Підтверджує email користувача."""
        logger.info(f"Спроба підтвердити email за допомогою токена: {token[:10]}...")
        email = await self.token_service.verify_email_verification_token(token=token)
        if not email:
            logger.warning("Спроба підтвердити email з недійсним або простроченим токеном.")
            raise BadRequestException(detail="Недійсний або прострочений токен підтвердження email.")

        user = await self.user_repository.get_by_email(email=email)
        if not user:
            logger.error(f"Користувача {email} не знайдено під час підтвердження email.")
            # Це малоймовірно, якщо токен валідний
            raise NotFoundException(detail="Користувача не знайдено.")

        if user.is_email_verified:
            logger.info(f"Email {email} вже підтверджено.")
            return True # Вже підтверджено

        updated_user = await self.user_service.mark_email_as_verified(user=user)
        logger.info(f"Email {email} для користувача {user.id} успішно підтверджено.")
        return updated_user.is_email_verified


# Екземпляр сервісу не створюємо тут глобально. Він буде створюватися там, де потрібен, з передачею сесії.
