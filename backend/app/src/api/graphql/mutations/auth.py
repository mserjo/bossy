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

# TODO: Імпортувати сервіси
# from backend.app.src.services.auth.user_service import UserService
# from backend.app.src.services.auth.token_service import TokenService
# from backend.app.src.services.files.avatar_service import AvatarService # Якщо тут обробка аватара
# from backend.app.src.core.dependencies import get_current_active_user # Для мутацій, що потребують автентифікації

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
        raise NotImplementedError("Реєстрація користувача ще не реалізована.") # Заглушка

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
        raise NotImplementedError("Логін користувача ще не реалізований.") # Заглушка

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
        raise NotImplementedError("Оновлення токена ще не реалізовано.") # Заглушка

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
        raise NotImplementedError("Вихід користувача ще не реалізований.") # Заглушка

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
