# backend/app/src/schemas/files/file.py
"""
Pydantic схеми для сутності "Запис Файлу" (FileRecord).

Цей модуль визначає схеми для:
- Базового представлення запису файлу (`FileRecordBaseSchema`).
- Створення нового запису файлу (зазвичай виконується сервісом після завантаження) (`FileRecordCreateSchema`).
- Представлення даних про запис файлу у відповідях API (`FileRecordSchema`).
"""
from datetime import datetime
from typing import Optional, Dict, Any  # Any для тимчасових полів

from pydantic import Field, AnyHttpUrl, field_validator

# Абсолютний імпорт базових схем та Enum
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.core.dicts import FileType # Змінено імпорт FileTypeEnum на FileType
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)

# TODO: Замінити Any на UserPublicProfileSchema, коли вона буде доступна/рефакторена.
# from backend.app.src.schemas.auth.user import UserPublicProfileSchema
UserPublicProfileSchema = Any  # Тимчасовий заповнювач

FILE_NAME_MAX_LENGTH = 255
MIME_TYPE_MAX_LENGTH = 100
PURPOSE_MAX_LENGTH = 50


class FileRecordBaseSchema(BaseSchema):
    """
    Базова схема для полів запису файлу.
    """
    file_name: str = Field(
        ...,
        max_length=FILE_NAME_MAX_LENGTH,
        description=_("file_record.fields.file_name.description"),
        examples=["profile_picture.jpg", "документ_завдання.pdf"]
    )
    mime_type: str = Field(
        ...,
        max_length=MIME_TYPE_MAX_LENGTH,
        description=_("file_record.fields.mime_type.description"),
        examples=["image/jpeg", "application/pdf"]
    )
    file_size: int = Field(
        ...,
        ge=0,
        description=_("file_record.fields.file_size.description")
    )
    purpose: Optional[FileType] = Field(
        None,
        description=_("file_record.fields.purpose.description")
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description=_("file_record.fields.metadata.description")
    )

    # Валідатор validate_purpose більше не потрібен, Pydantic v2 обробляє Enum автоматично

    # model_config успадковується з BaseSchema (from_attributes=True)


class FileRecordCreateSchema(FileRecordBaseSchema):
    """
    Схема для створення нового запису файлу.
    `uploader_user_id` та `file_path` зазвичай встановлюються сервісом.
    """
    # Успадковує поля з FileRecordBaseSchema.
    # Ці поля встановлюються сервісом після фактичного завантаження файлу:
    # uploader_user_id: Optional[int] = None
    # file_path: str
    # Тому вони не тут, а очікуються як аргументи сервісного методу.
    pass


class FileRecordResponseSchema(FileRecordBaseSchema, IDSchemaMixin, TimestampedSchemaMixin): # Renamed
    """
    Схема для представлення даних про запис файлу у відповідях API.
    """
    # id, created_at, updated_at успадковані.
    # file_name, mime_type, file_size, purpose, metadata успадковані.

    file_path: str = Field(
        description=_("file_record.fields.file_path.description"))
    uploader_user_id: Optional[int] = Field(None, description=_("file_record.fields.uploader_user_id.description"))
    url: Optional[AnyHttpUrl] = Field(None, description=_("file_record.fields.url.description"))
    uploader: Optional[UserPublicProfileSchema] = Field(None,
                                                        description=_("file_record.fields.uploader.description"))


if __name__ == "__main__":
    # Демонстраційний блок для схем записів файлів.
    logger.info("--- Pydantic Схеми для Записів Файлів (FileRecord) ---")

    logger.info("\nFileRecordBaseSchema (приклад валідних даних):")
    base_file_data = {
        "file_name": "мій_документ.pdf",  # TODO i18n
        "mime_type": "application/pdf",
        "file_size": 102400,  # 100KB
        "purpose": FileType.GENERAL_DOCUMENT.value, # Змінено на FileType
        "metadata": {"pages": 10, "author": "Іван Іваненко"}  # TODO i18n
    }
    base_file_instance = FileRecordBaseSchema(**base_file_data)
    logger.info(base_file_instance.model_dump_json(indent=2, exclude_none=True))
    try:
        FileRecordBaseSchema(file_name="test.txt", mime_type="text/plain", file_size=10, purpose="INVALID_PURPOSE")
    except ValueError as e:
        logger.info(f"Помилка валідації FileRecordBaseSchema (очікувано для purpose): {e}")

    logger.info("\nFileRecordCreateSchema (приклад використання):")
    # FileRecordCreateSchema успадковує від FileRecordBaseSchema, тому використовуємо ті ж дані.
    # `uploader_user_id` та `file_path` додаються сервісом.
    create_file_instance = FileRecordCreateSchema(**base_file_data)
    logger.info(create_file_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nFileRecordSchema (приклад відповіді API):")
    file_response_data = {
        "id": 1,
        "file_name": "аватар_користувача.png",  # TODO i18n
        "mime_type": "image/png",
        "file_size": 51200,  # 50KB
        "purpose": FileType.AVATAR.value, # Змінено на FileType
        "file_path": "s3://bucket-name/avatars/user_xyz/avatar.png",  # Приклад шляху
        "uploader_user_id": 101,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "url": "https://cdn.example.com/avatars/user_xyz/avatar.png",
        # "uploader": {"id": 101, "name": "Завантажувач Користувач"} # Приклад UserPublicProfileSchema
    }
    file_response_instance = FileRecordResponseSchema(**file_response_data) # Renamed
    logger.info(file_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми для пов'язаних об'єктів (`uploader`) та поле `url`")
    logger.info("потребують заповнення на рівні сервісу або через @computed_field (для URL).")
    logger.info(
        f"Поле 'purpose' використовує значення з Enum `FileType` (наприклад, '{FileType.TASK_ATTACHMENT.value}').")
