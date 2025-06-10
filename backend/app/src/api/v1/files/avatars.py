# backend/app/src/api/v1/files/avatars.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user, get_current_active_superuser
from app.src.models.auth import User as UserModel
from app.src.schemas.files.avatar import UserAvatarResponse # Схема для відповіді з інформацією про аватар
from app.src.schemas.files.file import FileRecordResponse # Може повертатися FileRecord як частина UserAvatarResponse
from app.src.services.files.avatar import UserAvatarService # Сервіс для управління аватарами
# FileUploadService може використовуватися непрямо через UserAvatarService

router = APIRouter()

@router.post(
    "/user/me", # Шлях відносно /files/avatars/user/me
    response_model=UserAvatarResponse, # Повертає інформацію про встановлений аватар
    status_code=status.HTTP_201_CREATED,
    summary="Завантаження/оновлення аватара поточного користувача",
    description="Дозволяє поточному аутентифікованому користувачу завантажити або оновити свій аватар."
)
async def upload_or_update_my_avatar(
    file: UploadFile = File(..., description="Файл аватара для завантаження (наприклад, зображення jpeg, png)"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    avatar_service: UserAvatarService = Depends()
):
    '''
    Завантажує та встановлює новий аватар для поточного користувача.
    Якщо аватар вже існує, він може бути замінений.
    Сервіс `UserAvatarService` може використовувати `FileUploadService` для збереження файлу,
    а потім пов'язувати `FileRecord` з профілем користувача.
    '''
    if not hasattr(avatar_service, 'db_session') or avatar_service.db_session is None:
        avatar_service.db_session = db

    try:
        avatar_info = await avatar_service.set_user_avatar(
            user_id=current_user.id,
            uploaded_file=file,
            requesting_user=current_user # Для перевірки прав, хоча тут це сам користувач
        )
    except HTTPException as e:
        raise e # Перекидаємо специфічні помилки від сервісу (неправильний тип файлу, завеликий розмір)
    except Exception as e:
        # Логування помилки e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка під час встановлення аватара: {str(e)}"
        )

    if not avatar_info: # Малоймовірно, якщо сервіс кидає винятки
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не вдалося встановити аватар.")

    return UserAvatarResponse.model_validate(avatar_info)


@router.get(
    "/user/{user_id}", # Шлях відносно /files/avatars/user/{user_id}
    response_model=UserAvatarResponse, # Або просто URL аватара у вигляді рядка/RedirectResponse
    summary="Отримання інформації про аватар користувача",
    description="Повертає інформацію про аватар вказаного користувача (наприклад, URL)."
)
async def get_user_avatar_info(
    user_id: int = Path(..., description="ID користувача, чий аватар запитується"),
    db: AsyncSession = Depends(get_db_session),
    # current_user: UserModel = Depends(get_current_active_user), # Для перевірки, чи має право бачити (зазвичай публічно)
    avatar_service: UserAvatarService = Depends()
):
    '''
    Отримує інформацію про аватар користувача.
    Аватари зазвичай є публічно доступними або доступними для всіх аутентифікованих користувачів.
    '''
    if not hasattr(avatar_service, 'db_session') or avatar_service.db_session is None:
        avatar_service.db_session = db

    avatar_info = await avatar_service.get_user_avatar_info(user_id=user_id)
    if not avatar_info or not avatar_info.avatar_url: # Перевіряємо, чи є URL
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Аватар для користувача ID {user_id} не знайдено.")

    return UserAvatarResponse.model_validate(avatar_info)
    # Альтернативно, якщо потрібно просто перенаправити на URL файлу:
    # from fastapi.responses import RedirectResponse
    # if not avatar_info or not avatar_info.avatar_url:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Аватар для користувача ID {user_id} не знайдено.")
    # return RedirectResponse(url=avatar_info.avatar_url, status_code=status.HTTP_302_FOUND)


@router.delete(
    "/user/me", # Шлях відносно /files/avatars/user/me
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення аватара поточного користувача",
    description="Дозволяє поточному аутентифікованому користувачу видалити свій аватар."
)
async def delete_my_avatar(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    avatar_service: UserAvatarService = Depends()
):
    '''
    Видаляє аватар поточного користувача.
    Сервіс має обробити видалення зв'язку та, можливо, самого файлу, якщо він більше не використовується.
    '''
    if not hasattr(avatar_service, 'db_session') or avatar_service.db_session is None:
        avatar_service.db_session = db

    success = await avatar_service.delete_user_avatar(
        user_id=current_user.id,
        requesting_user=current_user
    )
    if not success:
        # Може означати, що аватара не було, або сталася помилка при видаленні
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Або 500, якщо була помилка видалення
            detail="Не вдалося видалити аватар. Можливо, він не був встановлений."
        )
    # HTTP 204 No Content

# Міркування:
# 1.  Спеціалізація: Цей роутер спеціалізується на аватарах користувачів.
# 2.  Сервіс `UserAvatarService`:
#     - Використовує `FileUploadService` для завантаження файлу (з призначенням 'avatar').
#     - Оновлює посилання на аватар у профілі користувача (`UserModel.avatar_file_id` або подібне поле).
#     - Обробляє видалення старого файлу аватара, якщо він замінюється.
#     - Надає URL для доступу до аватара.
# 3.  Схеми: `UserAvatarResponse` (може містити URL аватара, ID файлу, тощо).
# 4.  Права доступу: Користувачі керують своїми аватарами. Перегляд аватарів інших користувачів зазвичай дозволений.
# 5.  URL-и: Цей роутер буде підключений до `files_router` з префіксом `/avatars`.
#     Шляхи будуть `/api/v1/files/avatars/user/me`, `/api/v1/files/avatars/user/{user_id}`.
# 6.  GET аватар: Ендпоінт GET може повертати метадані (включаючи URL) або робити Redirect на сам файл.
#     Повернення метаданих (UserAvatarResponse) є більш гнучким для клієнта.
# 7.  Коментарі: Українською мовою.
