# backend/app/src/api/v1/files/avatars.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління аватарами користувачів.

Включає завантаження/оновлення аватара для поточного користувача,
отримання інформації про аватар будь-якого користувача (зазвичай публічно),
та видалення власного аватара.
"""
from typing import Optional
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Path
from sqlalchemy.ext.asyncio import AsyncSession  # Не використовується прямо, якщо сесія в сервісі

# Повні шляхи імпорту
from backend.app.src.api.dependencies import get_api_db_session, get_current_active_user
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.files.avatar import UserAvatarResponse
# from backend.app.src.schemas.files.file import FileRecordResponse # Не використовується прямо тут
from backend.app.src.services.files.user_avatar_service import UserAvatarService
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter(
    # Префікс /avatars буде додано в __init__.py батьківського роутера files
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання UserAvatarService
async def get_user_avatar_service(session: AsyncSession = Depends(get_api_db_session)) -> UserAvatarService:
    """Залежність FastAPI для отримання екземпляра UserAvatarService."""
    return UserAvatarService(db_session=session)


@router.post(
    "/user/me",
    response_model=UserAvatarResponse,
    status_code=status.HTTP_201_CREATED,
    # 201 для нового, 200 для оновленого може бути, але 201 частіше для "встановлення"
    summary="Завантаження або оновлення аватара поточного користувача",  # i18n
    description="Дозволяє поточному аутентифікованому користувачу завантажити або оновити свій аватар."  # i18n
)
async def upload_or_update_my_avatar(
        file: UploadFile = File(...,
                                description="Файл аватара для завантаження (рекомендовано зображення jpeg, png, gif)"),
        # i18n
        current_user: UserModel = Depends(get_current_active_user),
        avatar_service: UserAvatarService = Depends(get_user_avatar_service)
) -> UserAvatarResponse:
    """
    Завантажує та встановлює новий аватар для поточного користувача.
    Якщо аватар вже існує, він замінюється (старий файл може бути видалено, якщо більше не використовується).
    `UserAvatarService` координує збереження файлу (через `FileUploadService`) та створення/оновлення записів.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' завантажує новий аватар: {file.filename} (тип: {file.content_type}, розмір: {file.size}).")

    # TODO: Перевірити file.size та file.content_type тут або в FileUploadService на відповідність обмеженням з settings.
    #  Наприклад, settings.MAX_AVATAR_SIZE_BYTES, settings.ALLOWED_AVATAR_MIME_TYPES.
    #  FileUploadService.initiate_upload вже має таку логіку, але для прямого завантаження тут її можна дублювати або винести в утиліту.

    try:
        # UserAvatarService.set_user_avatar має обробити завантаження файлу, створення FileRecord,
        # та оновлення User.avatar_id або запису UserAvatar.
        # Передаємо `file` (UploadFile) напряму в сервіс.
        avatar_response = await avatar_service.set_user_avatar_file(  # Очікуємо такий метод в сервісі
            user_id=current_user.id,
            uploaded_file=file,
            set_by_user_id=current_user.id  # Для аудиту
        )
        if not avatar_response:  # Малоймовірно, якщо сервіс кидає винятки
            # i18n
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Не вдалося встановити аватар.")

        logger.info(
            f"Аватар для користувача ID '{current_user.id}' успішно встановлено/оновлено. File ID: {avatar_response.file.id if avatar_response.file else 'N/A'}.")
        return avatar_response
    except ValueError as e:  # Помилки валідації з сервісу (неправильний тип файлу, завеликий розмір тощо)
        logger.warning(f"Помилка встановлення аватара для користувача ID '{current_user.id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:  # Якщо з якоїсь причини відмовлено в доступі
        logger.warning(f"Заборона встановлення аватара для ID '{current_user.id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка під час встановлення аватара для ID '{current_user.id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при обробці аватара.")


@router.get(
    "/user/{user_id_target}",  # Змінено user_id на user_id_target
    response_model=Optional[UserAvatarResponse],  # Може бути None, якщо аватар не встановлено
    summary="Отримання інформації про аватар користувача",  # i18n
    description="""Повертає інформацію про активний аватар вказаного користувача (наприклад, URL).
    Цей ендпоінт зазвичай публічно доступний."""  # i18n
    # TODO: Вирішити, чи потрібна автентифікація для цього ендпоінта. Поки що без неї.
)
async def get_user_avatar_info(
        user_id_target: UUID = Path(..., description="ID користувача, чий аватар запитується"),  # i18n
        avatar_service: UserAvatarService = Depends(get_user_avatar_service)
) -> Optional[UserAvatarResponse]:
    """
    Отримує інформацію про активний аватар користувача.
    Аватари зазвичай є публічно доступними.
    """
    logger.debug(f"Запит інформації про аватар для користувача ID: {user_id_target}")
    # UserAvatarService.get_active_user_avatar повертає UserAvatarResponse або None
    avatar_info = await avatar_service.get_active_user_avatar(user_id=user_id_target)

    if not avatar_info:
        logger.info(f"Активний аватар для користувача ID '{user_id_target}' не знайдено.")
        # Не помилка, просто немає аватара. Повертаємо 200 з порожнім тілом або відповідний статус, якщо клієнт очікує.
        # FastAPI автоматично поверне 200 з `null` тілом, якщо response_model=Optional[UserAvatarResponse]
        return None
        # Або, якщо завжди має бути відповідь, навіть порожня:
        # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Аватар для користувача ID {user_id_target} не знайдено.")

    logger.info(f"Інформацію про аватар для користувача ID '{user_id_target}' надано.")
    return avatar_info


@router.delete(
    "/user/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення аватара поточного користувача",  # i18n
    description="Дозволяє поточному аутентифікованому користувачу видалити свій активний аватар."  # i18n
)
async def delete_my_avatar(
        current_user: UserModel = Depends(get_current_active_user),
        avatar_service: UserAvatarService = Depends(get_user_avatar_service)
):
    """
    Видаляє активний аватар поточного користувача.
    Сервіс має обробити деактивацію зв'язку UserAvatar та, можливо, видалення FileRecord
    і самого файлу, якщо він більше не використовується.
    """
    logger.info(f"Користувач ID '{current_user.id}' намагається видалити свій аватар.")
    try:
        # UserAvatarService.delete_user_avatar має обробляти логіку
        success = await avatar_service.deactivate_current_user_avatar(  # Потрібен такий метод в сервісі
            user_id=current_user.id,
            actor_id=current_user.id  # Для аудиту
        )
        if not success:
            # Може означати, що аватара не було, або сталася помилка при видаленні, яку сервіс обробив як False.
            logger.warning(
                f"Не вдалося видалити аватар для користувача ID '{current_user.id}' (сервіс повернув False).")
            # i18n
            # Не кидаємо 404, якщо аватара просто не було, 204 все одно підходить.
            # Якщо була помилка, сервіс мав би кинути виняток.
            # Для узгодженості, якщо сервіс повертає False при "не знайдено", то можна повернути 404.
            # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Аватар не знайдено для видалення.")
    except ValueError as e:  # Якщо сервіс кидає помилки валідації/логіки
        logger.warning(f"Помилка видалення аватара для ID '{current_user.id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:
        logger.warning(f"Заборона видалення аватара для ID '{current_user.id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні аватара для ID '{current_user.id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    # HTTP 204 No Content неявно повертається, якщо немає тіла відповіді
    return None


logger.info(f"Роутер для управління аватарами (`{router.prefix}`) визначено.")
