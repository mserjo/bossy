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
from backend.app.src.core.dicts import FileType as FileTypeEnum

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
        description="Оригінальне або згенероване ім'я файлу.",
        examples=["profile_picture.jpg", "документ_завдання.pdf"]
    )
    mime_type: str = Field(
        ...,
        max_length=MIME_TYPE_MAX_LENGTH,
        description="MIME-тип файлу.",
        examples=["image/jpeg", "application/pdf"]
    )
    file_size: int = Field(
        ...,
        ge=0,
        description="Розмір файлу в байтах."
    )
    # TODO: Додати валідатор для purpose на основі Enum FileTypeEnum
    purpose: Optional[str] = Field(
        None,
        max_length=PURPOSE_MAX_LENGTH,
        description=f"Призначення файлу (наприклад, '{FileTypeEnum.AVATAR.value}', '{FileTypeEnum.TASK_ATTACHMENT.value}')."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Додаткові метадані файлу у форматі JSON (наприклад, розміри зображення, тривалість аудіо/відео)."
    )

    @field_validator('purpose')
    @classmethod
    def validate_purpose(cls, value: Optional[str]) -> Optional[str]:
        """Перевіряє, чи надане значення призначення є допустимим членом Enum FileType."""
        if value is None:
            return value
        allowed_purposes = {ft.value for ft in FileTypeEnum}
        if value not in allowed_purposes:
            # TODO i18n: Translatable error message
            raise ValueError(f"Недопустиме призначення файлу '{value}'. Дозволені: {', '.join(allowed_purposes)}")
        return value

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


class FileRecordSchema(FileRecordBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про запис файлу у відповідях API.
    """
    # id, created_at, updated_at успадковані.
    # file_name, mime_type, file_size, purpose, metadata успадковані.

    file_path: str = Field(
        description="Шлях до файлу на сервері або ключ в об'єктному сховищі (зазвичай не повертається клієнту напряму).")
    uploader_user_id: Optional[int] = Field(None, description="ID користувача, який завантажив файл.")

    # TODO: URL має генеруватися сервісом (наприклад, presigned URL для S3 або статичний URL).
    #       Це поле може бути @computed_field в Pydantic v2, якщо логіка генерації URL проста
    #       і не потребує асинхронних операцій або доступу до request.
    #       Або ж воно заповнюється на рівні сервісу перед поверненням відповіді.
    url: Optional[AnyHttpUrl] = Field(None, description="Публічний URL для доступу до файлу (якщо застосовно).")

    # TODO: Замінити Any на UserPublicProfileSchema.
    uploader: Optional[UserPublicProfileSchema] = Field(None,
                                                        description="Інформація про користувача, який завантажив файл.")


if __name__ == "__main__":
    # Демонстраційний блок для схем записів файлів.
    print("--- Pydantic Схеми для Записів Файлів (FileRecord) ---")

    print("\nFileRecordBaseSchema (приклад валідних даних):")
    base_file_data = {
        "file_name": "мій_документ.pdf",  # TODO i18n
        "mime_type": "application/pdf",
        "file_size": 102400,  # 100KB
        "purpose": FileTypeEnum.GENERAL_DOCUMENT.value,
        "metadata": {"pages": 10, "author": "Іван Іваненко"}  # TODO i18n
    }
    base_file_instance = FileRecordBaseSchema(**base_file_data)
    print(base_file_instance.model_dump_json(indent=2, exclude_none=True))
    try:
        FileRecordBaseSchema(file_name="test.txt", mime_type="text/plain", file_size=10, purpose="INVALID_PURPOSE")
    except ValueError as e:
        print(f"Помилка валідації FileRecordBaseSchema (очікувано для purpose): {e}")

    print("\nFileRecordCreateSchema (приклад використання):")
    # FileRecordCreateSchema успадковує від FileRecordBaseSchema, тому використовуємо ті ж дані.
    # `uploader_user_id` та `file_path` додаються сервісом.
    create_file_instance = FileRecordCreateSchema(**base_file_data)
    print(create_file_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nFileRecordSchema (приклад відповіді API):")
    file_response_data = {
        "id": 1,
        "file_name": "аватар_користувача.png",  # TODO i18n
        "mime_type": "image/png",
        "file_size": 51200,  # 50KB
        "purpose": FileTypeEnum.AVATAR.value,
        "file_path": "s3://bucket-name/avatars/user_xyz/avatar.png",  # Приклад шляху
        "uploader_user_id": 101,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "url": "https://cdn.example.com/avatars/user_xyz/avatar.png",
        # "uploader": {"id": 101, "name": "Завантажувач Користувач"} # Приклад UserPublicProfileSchema
    }
    file_response_instance = FileRecordSchema(**file_response_data)
    print(file_response_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nПримітка: Схеми для пов'язаних об'єктів (`uploader`) та поле `url`")
    print("потребують заповнення на рівні сервісу або через @computed_field (для URL).")
    print(
        f"Поле 'purpose' використовує значення з Enum `FileType` (наприклад, '{FileTypeEnum.TASK_ATTACHMENT.value}').")
