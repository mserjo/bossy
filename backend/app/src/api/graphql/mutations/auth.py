# backend/app/src/api/graphql/mutations/auth.py
# -*- coding: utf-8 -*-
"""
GraphQL мутації (Mutations), пов'язані з автентифікацією та управлінням акаунтом.
"""

import strawberry
from typing import Optional

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.user import (
    UserType, AuthPayload, UserRegisterInput, UserLoginInput,
    PasswordChangeInput, PasswordResetRequestInput, PasswordResetConfirmInput,
    UserAvatarUploadInput # Якщо завантаження аватара - це мутація тут
)
from backend.app.src.api.graphql.types.auth import TokenType # Потрібен для AuthPayload

from fastapi import HTTPException # Для обробки помилок сервісів

from backend.app.src.config.logging import logger
from backend.app.src.services.auth.user_service import UserService
from backend.app.src.services.auth.auth_service import AuthService # Використовуємо AuthService
from backend.app.src.services.auth.token_service import TokenService # Для скидання пароля
# from backend.app.src.services.notifications.notification_service import NotificationService # Для email
from backend.app.src.schemas.auth.user import UserCreateSchema # Для передачі в UserService
from backend.app.src.core.exceptions import BadRequestException, ForbiddenException, NotFoundException


@strawberry.type
class AuthMutations:
    """
    Клас, що групує GraphQL мутації для автентифікації, реєстрації та управління акаунтом.
    """

    @strawberry.mutation(description="Реєстрація нового користувача.")
    async def register_user(self, info: strawberry.Info, input: UserRegisterInput) -> AuthPayload: # Або інший тип відповіді
        """
        Реєструє нового користувача в системі.
        У разі успіху може повертати користувача та токени (авто-логін) або повідомлення про успіх.
        """
        # context = info.context
        # user_service = UserService(context.db_session)
        # token_service = TokenService(context.db_session) # Якщо потрібен авто-логін
        #
        # # Перевірка, чи користувач вже існує (user_service.get_user_by_email)
        # # Створення користувача (user_service.create_user)
        # # Генерація токенів (якщо авто-логін)
        # # Відправка email підтвердження (якщо потрібно)
        #
        # # Заглушка з авто-логіном
        # new_user_model = ... # Створений UserModel
        # access_token, refresh_token = await token_service.generate_user_tokens(new_user_model)
        # return AuthPayload(
        #     user=UserType.from_orm(new_user_model),
        #     token=TokenType(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
        # )
        # raise NotImplementedError("Реєстрація користувача ще не реалізована.") # Заглушка
        context = info.context
        db_session = context.db_session
        user_service = UserService(db_session)
        auth_service = AuthService(db_session) # Для створення токенів

        logger.info(f"GraphQL: Запит на реєстрацію нового користувача: {input.email}")

        try:
            # Перетворюємо GraphQL інпут на Pydantic схему для сервісу
            user_create_schema = UserCreateSchema(
                email=input.email,
                password=input.password,
                confirm_password=input.password, # Припускаємо, що UserRegisterInput не має confirm_password, або додаємо його
                name=input.username or input.email.split('@')[0], # Простий name, якщо username не надано
                username=input.username,
                first_name=input.first_name,
                last_name=input.last_name
                # user_type_code за замовчуванням "user" в схемі
            )
            # TODO: Якщо UserRegisterInput матиме confirm_password, передати його.
            # Поки що передаю password як confirm_password, щоб валідатор схеми не сварився,
            # але це не ідеально. Краще додати confirm_password в UserRegisterInput.

            new_user_model = await user_service.create_user(obj_in=user_create_schema)

            # Авто-логін після реєстрації
            access_token, refresh_token = await auth_service.create_jwt_tokens(user=new_user_model)

            logger.info(f"GraphQL: Користувач {new_user_model.email} успішно зареєстрований та автентифікований.")

            # TODO: Реалізувати відправку email підтвердження, якщо потрібно
            # notification_service = NotificationService(db_session)
            # await notification_service.send_registration_confirmation_email(new_user_model)

            return AuthPayload(
                user=UserType.from_orm(new_user_model), # Використовуємо from_orm для перетворення
                token=TokenType(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
            )
        except BadRequestException as e:
            logger.warning(f"GraphQL: Помилка реєстрації BadRequest - {e.detail}")
            raise HTTPException(status_code=400, detail=e.detail)
        except Exception as e:
            logger.error(f"GraphQL: Неочікувана помилка реєстрації - {str(e)}", exc_info=True)
            # Повертаємо більш загальну помилку для GraphQL клієнта
            raise Exception(f"Не вдалося зареєструвати користувача: {str(e)}")


    @strawberry.mutation(description="Автентифікація користувача та отримання JWT токенів.")
    async def login_user(self, info: strawberry.Info, input: UserLoginInput) -> AuthPayload:
        """
        Автентифікує користувача за email/username та паролем.
        Повертає дані користувача та пару JWT токенів (access та refresh).
        """
        # context = info.context
        # user_service = UserService(context.db_session)
        # token_service = TokenService(context.db_session)
        #
        # authenticated_user = await user_service.authenticate_user(email=input.email, password=input.password)
        # if not authenticated_user:
        #     raise Exception("Неправильний логін або пароль.")
        #
        # access_token, refresh_token = await token_service.generate_user_tokens(authenticated_user)
        # # Збереження refresh токена в БД/Redis
        #
        # return AuthPayload(
        #     user=UserType.from_orm(authenticated_user),
        #     token=TokenType(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
        # )
        # raise NotImplementedError("Логін користувача ще не реалізований.") # Заглушка
        context = info.context
        db_session = context.db_session
        auth_service = AuthService(db_session)

        logger.info(f"GraphQL: Запит на логін для користувача: {input.email}")

        try:
            # AuthService.authenticate_user повинен повертати UserModel або кидати виняток
            # Припускаємо, що UserLoginInput.email може бути email або username
            authenticated_user = await auth_service.authenticate_user(
                username_or_email=input.email, # Або input.username, якщо таке поле є в UserLoginInput
                password=input.password
            )
            if not authenticated_user: # Додаткова перевірка, хоча сервіс мав би кинути виняток
                raise BadRequestException("Неправильний логін або пароль.")

            access_token, refresh_token = await auth_service.create_jwt_tokens(user=authenticated_user)

            logger.info(f"GraphQL: Користувач {authenticated_user.email} успішно автентифікований.")

            return AuthPayload(
                user=UserType.from_orm(authenticated_user),
                token=TokenType(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
            )
        except BadRequestException as e: # Перехоплюємо помилки автентифікації
            logger.warning(f"GraphQL: Помилка логіну BadRequest - {e.detail}")
            # Для GraphQL краще кидати загальний Exception або спеціальний GraphQL error type
            raise Exception(e.detail) # Strawberry автоматично перетворить це на GraphQL помилку
        except Exception as e:
            logger.error(f"GraphQL: Неочікувана помилка логіну - {str(e)}", exc_info=True)
            raise Exception(f"Не вдалося увійти в систему: {str(e)}")

    @strawberry.mutation(description="Оновлення JWT access токена за допомогою refresh токена.")
    async def refresh_token(self, info: strawberry.Info, refresh_token_value: str) -> TokenType:
        """
        Приймає дійсний refresh токен та повертає нову пару JWT токенів.
        """
        # context = info.context
        # token_service = TokenService(context.db_session)
        # user_service = UserService(context.db_session) # Для отримання користувача
        #
        # # Валідація refresh токена, отримання user_id з нього
        # user_id = await token_service.validate_refresh_token(refresh_token_value)
        # if not user_id:
        #     raise Exception("Недійсний або прострочений refresh токен.")
        #
        # user = await user_service.get_user_by_id(user_id)
        # if not user or not user.is_active:
        #     raise Exception("Користувача не знайдено або він неактивний.")
        #
        # # Генерація нових токенів, інвалідація старого refresh токена (якщо потрібно)
        # new_access_token, new_refresh_token = await token_service.generate_user_tokens(user, old_refresh_token_to_revoke=refresh_token_value)
        #
        # return TokenType(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")
        # raise NotImplementedError("Оновлення токена ще не реалізовано.") # Заглушка
        context = info.context
        db_session = context.db_session
        auth_service = AuthService(db_session)

        logger.info(f"GraphQL: Запит на оновлення access token.")

        try:
            new_access_token, new_refresh_token, user_id = await auth_service.refresh_jwt_tokens(
                refresh_token_str=refresh_token_value
            )
            # user_id тут повертається з auth_service.refresh_jwt_tokens, можна використовувати для логування
            logger.info(f"GraphQL: Access token успішно оновлено для користувача ID {user_id}.")

            return TokenType(
                access_token=new_access_token,
                refresh_token=new_refresh_token, # Може бути None, якщо сервіс не повертає новий refresh
                token_type="bearer"
            )
        except HTTPException as e: # AuthService може кидати HTTPException (наприклад, 401 Unauthorized)
            logger.warning(f"GraphQL: Помилка оновлення access token - {e.detail}")
            raise Exception(e.detail) # Перетворюємо на загальний Exception для GraphQL
        except Exception as e:
            logger.error(f"GraphQL: Неочікувана помилка оновлення refresh token - {str(e)}", exc_info=True)
            raise Exception(f"Помилка сервера при оновленні токена: {str(e)}")


    @strawberry.mutation(description="Вихід користувача з системи (інвалідація refresh токена).")
    async def logout_user(self, info: strawberry.Info, refresh_token_value: Optional[str] = None) -> bool:
        """
        Виконує вихід користувача з системи.
        Якщо надано refresh_token_value, він буде інвалідований.
        Повертає True у разі успіху.
        """
        # context = info.context
        # # Поточний користувач може бути отриманий з access токена, якщо він ще валідний
        # # current_user = context.current_user
        #
        # if refresh_token_value:
        #     token_service = TokenService(context.db_session)
        #     await token_service.revoke_refresh_token(refresh_token_value)
        #     # Також можна інвалідувати access токен, якщо є механізм "чорного списку"
        #
        # # TODO: Додати логування виходу
        # return True
        # raise NotImplementedError("Вихід користувача ще не реалізовано.") # Заглушка
        context = info.context
        db_session = context.db_session
        auth_service = AuthService(db_session)

        # Поточний користувач для логування, якщо є
        current_user_display = "Анонімний користувач"
        if context.current_user:
            current_user_display = context.current_user.email

        logger.info(f"GraphQL: Запит на вихід для користувача (токен: {refresh_token_value[:10] if refresh_token_value else 'не надано'}). Поточний користувач сесії GraphQL: {current_user_display}")

        try:
            if refresh_token_value:
                # Якщо передано конкретний refresh token, інвалідуємо його
                await auth_service.invalidate_single_refresh_token(refresh_token_str=refresh_token_value)
                logger.info(f"GraphQL: Refresh token {refresh_token_value[:10]}... інвалідовано.")
            elif context.current_user:
                # Якщо refresh token не передано, але є поточний користувач,
                # інвалідуємо всі його refresh токени (стандартна поведінка для REST logout)
                await auth_service.invalidate_refresh_tokens_for_user(user_id=context.current_user.id)
                logger.info(f"GraphQL: Всі refresh токени для користувача {context.current_user.email} інвалідовано.")
            else:
                # Ні токена, ні користувача - нічого не робимо, але повертаємо успіх,
                # оскільки клієнт міг вже видалити токени локально.
                logger.info("GraphQL: Запит на вихід без токена та без активної сесії користувача.")

            # TODO: Додати інвалідацію access token через blacklist, якщо такий механізм буде.
            return True
        except HTTPException as e:
            logger.warning(f"GraphQL: Помилка виходу - {e.detail}")
            raise Exception(e.detail)
        except Exception as e:
            logger.error(f"GraphQL: Неочікувана помилка виходу - {str(e)}", exc_info=True)
            raise Exception(f"Помилка сервера при виході: {str(e)}")

    @strawberry.mutation(description="Запит на відновлення забутого пароля.")
    async def request_password_reset(self, info: strawberry.Info, input: PasswordResetRequestInput) -> bool:
        """
        Ініціює процес відновлення пароля. Відправляє email з токеном/посиланням.
        Завжди повертає True, щоб не розкривати існування email в системі.
        """
        # context = info.context
        # user_service = UserService(context.db_session)
        # token_service = TokenService(context.db_session) # Для генерації токена скидання
        #
        # user = await user_service.get_user_by_email(input.email)
        # if user:
        #     # Генерація токена скидання, збереження його, відправка email
        #     reset_token = await token_service.create_password_reset_token(user.email)
        #     await user_service.send_password_reset_email(user.email, reset_token)
        # # Незалежно від того, чи знайдено користувача, повертаємо успіх
        return True # Заглушка

    @strawberry.mutation(description="Встановлення нового пароля за допомогою токена скидання.")
    async def confirm_password_reset(self, info: strawberry.Info, input: PasswordResetConfirmInput) -> bool:
        """
        Встановлює новий пароль, використовуючи токен, отриманий з email.
        Повертає True у разі успіху.
        """
        # context = info.context
        # user_service = UserService(context.db_session)
        # token_service = TokenService(context.db_session)
        #
        # email = await token_service.verify_password_reset_token(input.token)
        # if not email:
        #     raise Exception("Недійсний або прострочений токен скидання пароля.")
        #
        # await user_service.reset_password_by_email(email, input.new_password)
        # # Інвалідувати токен скидання після використання
        # await token_service.revoke_password_reset_token(input.token)
        # return True
        raise NotImplementedError("Підтвердження скидання пароля ще не реалізовано.") # Заглушка

    @strawberry.mutation(description="Зміна поточного пароля аутентифікованим користувачем.")
    async def change_password(self, info: strawberry.Info, input: PasswordChangeInput) -> bool:
        """
        Дозволяє аутентифікованому користувачу змінити свій пароль.
        Повертає True у разі успіху.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова.")
        #
        # user_service = UserService(context.db_session)
        # # Перевірка старого пароля (user_service.verify_password)
        # # Оновлення пароля (user_service.change_password)
        # await user_service.change_user_password(user_id=current_user.id, old_password=input.old_password, new_password=input.new_password)
        # return True
        raise NotImplementedError("Зміна пароля ще не реалізована.") # Заглушка

# Експорт класу для агрегації в mutations/__init__.py
__all__ = [
    "AuthMutations",
]
