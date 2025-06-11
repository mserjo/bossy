# backend/app/src/api/v1/files/uploads.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для процесу завантаження файлів.

Включає ініціалізацію завантаження, передачу даних файлу (можливо, частинами)
та завершення завантаження зі створенням запису про файл.
"""
from typing import Optional, Dict, Any  # List не використовується
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession  # Не використовується прямо, якщо сесія в сервісі

# Повні шляхи імпорту
from backend.app.src.api.dependencies import get_api_db_session, get_current_active_user
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.files.upload import (
    FileUploadInitiateRequest,
    FileUploadInitiateResponse,
    FileUploadCompleteRequest,
    FileUploadResponse,
    FileDataUploadResponse  # Додано для відповіді на завантаження даних
)
from backend.app.src.services.files.file_upload_service import FileUploadService
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter(
    # Префікс /uploads буде додано в __init__.py батьківського роутера files
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання FileUploadService
async def get_file_upload_service(session: AsyncSession = Depends(get_api_db_session)) -> FileUploadService:
    """Залежність FastAPI для отримання екземпляра FileUploadService."""
    # FileUploadService.__init__ був змінений, щоб приймати db_session опціонально.
    # Якщо FileUploadService потребує db_session для FileRecordService, він має бути переданий.
    return FileUploadService(db_session=session)


@router.post(
    "/initiate",
    response_model=FileUploadInitiateResponse,
    status_code=status.HTTP_200_OK,  # Зазвичай 200 для ініціації, а не 201
    summary="Ініціалізація сесії завантаження файлу",  # i18n
    description="""Починає сесію завантаження файлу, перевіряє метадані (розмір, тип MIME).
    Повертає `upload_id` для використання при завантаженні даних файлу."""  # i18n
)
async def initiate_file_upload(
        initiate_data: FileUploadInitiateRequest,  # Включає file_name, mime_type, size_bytes
        current_user: UserModel = Depends(get_current_active_user),
        upload_service: FileUploadService = Depends(get_file_upload_service)
) -> FileUploadInitiateResponse:
    """
    Ініціює сесію завантаження файлу.
    Перевіряє обмеження на розмір та тип файлу.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' ініціює завантаження: {initiate_data.file_name} ({initiate_data.mime_type}, {initiate_data.size_bytes} байт).")
    try:
        response = await upload_service.initiate_upload(
            initiate_data=initiate_data,
            uploader_user_id=current_user.id
        )
        return response
    except ValueError as e:
        logger.warning(f"Помилка ініціалізації завантаження для '{initiate_data.file_name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при ініціалізації завантаження: {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.post(
    "/data/{upload_id}",
    response_model=FileDataUploadResponse,  # Спеціальна відповідь для завантаження даних
    summary="Завантаження даних файлу (або його частини)",  # i18n
    description="""Завантажує дані файлу (або частину файлу, якщо це чанкінг) для раніше ініційованої сесії.
    Використовує `upload_id`, отриманий від ендпоінта `/initiate`."""  # i18n
)
async def upload_file_data_chunk(
        upload_id: UUID = Path(..., description="ID сесії завантаження, отриманий від /initiate"),  # i18n
        file_name: str = Form(..., description="Оригінальне ім'я файлу (має співпадати з тим, що в /initiate)"),  # i18n
        file_data: UploadFile = File(..., description="Дані файлу (або частина файлу)"),  # i18n
        is_last_chunk: bool = Form(True, description="Прапорець, чи це остання частина файлу"),  # i18n
        chunk_number: Optional[int] = Form(None,
                                           description="Порядковий номер частини (якщо файл ділиться на частини)"),
        # i18n
        current_user: UserModel = Depends(get_current_active_user),
        # Перевірка, що користувач той самий, що ініціював (опціонально)
        upload_service: FileUploadService = Depends(get_file_upload_service)
) -> FileDataUploadResponse:
    """
    Обробляє завантаження даних файлу або його частини.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' завантажує дані для ID '{upload_id}', файл '{file_name}', чанк: {chunk_number}, останній: {is_last_chunk}.")

    # TODO: Перевірити, чи поточний користувач є тим, хто ініціював `upload_id`, якщо це потрібно для безпеки.
    #  Це може вимагати збереження `uploader_user_id` разом з `upload_id` в кеші або тимчасовій БД.

    try:
        async with file_data.open("rb") as f:  # Відкриваємо UploadFile в бінарному режимі для читання
            chunk_bytes = await f.read()

        response_dict = await upload_service.handle_file_data_upload(
            upload_id=upload_id,
            file_name=file_name,  # Передаємо ім'я файлу для збереження в тимчасовій директорії
            file_data_chunk=chunk_bytes,
            is_last_chunk=is_last_chunk,
            chunk_number=chunk_number
        )
        return FileDataUploadResponse(**response_dict)
    except ValueError as e:  # Наприклад, якщо upload_id не знайдено, або помилка запису
        logger.warning(f"Помилка завантаження даних для ID '{upload_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при завантаженні даних файлу для ID '{upload_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при обробці файлу.")


@router.post(
    "/complete/{upload_id}",
    response_model=FileUploadResponse,  # Містить FileRecordResponse та повідомлення
    status_code=status.HTTP_201_CREATED,  # Файл остаточно створено
    summary="Завершення сесії завантаження файлу",  # i18n
    description="""Підтверджує завершення завантаження файлу для вказаної сесії.
    Файл переміщується в постійне сховище, створюється запис FileRecord."""  # i18n
)
async def complete_file_upload(
        upload_id: UUID = Path(..., description="ID сесії завантаження"),  # i18n
        completion_data: FileUploadCompleteRequest,
        # Містить фінальні метадані: file_name, mime_type, size_bytes, group_id, entity_type, entity_id
        current_user: UserModel = Depends(get_current_active_user),
        upload_service: FileUploadService = Depends(get_file_upload_service)
) -> FileUploadResponse:
    """
    Завершує процес завантаження файлу.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' завершує завантаження для ID '{upload_id}'. Дані: {completion_data.model_dump_minimal()}")

    # TODO: Знову ж таки, перевірка, чи поточний користувач той, хто ініціював `upload_id`.

    try:
        file_upload_response = await upload_service.complete_upload(
            upload_id=upload_id,
            completion_data=completion_data,
            uploader_user_id=current_user.id
        )
        return file_upload_response
    except ValueError as e:  # Наприклад, тимчасовий файл не знайдено, помилка створення FileRecord
        logger.warning(f"Помилка завершення завантаження для ID '{upload_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при завершенні завантаження ID '{upload_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при фіналізації файлу.")


logger.info(f"Роутер для завантаження файлів (`{router.prefix}`) визначено.")
