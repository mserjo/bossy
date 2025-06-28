# backend/app/src/api/v1/files/avatars.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління аватарами користувачів API v1.

Цей модуль надає API для:
- Завантаження/оновлення аватара поточного користувача.
- Отримання URL аватара поточного користувача.
- Отримання URL аватара іншого користувача (за ID).
- Видалення свого аватара.
"""

from fastapi import (
    APIRouter, Depends, HTTPException, status, UploadFile, File, Path, Response as FastAPIResponse, Request
)
from typing import Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.files.avatar import UserAvatarSchema
from backend.app.src.services.files.avatar_service import AvatarService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.config import settings # Для налаштувань файлів

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти для аватарів, префікс /avatars буде встановлено в files/__init__.py
# або /users/me/avatar, якщо логіка інша.
# Поточна структура передбачає, що цей роутер підключається до files_router,
# тому шляхи будуть відносно /files/avatars

@router.post(
    "/me",
    response_model=UserAvatarSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Files", "User Avatars"],
    summary="Завантажити або оновити свій аватар"
)
async def upload_my_avatar(
    request: Request, # Для генерації URL
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends(),
    avatar_file: UploadFile = File(..., description="Файл аватара (зображення: jpg, png, gif)")
):
    logger.info(f"Користувач {current_user.email} (ID: {current_user.id}) завантажує новий аватар: {avatar_file.filename}.")

    if avatar_file.content_type not in settings.ALLOWED_AVATAR_MIME_TYPES:
        logger.warning(f"Неприпустимий тип файлу аватара {avatar_file.content_type} від {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неприпустимий тип файлу аватара. Дозволені: {', '.join(settings.ALLOWED_AVATAR_MIME_TYPES)}."
        )

    file_content = await avatar_file.read()
    if len(file_content) > settings.MAX_AVATAR_SIZE_BYTES:
        logger.warning(f"Файл аватара {avatar_file.filename} занадто великий ({len(file_content)} байт) від {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл аватара занадто великий. Максимальний розмір: {settings.MAX_AVATAR_SIZE_BYTES // 1024}KB."
        )

    avatar_service = AvatarService(db_session)
    try:
        user_avatar_info = await avatar_service.upload_or_update_avatar(
            user_id=current_user.id,
            file_data=file_content,
            filename=avatar_file.filename,
            content_type=avatar_file.content_type,
            file_size=len(file_content),
            request_base_url=str(request.base_url) # Для генерації повного URL, якщо потрібно
        )
        logger.info(f"Аватар для користувача {current_user.email} успішно завантажено/оновлено. URL: {user_avatar_info.avatar_url}")
        return user_avatar_info
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка завантаження аватара для {current_user.email}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при завантаженні аватара.")

@router.get(
    "/me",
    response_model=Optional[UserAvatarSchema],
    tags=["Files", "User Avatars"],
    summary="Отримати інформацію про свій аватар"
)
async def get_my_avatar_info(
    request: Request,
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} запитує інформацію про свій аватар.")
    avatar_service = AvatarService(db_session)
    avatar_info = await avatar_service.get_avatar_info_by_user_id(
        user_id=current_user.id,
        request_base_url=str(request.base_url)
        )
    if not avatar_info:
        logger.info(f"Аватар для користувача {current_user.email} не знайдено.")
    return avatar_info

@router.get(
    "/{user_id_target}",
    response_model=Optional[UserAvatarSchema],
    tags=["Files", "User Avatars"],
    summary="Отримати інформацію про аватар іншого користувача"
)
async def get_user_avatar_info(
    request: Request,
    user_id_target: int = Path(..., description="ID користувача, чий аватар запитується"),
    db_session: DBSession = Depends()
    # current_user: UserModel = Depends(CurrentActiveUser), # Якщо потрібна автентифікація для перегляду чужих аватарів
):
    logger.info(f"Запит аватара для користувача ID {user_id_target}.")
    avatar_service = AvatarService(db_session)
    avatar_info = await avatar_service.get_avatar_info_by_user_id(
        user_id=user_id_target,
        request_base_url=str(request.base_url)
        )
    if not avatar_info:
        logger.info(f"Аватар для користувача ID {user_id_target} не знайдено.")
    return avatar_info

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Files", "User Avatars"],
    summary="Видалити свій аватар"
)
async def delete_my_avatar(
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} (ID: {current_user.id}) видаляє свій аватар.")
    avatar_service = AvatarService(db_session)
    try:
        success = await avatar_service.delete_avatar_by_user_id(user_id=current_user.id)
        if not success:
            logger.info(f"Аватар для користувача {current_user.email} не знайдено для видалення, або помилка видалення.")
            # Якщо аватара не було, то операція "видалення" по суті успішна (його немає)
            # Повертаємо 204, щоб не вводити в оману клієнта, що сталася помилка, якщо він просто не існував.
            # Якщо ж сервіс розрізняє "не знайдено" і "помилка видалення існуючого", то можна повернути 404.
    except Exception as e_gen:
        logger.error(f"Помилка видалення аватара для {current_user.email}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при видаленні аватара.")

    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)
