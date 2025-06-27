# backend/app/src/api/v1/auth/login.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для автентифікації користувачів API v1.

Цей модуль надає API для:
- Входу користувача в систему (отримання JWT токенів).
- Виходу користувача з системи (інвалідaція токенів, якщо підтримується).
- Оновлення JWT токена доступу за допомогою refresh токена.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, Any, Dict # Додано Dict

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.auth.token import TokenSchema, RefreshTokenCreateSchema # Використовуємо реальні схеми
# UserPublicSchema не потрібна для відповіді в login, але може бути потрібна для інших ендпоінтів
# from backend.app.src.schemas.auth.user import UserPublicSchema
from backend.app.src.services.auth.auth_service import AuthService # Головний сервіс автентифікації
from backend.app.src.services.auth.user_service import UserService # Для отримання користувача в refresh
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser # Використовуємо реальні залежності
from backend.app.src.models.auth.user import UserModel # Для type hint

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/login",
    response_model=TokenSchema,
    tags=["Auth"],
    summary="Автентифікація користувача та отримання токенів"
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db_session: DBSession = Depends()
):
    """
    Автентифікує користувача за ім'ям користувача/email та паролем.
    У разі успіху повертає access token та опціонально refresh token.
    """
    logger.info(f"Спроба входу для користувача: {form_data.username}")
    auth_service = AuthService(db_session)

    user = await auth_service.authenticate_user(
        username_or_email=form_data.username,
        password=form_data.password
    )
    if not user:
        logger.warning(f"Не вдалося автентифікувати користувача: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірне ім'я користувача або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Припускаємо, що AuthService може генерувати токени або є окремий TokenService
    # Якщо AuthService генерує:
    access_token, refresh_token = await auth_service.create_jwt_tokens(user=user)

    logger.info(f"Користувач '{user.username}' успішно увійшов. Access token створено.")
    return TokenSchema(
        access_token=access_token,
        refresh_token=refresh_token, # AuthService повинен повертати refresh_token
        token_type="bearer"
    )

@router.post(
    "/refresh-token",
    response_model=TokenSchema,
    tags=["Auth"],
    summary="Оновлення access token за допомогою refresh token"
)
async def refresh_access_token_endpoint(
    refresh_token_data: RefreshTokenCreateSchema, # Використовуємо схему для тіла запиту
    db_session: DBSession = Depends()
):
    """
    Оновлює access token, якщо наданий дійсний refresh token.
    Може також повертати новий refresh token (рекомендується для безпеки).
    """
    logger.info(f"Спроба оновлення access token.")
    auth_service = AuthService(db_session)
    user_service = UserService(db_session) # Може знадобитися для отримання даних користувача

    try:
        # AuthService повинен мати метод для валідації refresh token та видачі нових токенів
        new_access_token, new_refresh_token, user_id = await auth_service.refresh_jwt_tokens(
            refresh_token_str=refresh_token_data.refresh_token
        )

        # user = await user_service.get_user_by_id(user_id) # Якщо потрібні дані користувача для логування
        # if not user: # Малоймовірно, якщо refresh_jwt_tokens успішний
        #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Користувач не знайдений")

        logger.info(f"Access token успішно оновлено для користувача ID {user_id}.")
        return TokenSchema(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
    except HTTPException as e: # AuthService може кидати HTTPException
        logger.warning(f"Помилка оновлення access token: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка під час оновлення refresh token: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при оновленні токена")


@router.post(
    "/logout",
    tags=["Auth"],
    summary="Вихід користувача з системи",
    status_code=status.HTTP_204_NO_CONTENT
)
async def logout(
    # response: Response, # Якщо потрібно маніпулювати куками
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
    # TODO: Потрібно передати сам токен для інвалідації, якщо це access token
    # token: Annotated[str, Depends(oauth2_scheme)] # Якщо інвалідуємо access token
):
    """
    Виконує вихід користувача з системи.
    - Інвалідує refresh token (наприклад, видаляє його з БД).
    - Опціонально: додає поточний access token в чорний список (якщо підтримується).
    """
    logger.info(f"Користувач '{current_user.username}' (ID: {current_user.id}) виконує вихід.")

    auth_service = AuthService(db_session)

    # Припускаємо, що AuthService має метод для інвалідації токенів
    # Для logout зазвичай інвалідують refresh token, що зберігається на сервері.
    # Access token зазвичай має короткий термін життя і інвалідується на клієнті (видаленням).
    # Якщо є refresh_token_data в запиті (наприклад, для інвалідації конкретного),
    # то його треба передати. Якщо інвалідуються всі для користувача:
    await auth_service.invalidate_refresh_tokens_for_user(user_id=current_user.id)

    # Якщо access token додається в blacklist:
    # access_token_str = token # Отриманий з Depends(oauth2_scheme)
    # await auth_service.add_access_token_to_blacklist(access_token_str)

    logger.info(f"Refresh токени для користувача {current_user.username} інвалідовано.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Роутер буде підключений в backend/app/src/api/v1/auth/__init__.py
# або безпосередньо в backend/app/src/api/v1/router.py
