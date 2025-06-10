# backend/app/src/api/v1/files/uploads.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user
from app.src.models.auth import User as UserModel
# from app.src.models.files import FileRecord as FileRecordModel # Потрібна модель FileRecord
from app.src.schemas.files.file import FileRecordResponse # Схема для відповіді з інформацією про файл
from app.src.schemas.files.upload import FileUploadResponse # Може містити FileRecordResponse та URL
from app.src.services.files.upload import FileUploadService # Сервіс для завантаження файлів

router = APIRouter()

@router.post(
    "/", # Шлях відносно /files/uploads/
    response_model=FileUploadResponse, # Або FileRecordResponse, якщо URL не повертається одразу
    status_code=status.HTTP_201_CREATED,
    summary="Завантаження файлу",
    description="""Завантажує файл на сервер.
    Дозволяє передавати додаткові метадані, такі як 'upload_purpose' (наприклад, 'avatar', 'group_icon', 'task_attachment')
    та 'related_item_id' (ID користувача, групи, задачі тощо)."""
)
async def upload_file(
    file: UploadFile = File(..., description="Файл для завантаження"),
    upload_purpose: Optional[str] = Form(None, description="Призначення завантаження (наприклад, 'avatar', 'group_icon')"),
    related_item_id: Optional[int] = Form(None, description="ID пов'язаного об'єкта (користувача, групи тощо)"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    upload_service: FileUploadService = Depends()
):
    '''
    Обробляє завантаження файлу.
    - `file`: Об'єкт UploadFile.
    - `upload_purpose`: Опціональний рядок, що вказує на мету завантаження.
    - `related_item_id`: Опціональний ID об'єкта, до якого прив'язується файл.

    Сервіс `FileUploadService` відповідає за:
    - Валідацію файлу (розмір, тип MIME).
    - Збереження файлу (локально або в хмарне сховище).
    - Створення запису `FileRecord` в базі даних.
    - Повернення інформації про завантажений файл, включаючи URL для доступу (якщо застосовно).
    '''
    if not hasattr(upload_service, 'db_session') or upload_service.db_session is None:
        upload_service.db_session = db

    # Перевірка прав на завантаження для конкретної мети/об'єкта може бути в сервісі
    # на основі current_user, upload_purpose та related_item_id.

    try:
        file_record = await upload_service.handle_file_upload(
            uploaded_file=file,
            requesting_user=current_user,
            purpose=upload_purpose,
            related_id=related_item_id
        )
    except HTTPException as e:
        # Якщо сервіс кидає специфічні HTTPException (наприклад, файл завеликий, не той тип)
        raise e
    except Exception as e:
        # Логування помилки e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка під час завантаження файлу: {str(e)}"
        )

    if not file_record: # Малоймовірно, якщо сервіс кидає винятки, але для повноти
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося обробити завантажений файл."
        )

    # Припускаємо, що file_record, який повертає сервіс, вже є Pydantic схемою FileUploadResponse
    # або може бути нею валідований.
    return FileUploadResponse.model_validate(file_record)

# Міркування:
# 1.  `UploadFile`: FastAPI використовує `python-multipart` для обробки завантаження файлів.
# 2.  Метадані: `upload_purpose` та `related_item_id` передаються як дані форми (`Form`).
#     Це дозволяє серверу зрозуміти контекст завантаження.
# 3.  Сервіс `FileUploadService`: Відповідає за основну логіку:
#     - Валідація (розмір, тип). За `technical_task.txt` - аватари, іконки.
#     - Збереження файлу (локально, як зазначено в `technical_task.txt`). Шлях до збереження має бути налаштовуваним.
#     - Створення запису `FileRecord` в БД (зберігає метадані: оригінальне ім'я, ім'я на диску, тип, розмір, user_id, group_id тощо).
#     - Повернення відповіді, що містить інформацію про файл, можливо, URL для доступу.
# 4.  Схеми: `FileUploadResponse` (може включати `file_id`, `filename`, `content_type`, `size`, `url`).
#     `FileRecordResponse` (схема для моделі `FileRecord`).
# 5.  Права доступу: Будь-який аутентифікований користувач може спробувати завантажити файл.
#     Сервіс має валідувати, чи дозволено завантаження для вказаної мети та пов'язаного об'єкта.
# 6.  URL-и: Цей роутер буде підключений до `files_router` з префіксом `/uploads`.
# 7.  Коментарі: Українською мовою.
# 8.  Безпека: Важливо правильно валідувати типи файлів та розміри, щоб запобігти зловживанням.
#     Імена файлів слід санітизувати перед збереженням.
