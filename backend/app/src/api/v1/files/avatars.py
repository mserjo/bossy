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

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Path, Response
from typing import Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.files.avatar import UserAvatarSchema # Для відповіді з URL
from backend.app.src.schemas.files.file import FileSchema # Можливо, для загальної інформації про файл
from backend.app.src.services.files.avatar_service import AvatarService
# FileService може знадобитися для безпосередньої роботи з файлами, якщо AvatarService його не інкапсулює повністю
# from backend.app.src.services.files.file_service import FileService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти для аватарів, префікс /files/avatars

@router.post(
    "/me", # Тобто /files/avatars/me
    response_model=UserAvatarSchema, # Повертає інформацію про аватар, включаючи URL
    status_code=status.HTTP_201_CREATED,
    tags=["Files", "User Avatars"],
    summary="Завантажити або оновити свій аватар"
)
async def upload_my_avatar(
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends(),
    avatar_file: UploadFile = File(..., description="Файл аватара (зображення)")
):
    """
    Завантажує новий або оновлює існуючий аватар для поточного користувача.
    Приймає файл зображення.
    """
    logger.info(f"Користувач {current_user.email} (ID: {current_user.id}) завантажує новий аватар.")

    # TODO: Додати перевірку типу файлу (MIME type) та розміру файлу.
    # Наприклад:
    # allowed_mime_types = ["image/jpeg", "image/png", "image/gif"]
    # if avatar_file.content_type not in allowed_mime_types:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неприпустимий тип файлу.")
    # max_size_bytes = 5 * 1024 * 1024 # 5 MB
    # if avatar_file.size > max_size_bytes:
    #     raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Файл занадто великий.")

    avatar_service = AvatarService(db_session)
    try:
        # Сервіс повинен обробити збереження файлу та оновлення запису в БД
        user_avatar_info = await avatar_service.upload_or_update_avatar(
            user_id=current_user.id,
            file_data=await avatar_file.read(), # Читаємо вміст файлу
            filename=avatar_file.filename,
            content_type=avatar_file.content_type
        )
        logger.info(f"Аватар для користувача {current_user.email} успішно завантажено/оновлено.")
        return user_avatar_info
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка завантаження аватара для {current_user.email}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при завантаженні аватара.")

@router.get(
    "/me",
    response_model=Optional[UserAvatarSchema], # Може бути None, якщо аватар не встановлено
    tags=["Files", "User Avatars"],
    summary="Отримати інформацію про свій аватар"
)
async def get_my_avatar_info(
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    """
    Повертає інформацію про поточний аватар користувача (наприклад, URL).
    """
    logger.info(f"Користувач {current_user.email} запитує інформацію про свій аватар.")
    avatar_service = AvatarService(db_session)
    avatar_info = await avatar_service.get_avatar_info_by_user_id(user_id=current_user.id)

    # Якщо аватар не знайдено, сервіс може повернути None.
    # Ендпоінт поверне 200 з null тілом, якщо response_model=Optional[...].
    # Або можна кинути 404, якщо це вважається помилкою.
    if not avatar_info:
        logger.info(f"Аватар для користувача {current_user.email} не знайдено.")
        # Тут можна залишити як є (поверне null) або:
        # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Аватар не встановлено.")
    return avatar_info

@router.get(
    "/{user_id_target}",
    response_model=Optional[UserAvatarSchema],
    tags=["Files", "User Avatars"],
    summary="Отримати інформацію про аватар іншого користувача"
)
async def get_user_avatar_info(
    user_id_target: int = Path(..., description="ID користувача, чий аватар запитується"),
    # current_user: UserModel = Depends(CurrentActiveUser), # Для логування, хто запитує
    db_session: DBSession = Depends()
):
    """
    Повертає інформацію про аватар вказаного користувача.
    Доступ може бути публічним або обмеженим.
    """
    # logger.info(f"Користувач {current_user.email} запитує аватар для користувача ID {user_id_target}.")
    logger.info(f"Запит аватара для користувача ID {user_id_target}.") # Якщо доступ публічний
    avatar_service = AvatarService(db_session)
    avatar_info = await avatar_service.get_avatar_info_by_user_id(user_id=user_id_target)
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
    """
    Видаляє поточний аватар користувача.
    """
    logger.info(f"Користувач {current_user.email} (ID: {current_user.id}) видаляє свій аватар.")
    avatar_service = AvatarService(db_session)
    try:
        success = await avatar_service.delete_avatar_by_user_id(user_id=current_user.id)
        if not success:
            # Можливо, аватар вже був відсутній
            logger.info(f"Аватар для користувача {current_user.email} не знайдено для видалення, або помилка видалення.")
            # Можна повернути 404, якщо аватар не існував, або 204 в будь-якому випадку, якщо мета досягнута (аватара немає)
            # Для простоти, якщо сервіс повертає False при "не знайдено", то 404.
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Аватар не знайдено для видалення.")
        logger.info(f"Аватар для користувача {current_user.email} успішно видалено.")
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка видалення аватара для {current_user.email}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при видаленні аватара.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/files/__init__.py
