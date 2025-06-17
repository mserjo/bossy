# backend/app/src/schemas/files/avatar.py
"""
Pydantic схеми для сутності "Аватар Користувача" (UserAvatar).

Цей модуль визначає схеми для:
- Базового представлення зв'язку аватара з користувачем (`UserAvatarBaseSchema`).
- Створення нового запису про аватар (зазвичай виконується сервісом) (`UserAvatarCreateSchema`).
- Представлення даних про аватар користувача у відповідях API (`UserAvatarSchema`).
"""
from datetime import datetime, timedelta # Moved timedelta here
from typing import Optional, Any  # Any для тимчасових полів

from pydantic import Field, AnyHttpUrl

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.config.logging import get_logger 
logger = get_logger(__name__)

# TODO: Замінити Any на конкретні схеми, коли вони будуть доступні/рефакторені.
# from backend.app.src.schemas.auth.user import UserPublicProfileSchema
# from backend.app.src.schemas.files.file import FileRecordSchema
UserPublicProfileSchema = Any  # Тимчасовий заповнювач
FileRecordSchema = Any  # Тимчасовий заповнювач


class UserAvatarBaseSchema(BaseSchema):
    """
    Базова схема для полів зв'язку аватара користувача.
    """
    user_id: int = Field(description="Ідентифікатор користувача, якому належить аватар.")
    file_record_id: int = Field(description="Ідентифікатор запису файлу, що є аватаром.")
    is_active: bool = Field(default=True, description="Чи є цей аватар поточним активним для користувача.")
    # model_config успадковується з BaseSchema (from_attributes=True)


class UserAvatarCreateSchema(UserAvatarBaseSchema):
    """
    Схема для створення нового запису про аватар користувача.
    Зазвичай використовується внутрішніми сервісами при завантаженні нового аватара.
    """
    # Успадковує user_id, file_record_id, is_active.
    # `created_at` (як час встановлення) буде встановлено автоматично через TimestampedSchemaMixin у відповіді.
    pass


class UserAvatarResponseSchema(UserAvatarBaseSchema, IDSchemaMixin, TimestampedSchemaMixin): # Renamed
    """
    Схема для представлення даних про аватар користувача у відповідях API.
    Поле `created_at` (з `TimestampedSchemaMixin`) позначає час встановлення аватара.
    """
    # id, created_at, updated_at успадковані.
    # user_id, file_record_id, is_active успадковані.

    # TODO: Поле `file_url` має заповнюватися сервісом, отримуючи URL з пов'язаного `FileRecord`.
    #       Це може бути прямий URL або presigned URL.
    file_url: Optional[AnyHttpUrl] = Field(None, description="URL для доступу до файлу аватара.")

    # TODO: Замінити Any на відповідні схеми.
    user: Optional[UserPublicProfileSchema] = Field(None,
                                                    description="Інформація про користувача (зазвичай не включається, якщо запит йде від цього ж користувача або аватар є частиною профілю користувача).")
    file_record: Optional[FileRecordSchema] = Field(None, description="Детальна інформація про файл аватара.")


if __name__ == "__main__":
    # Демонстраційний блок для схем аватарів користувачів.
    logger.info("--- Pydantic Схеми для Аватарів Користувачів (UserAvatar) ---")

    logger.info("\nUserAvatarCreateSchema (приклад для створення сервісом):")
    create_avatar_data = {
        "user_id": 101,
        "file_record_id": 205,
        "is_active": True
    }
    create_avatar_instance = UserAvatarCreateSchema(**create_avatar_data)
    logger.info(create_avatar_instance.model_dump_json(indent=2))

    logger.info("\nUserAvatarSchema (приклад відповіді API):")
    avatar_response_data = {
        "id": 1,
        "user_id": 101,
        "file_record_id": 205,
        "is_active": True,
        "created_at": datetime.now() - timedelta(days=1),  # Час встановлення
        "updated_at": datetime.now() - timedelta(days=1),
        "file_url": "https://cdn.example.com/avatars/user101/avatar_new.png",
        # "user": {"id": 101, "name": "Користувач З Аватаром"}, # Приклад UserPublicProfileSchema
        # "file_record": { # Приклад FileRecordSchema
        #     "id": 205,
        #     "file_name": "avatar_new.png",
        #     "mime_type": "image/png",
        #     "file_size": 12345,
        #     "purpose": "avatar",
        #     "created_at": datetime.now() - timedelta(days=1),
        #     "updated_at": datetime.now() - timedelta(days=1)
        # }
    }
    avatar_response_instance = UserAvatarResponseSchema(**avatar_response_data) # Renamed
    logger.info(avatar_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми для пов'язаних об'єктів (`user`, `file_record`) та поле `file_url`")
    logger.info("наразі є заповнювачами (Any) або потребують заповнення сервісом.")
