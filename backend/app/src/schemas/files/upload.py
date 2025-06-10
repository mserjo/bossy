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
from backend.app.src.core.dicts import FileType as FileTypeEnum # Enum для призначення файлу

FILE_NAME_MAX_LENGTH_UPLOAD = 255 # Збігається з FileRecord
MIME_TYPE_MAX_LENGTH_UPLOAD = 100 # Збігається з FileRecord
PURPOSE_MAX_LENGTH_UPLOAD = 50    # Збігається з FileRecord


class FileUploadInitiateRequestSchema(BaseSchema):
    """
    Схема для запиту на ініціацію завантаження файлу.
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
    # TODO: Додати валідатор для purpose на основі Enum FileTypeEnum
    purpose: str = Field(
        ...,
        max_length=PURPOSE_MAX_LENGTH_UPLOAD,
        description=f"Призначення файлу (наприклад, '{FileTypeEnum.AVATAR.value}', '{FileTypeEnum.TASK_ATTACHMENT.value}'). Визначає подальшу обробку та зберігання."
    )

    @field_validator('purpose')
    @classmethod
    def validate_purpose(cls, value: str) -> str:
        """Перевіряє, чи надане значення призначення є допустимим членом Enum FileType."""
        allowed_purposes = {ft.value for ft in FileTypeEnum}
        if value not in allowed_purposes:
            # TODO i18n: Translatable error message
            raise ValueError(f"Недопустиме призначення файлу '{value}'. Дозволені: {', '.join(allowed_purposes)}")
        return value


class PresignedUploadURLResponse(BaseSchema):
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


class FileUploadResponse(BaseSchema):
    """
    Схема відповіді після успішного завершення всього процесу завантаження файлу.
    Містить фінальну інформацію про завантажений файл.
    """
    file_id: int = Field(description="ID запису файлу (синонім file_record_id).", alias="fileRecordId")
    file_name: str = Field(description="Ім'я завантаженого файлу.")
    url: AnyHttpUrl = Field(description="Фінальний URL для доступу до завантаженого файлу.")
    mime_type: str = Field(description="MIME-тип файлу.")
    file_size: int = Field(description="Розмір файлу в байтах.")
    purpose: Optional[str] = Field(None, description="Призначення файлу.")

    class Config: # Використовуємо вкладений Config для Pydantic v2, а не model_config на рівні класу
        populate_by_name = True # Дозволяє використовувати аліас fileRecordId


if __name__ == "__main__":
    # Демонстраційний блок для схем процесу завантаження файлів.
    print("--- Pydantic Схеми для Процесу Завантаження Файлів ---")

    print("\nFileUploadInitiateRequestSchema (приклад запиту на ініціацію):")
    initiate_data = {
        "file_name": "contract_final.docx", # TODO i18n example
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "file_size": 256000, # 250KB
        "purpose": FileTypeEnum.GENERAL_DOCUMENT.value
    }
    initiate_instance = FileUploadInitiateRequestSchema(**initiate_data)
    print(initiate_instance.model_dump_json(indent=2))
    try:
        FileUploadInitiateRequestSchema(file_name="test.txt", mime_type="text/plain", file_size=10, purpose="INVALID_PURPOSE")
    except ValueError as e:
        print(f"Помилка валідації FileUploadInitiateRequestSchema (очікувано для purpose): {e}")


    print("\nPresignedUploadURLResponse (приклад відповіді з URL для завантаження):")
    presigned_data = {
        "upload_url": "https://s3.example.com/bucket-name/user_xyz/contract_final.docx?AWSAccessKeyId=...",
        "fields": {"key": "user_xyz/contract_final.docx", "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        "file_record_id": 101
    }
    presigned_instance = PresignedUploadURLResponse(**presigned_data)
    print(presigned_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nFileUploadCompleteRequestSchema (приклад запиту на підтвердження):")
    complete_data = {
        "file_record_id": 101,
        "upload_key": "user_xyz/contract_final.docx_completed", # Може змінитися, якщо на сервері інша логіка
        "e_tag": "\"abcdef1234567890fedcba0987654321\""
    }
    complete_instance = FileUploadCompleteRequestSchema(**complete_data)
    print(complete_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nFileUploadResponse (приклад фінальної відповіді):")
    final_response_data = {
        "file_id": 101, # Або fileRecordId, якщо використовується аліас при серіалізації
        "file_name": "contract_final.docx",
        "url": "https://cdn.example.com/files/user_xyz/contract_final.docx_completed",
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "file_size": 256000,
        "purpose": FileTypeEnum.GENERAL_DOCUMENT.value
    }
    # Для демонстрації аліасу при створенні екземпляра
    final_response_instance_alias = FileUploadResponse(fileRecordId=101, **{k:v for k,v in final_response_data.items() if k != 'file_id'})
    print(final_response_instance_alias.model_dump_json(indent=2, by_alias=True, exclude_none=True)) # by_alias=True для використання аліасів при серіалізації

    print("\nПримітка: Ці схеми описують кроки процесу завантаження файлів.")
    print("TODO: Додати валідацію 'purpose' на основі Enum FileTypeEnum в FileUploadInitiateRequestSchema.")
    print("TODO: Додати обмеження на 'file_size' в FileUploadInitiateRequestSchema згідно з налаштуваннями.")
