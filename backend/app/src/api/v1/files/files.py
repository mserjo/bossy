# backend/app/src/api/v1/files/files.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user, get_current_active_superuser
from app.src.models.auth import User as UserModel
# from app.src.models.files import FileRecord as FileRecordModel # Потрібна модель FileRecord
from app.src.schemas.files.file import FileRecordResponse # Схема для відповіді з інформацією про файл
from app.src.services.files.file_record import FileRecordService # Сервіс для роботи з FileRecord

router = APIRouter()

@router.get(
    "/{file_id}", # Шлях відносно /files/ (якщо цей роутер підключається без префіксу до files_router)
    response_model=FileRecordResponse,
    summary="Отримання метаданих файлу за ID",
    description="Повертає метадані про конкретний файл (`FileRecord`), що зберігається в системі. Доступ може бути обмежений."
)
async def get_file_record_details(
    file_id: int = Path(..., description="ID запису файлу (FileRecord)"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Для перевірки прав доступу
    file_record_service: FileRecordService = Depends()
):
    '''
    Отримує метадані файлу (`FileRecord`).
    Сервіс `FileRecordService` має перевірити, чи має поточний користувач право
    переглядати інформацію про цей файл (наприклад, чи він власник, чи файл пов'язаний з його групою,
    чи користувач є адміністратором).
    '''
    if not hasattr(file_record_service, 'db_session') or file_record_service.db_session is None:
        file_record_service.db_session = db

    file_record = await file_record_service.get_file_record_by_id(
        file_id=file_id,
        requesting_user=current_user
    )
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Запис файлу з ID {file_id} не знайдено або доступ заборонено."
        )
    return FileRecordResponse.model_validate(file_record)

@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення файлу та його запису (Адмін/Суперюзер)",
    description="Дозволяє адміністратору або суперюзеру видалити файл та відповідний запис `FileRecord` з системи. Може бути дозволено власнику, якщо файл не використовується."
)
async def delete_file_record_and_file(
    file_id: int = Path(..., description="ID запису файлу (FileRecord), який видаляється"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін, суперюзер, або власник
    file_record_service: FileRecordService = Depends()
):
    '''
    Видаляє запис `FileRecord` та пов'язаний з ним фізичний файл.
    Сервіс `FileRecordService` має перевірити права на видалення:
    - Чи є користувач адміністратором/суперюзером?
    - Чи є користувач власником файлу І чи файл більше ніде не використовується (наприклад, як аватар, вкладення)?
    Видалення файлів, що використовуються, може бути заборонено або вимагати спеціальних прав.
    '''
    if not hasattr(file_record_service, 'db_session') or file_record_service.db_session is None:
        file_record_service.db_session = db

    success = await file_record_service.delete_file_record_and_file(
        file_id=file_id,
        requesting_user=current_user
    )
    if not success:
        # Сервіс має кидати відповідні HTTPException (403, 404, 409 Conflict якщо файл використовується)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Або інший відповідний код
            detail=f"Не вдалося видалити файл з ID {file_id}. Можливо, його не існує, у вас немає прав, або файл використовується."
        )
    # HTTP 204 No Content

# Міркування:
# 1.  Призначення: Цей роутер для загальних операцій з `FileRecord`.
#     Специфічні операції (завантаження, керування аватарами) знаходяться в інших файлах цього модуля.
# 2.  Сервіс `FileRecordService`:
#     - `get_file_record_by_id`: Отримує метадані, перевіряє права доступу.
#     - `delete_file_record_and_file`: Видаляє запис з БД та фізичний файл. Включає складну логіку перевірки прав
#       та перевірку, чи файл не використовується іншими сутностями.
# 3.  Права доступу:
#     - Перегляд метаданих: Залежить від контексту (власник, доступ до пов'язаного об'єкта, адмін).
#     - Видалення: Зазвичай адміністратори/суперюзери. Власники можуть мати обмежені права на видалення.
# 4.  URL-и: Цей роутер може бути підключений до `files_router` без префіксу, якщо `files_router`
#     вже має префікс `/files`. Тоді шляхи будуть `/api/v1/files/{file_id}`.
# 5.  Коментарі: Українською мовою.
# 6.  Безпека: Видалення файлів - чутлива операція. Потрібна ретельна перевірка прав та використання файлу.
