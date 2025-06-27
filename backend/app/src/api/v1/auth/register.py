# backend/app/src/api/v1/auth/register.py
# -*- coding: utf-8 -*-
"""
Ендпоінт для реєстрації нових користувачів API v1.

Цей модуль надає API для створення нового облікового запису користувача.
Він включає валідацію вхідних даних, перевірку на унікальність email/username,
хешування паролю та збереження нового користувача в базі даних.
"""

from fastapi import APIRouter, Depends, HTTPException, status
# sqlalchemy.ext.asyncio.AsyncSession не потрібен тут напряму

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.auth.user import UserCreateSchema, UserPublicSchema # Реальні схеми
from backend.app.src.services.auth.user_service import UserService # Реальний сервіс
from backend.app.src.api.dependencies import DBSession # Реальна залежність
# TODO: Можливо, потрібен сервіс налаштувань для перевірки дозволу реєстрації
# from backend.app.src.services.system.system_settings_service import SystemSettingsService
# from backend.app.src.models.auth.user import UserModel # Якщо потрібно повернути модель для подальшої обробки

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/register",
    response_model=UserPublicSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
    summary="Реєстрація нового користувача"
)
async def register_new_user(
    user_create_data: UserCreateSchema,
    db_session: DBSession = Depends()
):
    """
    Створює новий обліковий запис користувача.
    - Перевіряє унікальність email та username (якщо надано).
    - Хешує пароль.
    - Зберігає нового користувача в базі даних.
    - Повертає публічні дані створеного користувача.
    """
    logger.info(f"Запит на реєстрацію нового користувача: {user_create_data.email}")

    user_service = UserService(db_session)

    # TODO: Додати перевірку, чи дозволена реєстрація в системних налаштуваннях.
    # settings_service = SystemSettingsService(db_session)
    # allow_registration_setting = await settings_service.get_setting_by_name("allow_registration")
    # if not (allow_registration_setting and allow_registration_setting.value is True):
    #     logger.warning("Спроба реєстрації, коли вона вимкнена в налаштуваннях.")
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Реєстрація нових користувачів наразі вимкнена."
    #     )

    try:
        # UserService.create_user повинен обробляти унікальність та повертати UserModel
        created_user = await user_service.create_user(user_create_data=user_create_data)
        if not created_user: # Додаткова перевірка, хоча сервіс, ймовірно, кинув би виняток
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не вдалося створити користувача."
            )

    except HTTPException as e: # Якщо сервіс кидає HTTPException (напр. 400 Bad Request for duplicate)
        logger.warning(f"Помилка реєстрації для {user_create_data.email}: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка під час реєстрації користувача {user_create_data.email}: {e_gen}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка сервера під час реєстрації користувача."
        )

    # TODO: Після успішної реєстрації можна:
    # 1. Автоматично логінити користувача та повертати токени (виклик AuthService).
    # 2. Надсилати email для підтвердження реєстрації (виклик NotificationService).

    logger.info(f"Користувач {created_user.email} успішно зареєстрований.")
    # Перетворюємо модель БД на Pydantic схему для відповіді
    # Це може робитися автоматично, якщо response_model налаштований правильно
    # і UserModel сумісний з UserPublicSchema (наприклад, через orm_mode).
    # Або явно:
    return UserPublicSchema.model_validate(created_user)


# Роутер буде підключений в backend/app/src/api/v1/auth/__init__.py
# або безпосередньо в backend/app/src/api/v1/router.py
