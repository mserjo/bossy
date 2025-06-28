# backend/app/src/api/v1/auth/profile.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління профілем поточного автентифікованого користувача API v1.

Цей модуль надає API для:
- Отримання даних профілю поточного користувача.
- Оновлення даних профілю поточного користувача (наприклад, ім'я, username, налаштування).
- Зміни паролю поточного користувача.
- Можливо, завантаження/оновлення аватара (хоча це може бути винесено в `files` API).
"""

# sqlalchemy.ext.asyncio.AsyncSession не потрібен тут напряму
from fastapi import APIRouter, Depends, HTTPException, status # Додано APIRouter, HTTPException, status

from backend.app.src.config.logging import logger # Змінено імпорт get_logger на logger
from backend.app.src.schemas.auth.user import UserPublicSchema, UserUpdateSchema, UserPasswordUpdateSchema # Виправлено імена схем
from backend.app.src.services.auth.user_service import UserService # Реальний сервіс
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser # Реальні залежності
from backend.app.src.models.auth.user import UserModel # Для type hint

# logger = get_logger(__name__) # logger тепер імпортується напряму
router = APIRouter()


@router.get(
    "/me",
    response_model=UserPublicSchema, # Повертаємо публічну схему
    tags=["Profile"],
    summary="Отримати дані поточного користувача"
)
async def read_current_user_profile(
    current_user: UserModel = Depends(CurrentActiveUser) # Тепер це UserModel
):
    """
    Повертає інформацію про профіль поточного автентифікованого та активного користувача.
    """
    logger.info(f"Запит даних профілю для поточного користувача: {current_user.email}")
    # Конвертуємо UserModel в UserPublicSchema для відповіді
    return UserPublicSchema.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserPublicSchema, # Повертаємо публічну схему
    tags=["Profile"],
    summary="Оновити профіль поточного користувача"
)
async def update_current_user_profile(
    profile_update_data: UserUpdateSchema, # Використовуємо UserUpdateSchema
    current_user: UserModel = Depends(CurrentActiveUser), # Тепер це UserModel
    db_session: DBSession = Depends()
):
    """
    Оновлює дані профілю поточного автентифікованого користувача.
    """
    logger.info(f"Запит на оновлення профілю для користувача: {current_user.email}")
    user_service = UserService(db_session)
    try:
        # UserService.update_user_profile приймає current_user: UserModel та obj_in: UserUpdateSchema
        updated_user = await user_service.update_user_profile(
            current_user=current_user, # Передаємо UserModel
            obj_in=profile_update_data
        )
        # Сервіс має кидати виняток при помилці, тому перевірка на None не потрібна, якщо сервіс надійний.
    except BadRequestException as e: # Ловимо кастомні винятки
        logger.warning(f"Помилка оновлення профілю для {current_user.email}: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка під час оновлення профілю {current_user.email}: {e_gen}", exc_info=True)
        from backend.app.src.core.exceptions import InternalServerErrorException # Локальний імпорт
        raise InternalServerErrorException(detail_key="error_profile_update_failed") # Новий ключ

    logger.info(f"Профіль користувача {updated_user.email} оновлено.")
    return UserPublicSchema.model_validate(updated_user)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Profile"],
    summary="Змінити пароль поточного користувача"
)
async def change_current_user_password(
    password_data: UserPasswordUpdateSchema, # Використовуємо UserPasswordUpdateSchema
    current_user: UserModel = Depends(CurrentActiveUser), # Тепер це UserModel
    db_session: DBSession = Depends()
):
    """
    Дозволяє поточному автентифікованому користувачу змінити свій пароль.
    Потребує введення поточного паролю для підтвердження.
    """
    logger.info(f"Запит на зміну пароля для користувача: {current_user.email}")
    user_service = UserService(db_session)

    try:
        await user_service.change_user_password( # Метод в сервісі називається change_user_password
            user=current_user,
            old_password=password_data.current_password,
            new_password=password_data.new_password
        )
    except BadRequestException as e: # Сервіс кидає BadRequestException при помилках
        logger.warning(f"Не вдалося змінити пароль для {current_user.email}: {e.detail}")
        raise e # Перекидаємо далі
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка під час зміни пароля для {current_user.email}: {e_gen}", exc_info=True)
        from backend.app.src.core.exceptions import InternalServerErrorException # Локальний імпорт
        raise InternalServerErrorException(detail_key="error_password_change_failed") # Новий ключ

    logger.info(f"Пароль для користувача {current_user.email} успішно змінено.")
    # Тіло відповіді не потрібне при успішній зміні (204 No Content)
    # FastAPI автоматично поверне 204, якщо немає return

# TODO: Додати ендпоінт для завантаження/оновлення аватара, якщо це тут,
# а не в `files` API. Це може вимагати `UploadFile`.
# @router.post("/me/avatar", tags=["Profile"], summary="Оновити аватар поточного користувача")
# async def upload_avatar(...): ...

# Роутер буде підключений в backend/app/src/api/v1/auth/__init__.py
# або безпосередньо в backend/app/src/api/v1/router.py
