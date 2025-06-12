# backend/app/src/api/v1/files/files.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для загального управління записами файлів (FileRecord).

Дозволяє отримувати метадані файлів та видаляти файли разом із їх записами
(зазвичай адміністративні дії або для власників файлів з обмеженнями).
"""
from typing import List, Optional  # Generic, TypeVar, BaseModel не потрібні, якщо імпортуються з core
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession  # Не використовується прямо, якщо сесія в сервісі

# Повні шляхи імпорту
from backend.app.src.api.dependencies import get_api_db_session, get_current_active_user, get_current_active_superuser, \
    paginator
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.files.file import FileRecordResponse
from backend.app.src.core.pagination import PagedResponse, PageParams  # Для пагінації
from backend.app.src.services.files.file_record_service import FileRecordService
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter(
    # Префікс не встановлюється тут, буде успадковано /files від батьківського роутера в files/__init__.py
    # Теги також успадковуються
)


# Залежність для отримання FileRecordService
async def get_file_record_service(session: AsyncSession = Depends(get_api_db_session)) -> FileRecordService:
    """Залежність FastAPI для отримання екземпляра FileRecordService."""
    return FileRecordService(db_session=session)


# TODO: Реалізувати більш гранульовані залежності для перевірки прав доступу до файлів, наприклад:
# async def require_file_record_viewer(file_id: UUID = Path(...), current_user: UserModel = Depends(get_current_active_user), ...): ...
# async def require_file_record_editor(file_id: UUID = Path(...), current_user: UserModel = Depends(get_current_active_user), ...): ...

@router.get(
    "/{file_id}",
    response_model=FileRecordResponse,
    summary="Отримання метаданих файлу за ID",  # i18n
    description="""Повертає метадані про конкретний файл (`FileRecord`).
    Доступ може бути обмежений залежно від прав користувача та контексту файлу."""  # i18n
    # dependencies=[Depends(require_file_record_viewer)] # TODO
)
async def get_file_record_details(
        file_id: UUID = Path(..., description="ID запису файлу (FileRecord)"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),  # Для перевірки прав у сервісі
        file_record_service: FileRecordService = Depends(get_file_record_service)
) -> FileRecordResponse:
    """
    Отримує метадані файлу (`FileRecord`).
    Сервіс `FileRecordService` має перевірити, чи має поточний користувач право
    переглядати інформацію про цей файл.
    """
    logger.debug(f"Користувач ID '{current_user.id}' запитує метадані файлу ID '{file_id}'.")
    # FileRecordService.get_file_record_by_id_for_user має перевіряти права
    # або цей ендпоінт має бути захищений більш специфічною залежністю.
    # TODO: Уточнити логіку прав доступу в сервісі або через залежність.
    file_record = await file_record_service.get_file_record_by_id_for_user(  # Потрібен такий метод в сервісі
        file_id=file_id,
        requesting_user_id=current_user.id,
        is_superuser=current_user.is_superuser
    )
    if not file_record:
        logger.warning(
            f"Запис файлу з ID '{file_id}' не знайдено або доступ для користувача ID '{current_user.id}' заборонено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Запис файлу не знайдено або доступ заборонено.")
    return file_record  # Сервіс вже повертає Pydantic схему


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення файлу та його запису (Адмін/Суперюзер/Власник)",  # i18n
    description="""Дозволяє авторизованому користувачу (суперюзер, адміністратор групи файлу, або власник,
    якщо файл не використовується критично) видалити файл та відповідний запис `FileRecord`."""  # i18n
    # dependencies=[Depends(require_file_record_editor)] # TODO
)
async def delete_file_record_and_file(
        file_id: UUID = Path(..., description="ID запису файлу (FileRecord), який видаляється"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),  # Для перевірки прав
        file_record_service: FileRecordService = Depends(get_file_record_service)
):
    """
    Видаляє запис `FileRecord` та пов'язаний з ним фізичний файл.
    Сервіс `FileRecordService` має перевірити права на видалення.
    """
    logger.info(f"Користувач ID '{current_user.id}' намагається видалити файл та запис ID '{file_id}'.")
    try:
        # FileRecordService.delete_file_record має обробляти права та видалення файлу зі сховища
        success = await file_record_service.delete_file_record_with_permission_check(  # Потрібен такий метод
            file_id=file_id,
            requesting_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            delete_from_storage=True
        )
        if not success:
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Не вдалося видалити файл. Можливо, його не існує, у вас немає прав, або файл використовується.")
    except ValueError as e:  # Специфічні бізнес-помилки від сервісу
        logger.warning(f"Помилка видалення файлу ID '{file_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:
        logger.warning(f"Заборона видалення файлу ID '{file_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні файлу ID '{file_id}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    return None  # HTTP 204 No Content


@router.get(
    "/",
    response_model=PagedResponse[FileRecordResponse],
    summary="Список всіх записів файлів (Суперюзер)",  # i18n
    description="Повертає сторінковий список всіх записів файлів у системі. Доступно тільки суперкористувачам.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def list_all_file_records_admin(  # Перейменовано для ясності
        page_params: PageParams = Depends(paginator),
        # TODO: Додати фільтри: user_id, group_id, entity_type, entity_id, mime_type_pattern
        uploader_user_id: Optional[UUID] = Query(None, description="Фільтр за ID користувача, що завантажив файл"),
        # i18n
        group_id: Optional[UUID] = Query(None, description="Фільтр за ID групи, до якої належить файл"),  # i18n
        entity_type: Optional[str] = Query(None, description="Фільтр за типом пов'язаної сутності"),  # i18n
        mime_type_pattern: Optional[str] = Query(None, description="Фільтр за MIME-типом (наприклад, 'image/%')"),
        # i18n
        file_record_service: FileRecordService = Depends(get_file_record_service),
        # current_superuser: UserModel = Depends(get_current_active_superuser) # Вже в router.dependencies
) -> PagedResponse[FileRecordResponse]:
    """
    Отримує список всіх записів файлів з пагінацією.
    Доступно тільки суперкористувачам.
    """
    logger.info(f"Суперюзер запитує список всіх записів файлів: сторінка {page_params.page}, розмір {page_params.size}")
    # FileRecordService.list_file_records_paginated має повертати (items, total_count)
    records_orm, total_records = await file_record_service.list_all_file_records_paginated(
        skip=page_params.skip,
        limit=page_params.limit,
        uploader_user_id=uploader_user_id,
        group_id=group_id,
        entity_type=entity_type,
        mime_type_pattern=mime_type_pattern
        # TODO: Додати інші фільтри та сортування
    )
    return PagedResponse[FileRecordResponse](
        total=total_records,
        page=page_params.page,
        size=page_params.size,
        results=[FileRecordResponse.model_validate(rec) for rec in records_orm]  # Pydantic v2
    )


logger.info(f"Роутер для загальних операцій з файлами (`{router.prefix}`) визначено.")
