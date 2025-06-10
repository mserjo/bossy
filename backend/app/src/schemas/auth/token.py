# backend/app/src/schemas/auth/token.py
"""
Pydantic схеми для JWT токенів.

Цей модуль визначає схеми для:
- `TokenPayload`: Корисне навантаження (claims) всередині JWT токена.
- `TokenResponse`: Відповідь API, що містить токени доступу та оновлення.
- `RefreshTokenRequest`: Запит на оновлення токена доступу за допомогою токена оновлення.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import Field

# Абсолютний імпорт базової схеми
from backend.app.src.schemas.base import BaseSchema
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class TokenPayload(BaseSchema):
    """
    Схема корисного навантаження (claims) JWT токена.
    Визначає стандартні та кастомні поля, що очікуються всередині токена.
    """
    sub: Optional[str] = Field(None, description="Ідентифікатор суб'єкта токена (зазвичай ID користувача або email).")
    user_id: Optional[int] = Field(None, description="Числовий ID користувача, якщо відрізняється від 'sub'.")
    # Патерн для типу токена: тільки "access" або "refresh"
    type: Optional[str] = Field(None, pattern=r"^(access|refresh)$", description="Тип токена ('access' або 'refresh').")

    # Стандартні JWT claims (https://tools.ietf.org/html/rfc7519#section-4.1)
    exp: Optional[datetime] = Field(None,
                                    description="Час закінчення терміну дії токена (Unix timestamp). Pydantic автоматично конвертує int в datetime.")
    iat: Optional[datetime] = Field(None, description="Час видачі токена (Unix timestamp).")
    iss: Optional[str] = Field(None, description="Видавець токена (має відповідати налаштуванням).")
    aud: Optional[str] = Field(None, description="Аудиторія токена (має відповідати налаштуванням).")

    # Приклад кастомних полів (можуть бути додані за потребою)
    roles: Optional[List[str]] = Field(default_factory=list,
                                       description="Список рядкових ідентифікаторів ролей користувача.")
    permissions: Optional[List[str]] = Field(default_factory=list,
                                             description="Список рядкових ідентифікаторів дозволів користувача.")

    # model_config успадковується з BaseSchema (from_attributes=True)


class TokenResponse(BaseSchema):
    """
    Схема відповіді API при успішному вході або оновленні токенів.
    """
    access_token: str = Field(description="JWT токен доступу.")
    refresh_token: str = Field(description="JWT токен оновлення.")
    token_type: str = Field("bearer", description="Тип токена (завжди 'bearer').")


class RefreshTokenRequest(BaseSchema):
    """
    Схема запиту для оновлення токена доступу.
    Очікує надання дійсного токена оновлення.
    """
    refresh_token: str = Field(description="Дійсний JWT токен оновлення.")


class RefreshTokenCreateSchema(BaseSchema):
    """
    Схема для створення запису RefreshToken в базі даних.
    Зазвичай використовується внутрішньо сервісом автентифікації.
    """
    user_id: int = Field(description="ID користувача, якому належить токен.")
    token: str = Field(description="Рядкове представлення токена оновлення (або його хеш).")
    expires_at: datetime = Field(description="Час закінчення терміну дії токена оновлення.")


if __name__ == "__main__":
    # Демонстраційний блок для схем токенів.
    logger.info("--- Pydantic Схеми для Токенів (Token) ---")

    logger.info("\nTokenPayload (приклад):")
    payload_data = {
        "sub": "user@example.com",
        "user_id": 123,
        "type": "access",
        "exp": int((datetime.now() + timedelta(minutes=15)).timestamp()),
        # Pydantic очікує int для datetime з timestamp
        "iat": int(datetime.now().timestamp()),
        "iss": "kudos.example.com",
        "aud": "kudos.example.com",
        "roles": ["user", "editor"],
        "permissions": ["read_articles", "edit_articles"]
    }
    try:
        payload_instance = TokenPayload(**payload_data)
        # Конвертуємо datetime назад в int для JSON серіалізації, якщо потрібно точне відтворення вхідних даних
        # Або залишаємо як є, якщо ISO формат дати є прийнятним у JSON
        # Для демонстрації `exp` та `iat` як datetime:
        # dump_payload = payload_instance.model_dump(exclude_none=True)
        # dump_payload['exp'] = dump_payload['exp'].isoformat()
        # dump_payload['iat'] = dump_payload['iat'].isoformat()
        # logger.info(json.dumps(dump_payload, indent=2))
        logger.info(payload_instance.model_dump_json(indent=2, exclude_none=True))

        invalid_payload_data = payload_data.copy()
        invalid_payload_data["type"] = "invalid_type"
        TokenPayload(**invalid_payload_data)  # Це має викликати помилку валідації
    except Exception as e:
        logger.info(f"Помилка валідації TokenPayload (очікувано для invalid_type): {e}")

    logger.info("\nTokenResponse (приклад):")
    token_response_data = {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhY2Nlc3NfdXNlciIsImV4cCI6MTY3ODg4NjQwMH0.example_access_token",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJyZWZyZXNoX3VzZXIiLCJleHAiOjE2Nzk0OTEyMDB9.example_refresh_token",
        # token_type має значення за замовчуванням "bearer"
    }
    token_response_instance = TokenResponse(**token_response_data)
    logger.info(token_response_instance.model_dump_json(indent=2))

    logger.info("\nRefreshTokenRequest (приклад):")
    refresh_request_data = {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJyZWZyZXNoX3VzZXIiLCJleHAiOjE2Nzk0OTEyMDB9.example_refresh_token_for_request"
    }
    refresh_request_instance = RefreshTokenRequest(**refresh_request_data)
    logger.info(refresh_request_instance.model_dump_json(indent=2))

    logger.info("\nПримітка: Ці схеми використовуються для валідації даних, пов'язаних з JWT токенами.")

# Потрібно для timedelta в __main__
from datetime import timedelta
# import json # Для кастомного дампу дат як int
