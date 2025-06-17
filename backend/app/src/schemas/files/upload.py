# backend/app/src/schemas/files/upload.py
"""
Pydantic схеми для процесу завантаження файлів.

Цей модуль визначає схеми для:
- Ініціації завантаження файлу (`FileUploadInitiateRequestSchema`).
- Відповіді з URL для прямого завантаження (наприклад, presigned URL S3) (`PresignedUploadURLResponse`).
- Підтвердження успішного завантаження (`FileUploadCompleteRequestSchema`).
- Фінальної відповіді з інформацією про завантажений файл (`FileUploadResponse`).
"""
from typing import Optional, Dict

from pydantic import Field, AnyHttpUrl, field_validator

# Абсолютний імпорт базової схеми та Enum
from backend.app.src.schemas.base import BaseSchema
from backend.app.src.core.dicts import FileType # Змінено імпорт FileTypeEnum на FileType
from backend.app.src.config.logging import get_logger 
logger = get_logger(__name__)

FILE_NAME_MAX_LENGTH_UPLOAD = 255 # Збігається з FileRecord
MIME_TYPE_MAX_LENGTH_UPLOAD = 100 # Збігається з FileRecord
PURPOSE_MAX_LENGTH_UPLOAD = 50    # Збігається з FileRecord


class PresignedUrlRequestSchema(BaseSchema): # Renamed from FileUploadInitiateRequestSchema
    """
    Схема для запиту на ініціацію завантаження файлу та отримання presigned URL.
    Клієнт надсилає метадані файлу, щоб отримати URL для завантаження.
    """
    file_name: str = Field(
        ...,
        max_length=FILE_NAME_MAX_LENGTH_UPLOAD,
        description="Ім'я файлу, що завантажується.",
        examples=["my_document.pdf", "profile_image.jpg"]
    )
    mime_type: str = Field(
        ...,
        max_length=MIME_TYPE_MAX_LENGTH_UPLOAD,
        description="MIME-тип файлу.",
        examples=["application/pdf", "image/jpeg"]
    )
    file_size: int = Field(
        ...,
        ge=0, # Розмір не може бути від'ємним
        # TODO: Додати максимальний розмір файлу з налаштувань settings.MAX_FILE_SIZE_MB
        # le=settings.MAX_FILE_SIZE_MB * 1024 * 1024,
        description="Розмір файлу в байтах."
    )
    # Валідатор для purpose на основі Enum FileType вже існує нижче.
    purpose: FileType = Field( # Змінено на FileType
        ...,
        # max_length більше не потрібен для Enum
        description="Призначення файлу. Визначає подальшу обробку та зберігання."
    )

    # Валідатор validate_purpose більше не потрібен, Pydantic v2 обробляє Enum автоматично


class PresignedUrlResponseSchema(BaseSchema): # Renamed from PresignedUploadURLResponse
    """
    Схема відповіді, що містить URL для прямого завантаження файлу (наприклад, presigned URL для S3)
    та ідентифікатор створеного запису файлу.
    """
    upload_url: AnyHttpUrl = Field(description="URL, на який клієнт має завантажити файл (PUT або POST).")
    fields: Optional[Dict[str, str]] = Field(
        None,
        description="Додаткові поля, які потрібно включити в тіло POST-запиту (для S3 presigned POST)."
    )
    file_record_id: int = Field(description="ID створеного запису FileRecord, що очікує на завантаження файлу.")


class FileUploadCompleteRequestSchema(BaseSchema):
    """
    Схема для запиту на підтвердження успішного завантаження файлу.
    Клієнт надсилає цей запит після того, як файл було успішно завантажено за наданим URL.
    """
    file_record_id: int = Field(description="ID запису FileRecord, для якого підтверджується завантаження.")
    # Наступні поля можуть бути специфічними для провайдера сховища (наприклад, S3)
    upload_key: Optional[str] = Field(
        None,
        description="Ключ об'єкта в сховищі, якщо він відрізняється від початкового file_path (необов'язково)."
    )
    e_tag: Optional[str] = Field(
        None,
        description="ETag об'єкта зі сховища, використовується для перевірки цілісності (наприклад, для S3)."
    )
    # Можна додати інші поля, такі як version_id для S3.


