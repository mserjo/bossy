# backend/app/src/api/v1/files/files.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для загальних операцій з файлами API v1.

Цей модуль може надавати API для:
- Завантаження файлів, не пов'язаних з аватарами (наприклад, іконки груп, нагород, файли до завдань).
- Отримання інформації про ці файли.
- Видалення цих файлів (якщо дозволено відповідними правами).

Конкретні операції та права доступу будуть залежати від типу файлу та контексту.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Path, status, Query, Response as FastAPIResponse
from typing import List, Optional, Annotated

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.files.file import FileSchema, FileUploadResponseSchema
from backend.app.src.services.files.file_service import FileService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.config import settings # Для шляху до файлів

logger = get_logger(__name__)
router = APIRouter()

# Загальні операції з файлами.
# Шляхи будуть відносно префіксу /files, встановленого в v1.router

@router.post(
    "/upload/generic",
    response_model=FileUploadResponseSchema, # Повертає інформацію про завантажений файл
    status_code=status.HTTP_201_CREATED,
    tags=["Files", "General Files"],
    summary="Завантажити загальний файл"
)
async def upload_generic_file_endpoint(
    uploaded_file: Annotated[UploadFile, File(description="Файл для завантаження")],
    # Додаткові параметри для контекстуалізації файлу:
    file_type: Annotated[Optional[str], Query(description="Тип файлу, напр. 'group_icon', 'task_attachment', 'reward_image'")] = None,
    related_entity_id: Annotated[Optional[int], Query(description="ID сутності, до якої кріпиться файл (група, завдання, нагорода)")] = None,
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends(),
):
    """
    Завантажує файл в систему.
    - `file_type`: вказує на призначення файлу.
    - `related_entity_id`: ID сутності, з якою пов'язаний файл.
    Права доступу на завантаження перевіряються в сервісі на основі file_type та related_entity_id.
    """
    logger.info(
        f"Користувач {current_user.email} завантажує файл: {uploaded_file.filename} "
        f"(тип: {file_type}, сутність ID: {related_entity_id})."
    )

    # TODO: Валідація file_type та related_entity_id, якщо вони обов'язкові для певних сценаріїв
    # TODO: Валідація розміру та MIME типу файлу (можна на рівні сервісу)
    # if uploaded_file.content_type not in settings.ALLOWED_FILE_MIME_TYPES:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неприпустимий тип файлу.")
    # if uploaded_file.size > settings.MAX_FILE_SIZE_BYTES:
    #     raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Файл занадто великий.")

    file_service = FileService(db_session)
    try:
        file_record = await file_service.upload_general_file(
            file_data=await uploaded_file.read(),
            filename=uploaded_file.filename,
            content_type=uploaded_file.content_type,
            uploader_id=current_user.id,
            file_type=file_type,
            related_entity_id=related_entity_id
        )
        # Формуємо URL для доступу (приклад, залежить від налаштувань static files)
        # file_url = f"{settings.API_V1_STR}/files/download/{file_record.id}" # Якщо є окремий ендпоінт для скачування
        file_url = request.url_for("download_general_file_endpoint", file_id_or_filename=str(file_record.id)) # Якщо є ендпоінт для скачування
        # Або прямий URL до static, якщо налаштовано:
        # file_url = f"/static/{file_record.path_on_server}"

        return FileUploadResponseSchema(
            id=file_record.id,
            filename=file_record.filename,
            content_type=file_record.content_type,
            size_bytes=file_record.size_bytes,
            url=str(file_url), # Переконуємось, що це рядок
            created_at=file_record.created_at
        )
    except HTTPException as e:
        raise e
    except ValueError as ve: # Наприклад, якщо file_type не підтримується
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"Помилка завантаження файлу {uploaded_file.filename}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при завантаженні файлу.")

# Ендпоінт для отримання/скачування файлу.
# Можна зробити один ендпоінт, який повертає FileResponse,
# або окремий для метаданих (FileSchema) і окремий для скачування.
# Для простоти, зробимо один, що може повертати FileResponse.
# Шлях може бути /files/download/{file_id_or_filename}
@router.get(
    "/download/{file_id_or_filename}",
    # response_model=None, # FileResponse не вказується в response_model
    tags=["Files", "General Files"],
    summary="Завантажити файл за ID або іменем"
)
async def download_general_file_endpoint(
    file_id_or_filename: str = Path(..., description="ID файлу або його унікальне ім'я на сервері"),
    current_user: UserModel = Depends(CurrentActiveUser), # Для перевірки прав доступу
    db_session: DBSession = Depends(),
):
    logger.info(f"Користувач {current_user.email} запитує файл: {file_id_or_filename}.")
    file_service = FileService(db_session)

    try:
        # Сервіс має перевірити права доступу користувача до файлу
        file_path_on_server, filename, media_type = await file_service.get_file_for_download(
            file_identifier=file_id_or_filename,
            requesting_user_id=current_user.id
        )

        if not file_path_on_server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не знайдено або доступ заборонено.")

        from fastapi.responses import FileResponse # Імпортуємо тут, щоб уникнути циклічних залежностей на верхньому рівні
        return FileResponse(path=file_path_on_server, filename=filename, media_type=media_type)

    except HTTPException as e:
        raise e
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не знайдено на сервері.")
    except Exception as e_gen:
        logger.error(f"Помилка при спробі завантаження файлу {file_id_or_filename}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


@router.delete(
    "/{file_id}", # Видалення за ID запису в БД
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Files", "General Files"],
    summary="Видалити загальний файл"
)
async def delete_general_file_endpoint(
    file_id: int = Path(..., description="ID запису файлу для видалення"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends(),
):
    logger.info(f"Користувач {current_user.email} запитує видалення файлу ID: {file_id}.")
    file_service = FileService(db_session)
    try:
        # Сервіс має перевірити, чи користувач має право видаляти цей файл
        # (наприклад, він завантажувач, або адмін сутності, до якої файл прикріплений)
        success = await file_service.delete_general_file(
            file_id=file_id,
            actor_id=current_user.id
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не знайдено або не вдалося видалити.")
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка видалення файлу ID {file_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/files/__init__.py
# з префіксом / (тобто шляхи будуть /files/upload/generic, /files/download/...)
