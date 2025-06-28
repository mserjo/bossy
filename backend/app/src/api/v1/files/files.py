# backend/app/src/api/v1/files/files.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для загальних операцій з файлами API v1.

Цей модуль може надавати API для:
- Завантаження файлів, не пов'язаних з аватарами (наприклад, іконки груп, нагород, файли до завдань).
- Отримання інформації про ці файли.
- Завантаження (скачування) цих файлів.
- Видалення цих файлів (якщо дозволено відповідними правами).

Конкретні операції та права доступу будуть залежати від типу файлу та контексту.
"""

from fastapi import (
    APIRouter, Depends, UploadFile, File, Path, Query, status, HTTPException, Response as FastAPIResponse, Request
)
from typing import List, Optional, Annotated

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.files.file import FileSchema, FileUploadResponseSchema
from backend.app.src.services.files.file_service import FileService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.config import settings

logger = get_logger(__name__)
router = APIRouter()

# Загальні операції з файлами.
# Шляхи будуть відносно префіксу /files, встановленого в v1.router

@router.post(
    "/upload/generic",
    response_model=FileUploadResponseSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Files", "General Files"],
    summary="Завантажити загальний файл"
)
async def upload_generic_file_endpoint(
    request: Request, # Додано для генерації URL
    uploaded_file: Annotated[UploadFile, File(description="Файл для завантаження")],
    file_type: Annotated[Optional[str], Query(description="Тип файлу, напр. 'group_icon', 'task_attachment', 'reward_image'")] = None,
    related_entity_id: Annotated[Optional[int], Query(description="ID сутності, до якої кріпиться файл (група, завдання, нагорода)")] = None,
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends(),
):
    logger.info(
        f"Користувач {current_user.email} завантажує файл: {uploaded_file.filename} "
        f"(тип: {file_type}, сутність ID: {related_entity_id}). Розмір: {uploaded_file.size}, Тип MIME: {uploaded_file.content_type}"
    )

    if uploaded_file.content_type not in settings.ALLOWED_FILE_MIME_TYPES:
        logger.warning(f"Неприпустимий тип файлу {uploaded_file.content_type} від {current_user.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Неприпустимий тип файлу: {uploaded_file.content_type}. Дозволені: {', '.join(settings.ALLOWED_FILE_MIME_TYPES)}")

    if uploaded_file.size > settings.MAX_FILE_SIZE_BYTES:
        logger.warning(f"Файл {uploaded_file.filename} занадто великий ({uploaded_file.size} байт) від {current_user.email}")
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"Файл занадто великий. Максимальний розмір: {settings.MAX_FILE_SIZE_BYTES // 1024 // 1024}MB.")

    file_service = FileService(db_session)
    try:
        file_data_content = await uploaded_file.read()
        # Перевірка розміру ще раз після читання, якщо uploaded_file.size не завжди надійний до read()
        if len(file_data_content) > settings.MAX_FILE_SIZE_BYTES:
            logger.warning(f"Файл {uploaded_file.filename} занадто великий ({len(file_data_content)} байт) після читання від {current_user.email}")
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"Файл занадто великий. Максимальний розмір: {settings.MAX_FILE_SIZE_BYTES // 1024 // 1024}MB.")

        file_record = await file_service.upload_general_file(
            file_data=file_data_content,
            filename=uploaded_file.filename,
            content_type=uploaded_file.content_type,
            uploader_id=current_user.id,
            file_type=file_type,
            related_entity_id=related_entity_id,
            file_size=len(file_data_content)
        )

        try:
            # Генерація URL через request.url_for
            # Ім'я ендпоінта має відповідати імені функції download_general_file_endpoint
            file_url = str(request.url_for('download_general_file_endpoint', file_id_or_filename=str(file_record.id)))
        except Exception as url_exc:
            logger.warning(f"Не вдалося згенерувати URL для файлу {file_record.id} через url_for: {url_exc}. Використовується статичний шлях.")
            # Запасний варіант, якщо url_for не спрацює (наприклад, поза контекстом запиту в тестах)
            # Або якщо файли роздаються через static mount напряму
            file_url = f"{settings.STATIC_FILES_URL_PREFIX}{file_record.path_on_server}" # Припускаючи, що path_on_server - відносний шлях

        return FileUploadResponseSchema(
            id=file_record.id,
            filename=file_record.filename,
            content_type=file_record.content_type,
            size_bytes=file_record.size_bytes,
            url=file_url,
            created_at=file_record.created_at
        )
    except HTTPException as e:
        raise e
    except ValueError as ve:
        logger.warning(f"Помилка валідації при завантаженні файлу {uploaded_file.filename}: {str(ve)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"Помилка завантаження файлу {uploaded_file.filename}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при завантаженні файлу.")

@router.get(
    "/download/{file_id_or_filename:path}", # :path дозволяє слєші в імені файлу, якщо це шлях
    tags=["Files", "General Files"],
    summary="Завантажити файл за ID або відносним шляхом"
    # response_class=FileResponse # FileResponse не вказується в response_model, а повертається напряму
)
async def download_general_file_endpoint(
    file_id_or_filename: str = Path(..., description="ID файлу або його відносний шлях на сервері"),
    # current_user: UserModel = Depends(CurrentActiveUser), # Розкоментувати, якщо потрібна автентифікація для скачування
    db_session: DBSession = Depends(),
):
    # logger.info(f"Користувач {current_user.email if current_user else 'Анонім'} запитує файл: {file_id_or_filename}.")
    logger.info(f"Запит на завантаження файлу: {file_id_or_filename}.")
    file_service = FileService(db_session)
    try:
        # requesting_user_id = current_user.id if current_user else None
        # Сервіс має перевірити права доступу користувача до файлу, якщо current_user передається
        file_path_on_storage, actual_filename, media_type = await file_service.get_file_for_download(
            file_identifier=file_id_or_filename,
            # requesting_user_id=requesting_user_id # Передати для перевірки прав, якщо потрібно
        )

        if not file_path_on_storage: # Сервіс повертає None, якщо файл не знайдено або доступ заборонено
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не знайдено або доступ заборонено.")

        from fastapi.responses import FileResponse
        return FileResponse(path=file_path_on_storage, filename=actual_filename, media_type=media_type)

    except HTTPException as e:
        raise e
    except FileNotFoundError: # Якщо сервіс кидає FileNotFoundError
        logger.warning(f"Файл {file_id_or_filename} не знайдено на сервері.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не знайдено на сервері.")
    except Exception as e_gen:
        logger.error(f"Помилка при спробі завантаження файлу {file_id_or_filename}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при завантаженні файлу.")


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Files", "General Files"],
    summary="Видалити загальний файл"
)
async def delete_general_file_endpoint(
    file_id: int = Path(..., description="ID запису файлу для видалення"),
    current_user: UserModel = Depends(CurrentActiveUser), # Потрібен для перевірки прав
    db_session: DBSession = Depends(),
):
    logger.info(f"Користувач {current_user.email} запитує видалення файлу ID: {file_id}.")
    file_service = FileService(db_session)
    try:
        success = await file_service.delete_general_file(
            file_id=file_id,
            actor_id=current_user.id
        )
        if not success: # Сервіс може повернути False, якщо файл не знайдено або немає прав
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не знайдено або не вдалося видалити (перевірте права).")
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка видалення файлу ID {file_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при видаленні файлу.")

    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)
