# backend/app/src/schemas/auth/session.py
"""
Pydantic схеми для сутності "Сесія Користувача" (Session).

Цей модуль визначає схему `SessionSchema` для представлення даних
про сесію користувача у відповідях API.
"""
from datetime import datetime
from typing import Optional

from uuid import UUID # Для поля session_token

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.config import logger  # Імпорт логера
from pydantic import Field


class UserSessionResponse(BaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Pydantic схема для представлення даних сесії користувача у відповідях API.

    Успадковує `id`, `created_at`, `updated_at` від базових схем/міксинів.
    """
    user_id: int = Field(description="Ідентифікатор користувача, якому належить сесія.")
    session_token: UUID = Field(description="Унікальний токен сесії (UUID).")
    expires_at: datetime = Field(description="Час закінчення терміну дії сесії.")
    user_agent: Optional[str] = Field(None, description="User-Agent клієнта, з якого створено сесію.")
    ip_address: Optional[str] = Field(None, description="IP-адреса клієнта, з якого створено сесію.")
    last_active_at: Optional[datetime] = Field(None, description="Час останньої активності сесії.")

    # model_config успадковується з BaseSchema (from_attributes=True)


class UserSessionCreate(BaseSchema):
    """
    Схема для створення нового запису сесії користувача.
    """
    user_id: int = Field(description="ID користувача, якому належить сесія.")
    session_token: UUID = Field(description="Унікальний токен сесії (UUID).") # Має генеруватися сервером
    expires_at: datetime = Field(description="Час закінчення терміну дії сесії.")
    user_agent: Optional[str] = Field(None, description="User-Agent клієнта.")
    ip_address: Optional[str] = Field(None, description="IP-адреса клієнта.")
    # last_active_at не включається сюди, бо встановлюється при активності


if __name__ == "__main__":
    from datetime import timedelta
    import uuid

    logger.info("--- Pydantic Схема для Сесії Користувача (UserSessionResponse) ---")

    session_data_example = {
        "id": 1,
        "user_id": 101,
        "session_token": uuid.uuid4(), # Змінено з session_key
        "expires_at": datetime.now() + timedelta(hours=2),
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "ip_address": "192.168.1.100",
        "last_active_at": datetime.now() - timedelta(minutes=1), # Додано
        "created_at": datetime.now() - timedelta(minutes=5),
        "updated_at": datetime.now(),
    }

    session_instance = UserSessionResponse(**session_data_example) # Змінено з SessionSchema
    logger.info(f"\nПриклад екземпляра UserSessionResponse:\n{session_instance.model_dump_json(indent=2, exclude_none=True)}")

    logger.info("\n--- Pydantic Схема для Створення Сесії (UserSessionCreate) ---")
    create_data_example = {
        "user_id": 102,
        "session_token": uuid.uuid4(), # Змінено з session_key
        "expires_at": datetime.now() + timedelta(days=7),
        "user_agent": "My Test Client 1.0",
        "ip_address": "127.0.0.1"
    }
    create_instance = UserSessionCreate(**create_data_example)
    logger.info(f"\nПриклад екземпляра UserSessionCreate:\n{create_instance.model_dump_json(indent=2, exclude_none=True)}")

    logger.info("\nПримітка: Ці схеми використовуються для валідації та представлення даних сесій.")