class FileUploadResponseSchema(BaseSchema): # Renamed from FileUploadResponse
    """
    Схема відповіді після успішного завершення всього процесу завантаження файлу.
    Містить фінальну інформацію про завантажений файл.
    """
    file_id: int = Field(description="ID запису файлу (синонім file_record_id).", alias="fileRecordId")
    file_name: str = Field(description="Ім'я завантаженого файлу.")
    url: AnyHttpUrl = Field(description="Фінальний URL для доступу до завантаженого файлу.")
    mime_type: str = Field(description="MIME-тип файлу.")
    file_size: int = Field(description="Розмір файлу в байтах.")
    purpose: Optional[FileType] = Field(None, description="Призначення файлу.") # Змінено на FileType

    # model_config успадковується з BaseSchema, який вже має populate_by_name = True
    # class Config:
    #     populate_by_name = True


if __name__ == "__main__":
    # Демонстраційний блок для схем процесу завантаження файлів.
    logger.info("--- Pydantic Схеми для Процесу Завантаження Файлів ---")

    logger.info("\nFileUploadInitiateRequestSchema (приклад запиту на ініціацію):")
    initiate_data = {
        "file_name": "contract_final.docx", # TODO i18n example
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "file_size": 256000, # 250KB
        "purpose": FileType.GENERAL_DOCUMENT.value # Змінено на FileType
    }
    initiate_instance = PresignedUrlRequestSchema(**initiate_data) # Renamed
    logger.info(initiate_instance.model_dump_json(indent=2))
    try:
        PresignedUrlRequestSchema(file_name="test.txt", mime_type="text/plain", file_size=10, purpose="INVALID_PURPOSE") # Renamed
    except ValueError as e:
        logger.info(f"Помилка валідації PresignedUrlRequestSchema (очікувано для purpose): {e}") # Renamed


    logger.info("\nPresignedUrlResponseSchema (приклад відповіді з URL для завантаження):") # Renamed
    presigned_data = {
        "upload_url": "https://s3.example.com/bucket-name/user_xyz/contract_final.docx?AWSAccessKeyId=...",
        "fields": {"key": "user_xyz/contract_final.docx", "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        "file_record_id": 101
    }
    presigned_instance = PresignedUrlResponseSchema(**presigned_data) # Renamed
    logger.info(presigned_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nFileUploadCompleteRequestSchema (приклад запиту на підтвердження):")
    complete_data = {
        "file_record_id": 101,
        "upload_key": "user_xyz/contract_final.docx_completed", # Може змінитися, якщо на сервері інша логіка
        "e_tag": "\"abcdef1234567890fedcba0987654321\""
    }
    complete_instance = FileUploadCompleteRequestSchema(**complete_data)
    logger.info(complete_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nFileUploadResponse (приклад фінальної відповіді):")
    final_response_data = {
        "file_id": 101, # Або fileRecordId, якщо використовується аліас при серіалізації
        "file_name": "contract_final.docx",
        "url": "https://cdn.example.com/files/user_xyz/contract_final.docx_completed",
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "file_size": 256000,
        "purpose": FileType.GENERAL_DOCUMENT.value # Змінено на FileType
    }
    # Для демонстрації аліасу при створенні екземпляра
    final_response_instance_alias = FileUploadResponseSchema(fileRecordId=101, **{k:v for k,v in final_response_data.items() if k != 'file_id'}) # Renamed
    logger.info(final_response_instance_alias.model_dump_json(indent=2, by_alias=True, exclude_none=True)) # by_alias=True для використання аліасів при серіалізації

    logger.info("\nПримітка: Ці схеми описують кроки процесу завантаження файлів.")
    logger.info("Валідатор для 'purpose' на основі Enum FileType в PresignedUrlRequestSchema вже існує.") # Updated TODO
    logger.info("TODO: Додати обмеження на 'file_size' в PresignedUrlRequestSchema згідно з налаштуваннями.")
