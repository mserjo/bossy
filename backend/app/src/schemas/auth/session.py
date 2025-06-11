# backend/app/src/schemas/auth/session.py
"""
Pydantic схеми для сутності "Сесія Користувача" (Session).

Цей модуль визначає схему `SessionSchema` для представлення даних
про сесію користувача у відповідях API.
"""
from datetime import datetime
from typing import Optional

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# from pydantic import Field # Може знадобитися для кастомних атрибутів Field

class SessionSchema(BaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Pydantic схема для представлення даних сесії користувача.

    Успадковує `id`, `created_at`, `updated_at` від базових схем/міксинів.
    Призначена для використання у відповідях API, наприклад, при перегляді активних сесій.
    """
    user_id: int = Field(description="Ідентифікатор користувача, якому належить сесія.")
    session_key: str = Field(description="Унікальний ключ сесії.")
    expires_at: datetime = Field(description="Час закінчення терміну дії сесії.")
    user_agent: Optional[str] = Field(None, description="User-Agent клієнта, з якого створено сесію.")
    ip_address: Optional[str] = Field(None, description="IP-адреса клієнта, з якого створено сесію.")

    # model_config успадковується з BaseSchema (from_attributes=True)


class SessionCreateSchema(BaseSchema):
    """
    Схема для створення нового запису сесії користувача.
    Зазвичай використовується внутрішньо сервісом автентифікації при вході користувача.
    """
    user_id: int = Field(description="ID користувача, якому належить сесія.")
    session_key: str = Field(description="Унікальний ключ сесії.")
    expires_at: datetime = Field(description="Час закінчення терміну дії сесії.")
    user_agent: Optional[str] = Field(None, description="User-Agent клієнта.")
    ip_address: Optional[str] = Field(None, description="IP-адреса клієнта.")


if __name__ == "__main__":
    # Демонстраційний блок для схеми SessionSchema.
    logger.info("--- Pydantic Схема для Сесії Користувача (SessionSchema) ---")

    session_data_example = {
        "id": 1,
        "user_id": 101,
        "session_key": "abcdef123456uvwxyz",
        "expires_at": datetime.now() + timedelta(hours=2),
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "ip_address": "192.168.1.100",
        "created_at": datetime.now() - timedelta(minutes=5),
        "updated_at": datetime.now(),
    }

    session_instance = SessionSchema(**session_data_example)
    logger.info(f"\nПриклад екземпляра SessionSchema:\n{session_instance.model_dump_json(indent=2, exclude_none=True)}")

    logger.info("\nПримітка: Ця схема використовується для представлення даних сесій у відповідях API.")

# Потрібно для timedelta в __main__
from datetime import timedelta
