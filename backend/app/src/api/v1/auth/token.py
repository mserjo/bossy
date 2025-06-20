# backend/app/src/api/v1/auth/token.py
# -*- coding: utf-8 -*-
"""
Ендпоінти, пов'язані з управлінням та валідацією токенів.
Наприклад, перевірка валідності існуючого токена доступу.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession  # Може не знадобитися, якщо сервіси обробляють сесію

from backend.app.src.api.dependencies import get_api_db_session, get_current_active_superuser, get_token_service, get_user_service
from backend.app.src.schemas.auth.token import TokenData, TokenVerifyRequest, TokenVerifyResponse
from backend.app.src.services.auth.token import TokenService
from backend.app.src.services.auth.user import UserService  # Для додаткової перевірки користувача
from backend.app.src.models.auth.user import User as UserModel  # Для перевірки користувача
from backend.app.src.config import settings as global_settings  # Для JWT_SECRET_KEY, ALGORITHM (якщо потрібні напряму, але краще через сервіс)
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter()

# ПРИМІТКА: Функціональність цього ендпоінта залежить від методу `validate_access_token`
# в `TokenService`. Рішення щодо необхідності додаткової перевірки користувача
# (див. TODO нижче) вплине на кінцеву логіку.
@router.post(
    "/verify",  # Префікс /token буде додано в auth/__init__.py -> /auth/token/verify
    response_model=TokenVerifyResponse,
    summary="Перевірка валідності токена доступу",  # i18n
    description="Перевіряє наданий токен доступу та повертає його розкодовані дані, якщо токен валідний. Доступно тільки суперкористувачам.",
    # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Захист ендпоінту
)
async def verify_access_token_endpoint(  # Перейменовано
        token_data: TokenVerifyRequest,
        token_service: TokenService = Depends(get_token_service),
        user_service: UserService = Depends(get_user_service)  # Для опціональної перевірки користувача
):
    """
    Перевіряє валідність токена доступу.

    - **token**: Токен доступу (access token) для перевірки.
    """
    logger.info(f"Запит на перевірку токена (перші 15 символів): {token_data.token[:15]}...")

    try:
        # TokenService.validate_access_token повертає payload або None/кидає виняток
        payload_dict = await token_service.validate_access_token(token=token_data.token)

        if not payload_dict:  # Якщо сервіс повертає None при невалідному токені
            logger.warning(f"Перевірка токена не вдалася: validate_access_token повернув None.")
            # i18n
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Наданий токен невалідний або прострочений.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id_from_token = payload_dict.get("sub")
        if not user_id_from_token:
            logger.warning("Токен валідний, але відсутній 'sub' (ID користувача) в payload.")
            # i18n
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Некоректний формат токена: відсутній ідентифікатор користувача.")

        # Опціональна додаткова перевірка: чи існує користувач і чи він активний
        # TODO: Вирішити, чи потрібна ця перевірка тут, якщо токен вже валідний.
        #  Для інтроспекції токена суперкористувачем, можливо, достатньо просто розкодованого payload.
        # user = await user_service.get_user_orm_by_id(user_id=UUID(user_id_from_token))
        # if not user:
        #     logger.warning(f"Користувач {user_id_from_token} з токена не знайдений в БД.")
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Користувач, асоційований з токеном, не знайдений.") # i18n
        # if not user.is_active:
        #     logger.warning(f"Користувач {user_id_from_token} з токена неактивний.")
        #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Користувач, асоційований з токеном, неактивний.") # i18n

        logger.info(f"Токен успішно перевірено для користувача ID: {user_id_from_token}.")
        # i18n
        return TokenVerifyResponse(
            valid=True,
            message="Токен валідний.",
            data=TokenData(**payload_dict)  # Перетворюємо payload в Pydantic модель TokenData
        )
    except HTTPException as http_exc:  # Перехоплюємо HTTPException, що могли бути кинуті з token_service
        raise http_exc
    except Exception as e:  # Для інших непередбачених помилок (наприклад, з TokenData(**payload_dict))
        logger.error(f"Неочікувана помилка перевірки токена: {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка сервера під час перевірки токена."
        )


# TODO: Розглянути додавання інших ендпоінтів, пов'язаних з токенами, якщо потрібно:
#  - Ендпоінт для відкликання певного токена (якщо реалізовано JTI та список відкликаних токенів).
#  - Ендпоінт для переліку активних сесій/токенів користувача (для адміністрування).

logger.info("Роутер для операцій з токенами (`/token/*`) визначено.")
