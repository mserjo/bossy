# backend/app/src/api/v1/auth/register.py
# -*- coding: utf-8 -*-
"""
Ендпоінт для реєстрації нових користувачів.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.api.dependencies import get_api_db_session, get_user_service, get_token_service
# from backend.app.src.models.auth.user import User as UserModel # UserModel не використовується прямо у відповіді, якщо є UserResponse
from backend.app.src.schemas.auth.user import UserCreate, UserResponse
from backend.app.src.schemas.auth.token import TokenResponse  # Для опціонального авто-логіну
from backend.app.src.services.auth.user import UserService
from backend.app.src.services.auth.token import TokenService  # Для опціонального авто-логіну
from backend.app.src.config import settings as global_settings  # Для налаштувань cookie та авто-логіну
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter()

# ПРИМІТКА: Успішна реєстрація залежить від коректної реалізації методу `create_user`
# в `UserService`, включаючи обробку унікальності полів та можливе призначення
# типів/ролей користувача за замовчуванням. Також, логіка може змінитися,
# якщо буде реалізовано автоматичний вхід після реєстрації (див. TODO нижче).
@router.post(
    "/register",
    # response_model=UserResponse, # Зміниться на TokenResponse, якщо буде авто-логін
    status_code=status.HTTP_201_CREATED,
    summary="Реєстрація нового користувача",  # i18n
    description="Створює новий обліковий запис користувача в системі. За замовчуванням не виконує автоматичний вхід."
    # i18n
)
async def register_user(
        user_in: UserCreate,  # Дані для створення користувача
        response: Response,  # Для встановлення cookie при авто-логіні
        user_service: UserService = Depends(get_user_service),
        token_service: TokenService = Depends(get_token_service)  # Для авто-логіну
) -> UserResponse:  # Або TokenResponse при авто-логіні
    """
    Реєструє нового користувача в системі.

    - **email**: Електронна пошта користувача (має бути унікальною).
    - **password**: Пароль користувача (буде хешовано перед збереженням).
    - **username**: Ім'я користувача/нікнейм (має бути унікальним, якщо використовується).
    - **first_name**: Ім'я (опціонально).
    - **last_name**: Прізвище (опціонально).
    """
    logger.info(f"Спроба реєстрації нового користувача з email: {user_in.email}" + (
        f" та username: {user_in.username}" if user_in.username else ""))

    # Логіка перевірки унікальності email/username тепер інкапсульована в UserService.create_user,
    # який має кидати ValueError у разі дублювання.

    try:
        # UserService.create_user має повернути ORM модель створеного користувача
        # TODO: UserService.create_user може потребувати `user_type_code` та `role_codes` за замовчуванням.
        #  Наприклад, `user_service.create_user(user_create_data=user_in, user_type_code="USER_TYPE", role_codes=["USER"])`
        #  Це залежить від реалізації `create_user` в `UserService`. Припускаємо, що він має дефолти.
        created_user_orm = await user_service.create_user(user_create_data=user_in)
        if not created_user_orm:  # Малоймовірно, якщо сервіс кидає винятки при помилках
            logger.error(f"UserService.create_user повернув None для email {user_in.email}")
            # i18n
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Не вдалося створити користувача.")

    except ValueError as e:  # Обробка помилок валідації з сервісного шару (наприклад, email/username зайнято)
        logger.warning(f"Помилка валідації при реєстрації користувача (email: {user_in.email}): {e}")
        # i18n (повідомлення `e` вже має бути підготовленим для користувача з сервісу)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # Або 409 Conflict для дублікатів
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Неочікувана помилка під час створення користувача (email: {user_in.email}): {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Виникла помилка сервера під час реєстрації."
        )

    logger.info(f"Користувача '{created_user_orm.username}' (ID: {created_user_orm.id}) успішно зареєстровано.")

    # TODO: Реалізувати автоматичний вхід після реєстрації, якщо це потрібно згідно `technical_task.txt`.
    #  Якщо так, цей ендпоінт має повертати TokenResponse.
    # if getattr(global_settings, "AUTO_LOGIN_AFTER_REGISTRATION", False):
    #     logger.info(f"Виконується автоматичний вхід для користувача '{created_user_orm.username}'.")
    #     access_token_str = await token_service.create_access_token(subject=str(created_user_orm.id))
    #     refresh_token_str = await token_service.create_refresh_token(user_id=created_user_orm.id)
    #     response.set_cookie(
    #         key=global_settings.REFRESH_TOKEN_COOKIE_KEY, # Використання global_settings
    #         value=refresh_token_str,
    #         httponly=True, secure=global_settings.REFRESH_TOKEN_COOKIE_SECURE,
    #         samesite=global_settings.REFRESH_TOKEN_COOKIE_SAMESITE,
    #         max_age=global_settings.REFRESH_TOKEN_EXPIRE_SECONDS,
    #         path=f"{global_settings.API_V1_STR}/auth"
    #     )
    #     return TokenResponse(access_token=access_token_str, refresh_token=refresh_token_str, token_type="bearer")

    # За замовчуванням повертаємо дані користувача без автоматичного входу
    # Pydantic v2 .model_validate() використовується неявно FastAPI при поверненні ORM моделі
    return UserResponse.model_validate(created_user_orm)


logger.info("Роутер для реєстрації (`/register`) визначено.")
