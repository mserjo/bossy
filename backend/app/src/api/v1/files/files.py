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

from fastapi import APIRouter, Depends, UploadFile, File, Path, status
from typing import List, Optional

from backend.app.src.config.logging import get_logger
# TODO: Імпортувати схеми (наприклад, FileRecordSchema, FileUploadResponseSchema)
# TODO: Імпортувати FileService
# TODO: Імпортувати залежності (DBSession, CurrentActiveUser, перевірки прав для конкретних дій)

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти можуть мати префікс /files або більш специфічні, наприклад,
# /groups/{group_id}/icons, /tasks/{task_id}/attachments тощо.
# Для загального файлу `files.py` можна зробити більш загальний ендпоінт,
# якщо FileService буде обробляти контекст (до чого відноситься файл).

@router.post(
    "/upload", # Можливо, потрібен більш конкретний шлях або параметри для визначення типу файлу
    # response_model=FileSchema, # Або спеціальна схема відповіді
    status_code=status.HTTP_201_CREATED,
    tags=["Files", "General Files"],
    summary="Завантажити загальний файл (заглушка)"
)
async def upload_general_file(
    # file_type: str = Query(..., description="Тип файлу, напр. 'group_icon', 'task_attachment'"),
    # related_entity_id: Optional[int] = Query(None, description="ID сутності, до якої кріпиться файл"),
    # current_user: UserModel = Depends(CurrentActiveUser), # Перевірка прав на завантаження
    # db_session: DBSession = Depends(),
    uploaded_file: UploadFile = File(...)
):
    """
    Завантажує файл в систему. Тип файлу та його приналежність
    мають визначатися додатковими параметрами або логікою сервісу.
    """
    logger.info(f"Запит на завантаження загального файлу: {uploaded_file.filename} (заглушка).")
    # TODO: Реалізувати логіку збереження файлу через FileService.
    # Перевірити права користувача на завантаження файлу даного типу для даної сутності.
    # Валідація типу файлу, розміру.
    return {
        "file_id": "file_xyz789",
        "filename": uploaded_file.filename,
        "content_type": uploaded_file.content_type,
        "url": f"/static/uploads/general/{uploaded_file.filename}", # Приклад URL
        "message": "Файл успішно завантажено (заглушка)."
    }

@router.get(
    "/{file_id}",
    # response_model=FileSchema, # Або FileResponse для прямої віддачі файлу
    tags=["Files", "General Files"],
    summary="Отримати інформацію про файл або сам файл (заглушка)"
)
async def get_general_file_info_or_download(
    file_id: str # Або int
    # current_user: UserModel = Depends(CurrentActiveUser), # Перевірка прав на доступ
    # db_session: DBSession = Depends(),
):
    logger.info(f"Запит інформації/файлу ID: {file_id} (заглушка).")
    # TODO: Реалізувати логіку отримання інформації про файл або самого файлу.
    # Якщо повертати сам файл, використовувати FileResponse.
    # Перевірити права доступу.
    return {"file_id": file_id, "filename": "example_document.pdf", "url": f"/static/uploads/general/example_document.pdf"}


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Files", "General Files"],
    summary="Видалити загальний файл (заглушка)"
)
async def delete_general_file(
    file_id: str # Або int
    # current_user: UserModel = Depends(CurrentActiveUser), # Перевірка прав на видалення
    # db_session: DBSession = Depends(),
):
    logger.info(f"Запит на видалення файлу ID: {file_id} (заглушка).")
    # TODO: Реалізувати логіку видалення файлу та запису в БД.
    # Перевірити права.
    return

# Роутер буде підключений в backend/app/src/api/v1/files/__init__.py
