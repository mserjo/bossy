# backend/app/src/api/v1/auth/login.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для автентифікації: вхід, оновлення токена, вихід.
"""
# import logging # Замінено на централізований логер
from typing import Annotated  # Для FastAPI.Depends з Python 3.9+

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm  # Для форми логіну
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import (
    get_api_db_session,
    get_user_service,  # Отримуємо реальні сервіси
    get_token_service,
    # TODO: Створити/використати залежність, що витягує refresh_token з cookie та валідує його через TokenService
    #  Наприклад: get_validated_refresh_token_cookie -> Tuple[str, User] (токен_рядок, користувач)
    #  Поки що, будемо використовувати концептуальну залежність або спрощену логіку.
)
from backend.app.src.services.auth.user import UserService
from backend.app.src.services.auth.token import TokenService
from backend.app.src.models.auth.user import User  # Модель SQLAlchemy
from backend.app.src.schemas.auth.token import TokenResponse
# LoginRequest (Pydantic модель) може бути не потрібна, якщо використовувати OAuth2PasswordRequestForm
# from backend.app.src.schemas.auth.login import LoginRequest # Якщо використовується кастомна схема
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings  # Для налаштувань cookie
from fastapi import Response as FastAPIResponse # для HTTP_204_NO_CONTENT

router = APIRouter()

# TODO: Перемістити ці константи в `settings` або в `TokenService`
REFRESH_TOKEN_COOKIE_KEY = "refreshToken"


@router.post(
    "/token",  # Стандартний шлях для отримання токенів за логіном/паролем
    response_model=TokenResponse,
    summary="Автентифікація та отримання токенів",  # i18n
    description="Аутентифікує користувача за email (в полі username) та паролем, повертає access та refresh токени."
    # i18n
)
async def login_for_access_token(
        response: Response,  # Для встановлення httpOnly cookie
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],  # Використовуємо стандартну форму OAuth2
        db_session: AsyncSession = Depends(get_api_db_session),  # Залежність для сесії БД
        user_service: UserService = Depends(get_user_service),  # Залежність для UserService
        token_service: TokenService = Depends(get_token_service)  # Залежність для TokenService
):
    """
    Автентифікує користувача та видає токени.
    Refresh token встановлюється в HttpOnly cookie.

    - **username**: Електронна пошта користувача (поле username форми OAuth2).
    - **password**: Пароль користувача.
    """
    logger.info(f"Спроба входу для користувача: {form_data.username}")

    # Автентифікація користувача через UserService
    # TODO: UserService повинен мати метод authenticate_user, який повертає User або кидає виняток
    authenticated_user = await user_service.authenticate_user(
        email=form_data.username,  # OAuth2PasswordRequestForm використовує 'username' для email
        password=form_data.password
    )
    if not authenticated_user:
        logger.warning(f"Невдала спроба входу для: {form_data.username} - невірні облікові дані.")
        # i18n
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильний email або пароль.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authenticated_user.is_active:
        logger.warning(f"Спроба входу неактивним користувачем: {form_data.username}")
        # i18n
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # Або 403 Forbidden
            detail="Обліковий запис неактивний."
        )

    # Створення токенів через TokenService
    # TODO: TokenService.create_access_token має приймати user_id або user об'єкт
    # TODO: TokenService.create_refresh_token має зберігати JTI в БД і повертати сам токен-рядок
    access_token_str = await token_service.create_access_token(subject=str(authenticated_user.id))
    refresh_token_str = await token_service.create_refresh_token(user_id=authenticated_user.id)

    # Встановлення refresh_token в httpOnly cookie
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_KEY,
        value=refresh_token_str,
        httponly=True,
        secure=global_settings.REFRESH_TOKEN_COOKIE_SECURE,  # True для HTTPS
        samesite=global_settings.REFRESH_TOKEN_COOKIE_SAMESITE,  # 'lax' або 'strict'
        max_age=global_settings.REFRESH_TOKEN_EXPIRE_SECONDS,
        path=f"{global_settings.API_V1_STR}/auth"  # Обмежуємо шлях дії cookie
    )
    logger.info(f"Успішний вхід для користувача '{authenticated_user.username}'. Токени видано.")
    return TokenResponse(
        access_token=access_token_str,
        refresh_token=refresh_token_str,
        # Повертаємо також у тілі для зручності клієнтів, що не можуть використовувати cookies
        token_type="bearer"
    )


async def get_user_from_valid_refresh_token_cookie(  # Залежність для /refresh та /logout
        request: Request,
        token_service: TokenService = Depends(get_token_service)
) -> User:
    """
    Витягує refresh token з cookie, валідує його через TokenService
    (який має обробити JTI, знайти в БД, перевірити revoke status, expiry),
    та повертає асоційованого користувача (ORM модель).
    TokenService.process_refresh_token також має відкликати використаний токен (для ротації).
    """
    refresh_token_str = request.cookies.get(REFRESH_TOKEN_COOKIE_KEY)
    if not refresh_token_str:
        logger.warning("Спроба оновлення/виходу без refresh token cookie.")
        # i18n
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token відсутній.")

    # TokenService.process_refresh_token має повернути User або кинути помилку
    # Також він має відкликати цей refresh_token (JTI) для ротації.
    user = await token_service.process_refresh_token(refresh_token_jti_str=refresh_token_str)
    if not user:  # Якщо process_refresh_token повертає None при помилці валідації
        logger.warning(f"Недійсний або відкликаний refresh token надано (cookie). Токен: ...{refresh_token_str[-6:]}")
        # i18n
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Недійсний або прострочений refresh token.")
    return user


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Оновлення токена доступу",  # i18n
    description="Оновлює токен доступу, використовуючи refresh token з HttpOnly cookie. Реалізує ротацію refresh token."
    # i18n
)
async def refresh_access_token(
        response: Response,  # Для встановлення нового refresh_token cookie
        # Залежність, що валідує refresh token з cookie та повертає користувача.
        # TokenService.process_refresh_token має відкликати старий refresh token.
        current_user: User = Depends(get_user_from_valid_refresh_token_cookie),
        token_service: TokenService = Depends(get_token_service)  # Отримуємо TokenService
):
    """
    Оновлює токен доступу та генерує новий refresh token (ротація).
    """
    if not current_user.is_active:
        logger.warning(f"Спроба оновлення токена неактивним користувачем: {current_user.username}")
        # i18n
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Обліковий запис неактивний.")

    # Створюємо новий access token
    new_access_token_str = await token_service.create_access_token(subject=str(current_user.id))
    # Створюємо новий refresh token (ротація)
    new_refresh_token_str = await token_service.create_refresh_token(user_id=current_user.id)

    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_KEY,
        value=new_refresh_token_str,
        httponly=True,
        secure=global_settings.REFRESH_TOKEN_COOKIE_SECURE,
        samesite=global_settings.REFRESH_TOKEN_COOKIE_SAMESITE,
        max_age=global_settings.REFRESH_TOKEN_EXPIRE_SECONDS,
        path=f"{global_settings.API_V1_STR}/auth"
    )
    logger.info(f"Токени успішно оновлено для користувача '{current_user.username}'.")
    return TokenResponse(
        access_token=new_access_token_str,
        refresh_token=new_refresh_token_str,  # Повертаємо новий refresh token
        token_type="bearer"
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Вихід користувача",  # i18n
    description="Здійснює вихід користувача, інвалідуючи поточний refresh token (видаляючи його з БД та cookie)."
    # i18n
)
async def logout(
        response: Response,
        request: Request,  # Потрібен для отримання cookie, якщо залежність не передає сам токен
        # Залежність, що валідує refresh token з cookie.
        # TokenService.process_refresh_token НЕ повинен відкликати токен тут, бо ми це робимо явно.
        # Або потрібен інший метод в TokenService для простої валідації та отримання JTI.
        # Поки що, припустимо, що get_user_from_valid_refresh_token_cookie НЕ відкликає токен,
        # а TokenService має окремий метод revoke_refresh_token_by_jti.
        # АБО, якщо process_refresh_token відкликає, то це вже частина логіки виходу.
        # Для logout достатньо, щоб refresh token був видалений з БД.
        token_service: TokenService = Depends(get_token_service)
):
    """
    Виконує вихід користувача.
    Інвалідує refresh token, що був переданий в httpOnly cookie.
    """
    refresh_token_str = request.cookies.get(REFRESH_TOKEN_COOKIE_KEY)
    if not refresh_token_str:
        logger.info("Спроба виходу без refresh token cookie. Жодних дій на сервері.")
        # Все одно видаляємо cookie, якщо він якось залишився у клієнта
        response.delete_cookie(
            key=REFRESH_TOKEN_COOKIE_KEY,
            secure=global_settings.REFRESH_TOKEN_COOKIE_SECURE,
            samesite=global_settings.REFRESH_TOKEN_COOKIE_SAMESITE,
            path=f"{global_settings.API_V1_STR}/auth"
        )
        # i18n
        # Не кидаємо помилку, просто виходимо, якщо токена немає.
        return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)

    # TODO: TokenService має надати метод для відкликання refresh токена за його значенням (JTI).
    #  `revoke_refresh_token` в TokenService приймає JTI.
    success = await token_service.revoke_refresh_token(refresh_token_jti_str=refresh_token_str)

    if success:
        logger.info(f"Refresh token (останні 6 символів: ...{refresh_token_str[-6:]}) успішно відкликано.")
    else:
        logger.warning(
            f"Не вдалося відкликати refresh token (можливо, вже не існував або невалідний): ...{refresh_token_str[-6:]}")

    # Видаляємо cookie з відповіді
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE_KEY,
        secure=global_settings.REFRESH_TOKEN_COOKIE_SECURE,
        samesite=global_settings.REFRESH_TOKEN_COOKIE_SAMESITE,
        path=f"{global_settings.API_V1_STR}/auth"
    )
    logger.info(f"Cookie '{REFRESH_TOKEN_COOKIE_KEY}' видалено для сесії виходу.")
    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)


logger.info("Роутер для автентифікації, оновлення токенів та виходу (`/login`, `/refresh`, `/logout`) визначено.")
