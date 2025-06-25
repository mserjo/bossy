# backend/app/src/schemas/auth/token.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для токенів автентифікації,
зокрема для відповіді API, що включає access та refresh токени,
а також для представлення даних з моделі `RefreshTokenModel`.
"""

from pydantic import Field
from typing import Optional, Any
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema # IdentifiedSchema, TimestampedSchema
# Потрібно імпортувати схему користувача для зв'язку в RefreshTokenSchema (якщо розгортаємо)
# from backend.app.src.schemas.auth.user import UserPublicSchema (приклад)

# --- Схема для відповіді API з токенами ---
class TokenResponseSchema(BaseSchema):
    """
    Схема для відповіді API, що містить access та refresh токени.
    """
    access_token: str = Field(..., description="Access JWT токен")
    refresh_token: Optional[str] = Field(None, description="Refresh токен (може бути в httpOnly cookie)")
    token_type: str = Field(default="bearer", description="Тип токена (зазвичай 'bearer')")
    expires_in: Optional[int] = Field(None, description="Час життя access токена в секундах") # Для інформації клієнту
    # user: Optional[UserPublicSchema] = Field(None, description="Інформація про користувача (опціонально)") # Можна додати

# --- Схема для представлення даних Refresh токена (для читання, наприклад, адміном) ---
class RefreshTokenSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення даних про Refresh токен.
    """
    user_id: uuid.UUID = Field(..., description="Ідентифікатор користувача, якому належить токен")
    # hashed_token: str # Не віддаємо хеш токена через API
    expires_at: datetime = Field(..., description="Дата та час закінчення терміну дії токена")
    is_revoked: bool = Field(..., description="Прапорець, чи був токен відкликаний")
    revoked_at: Optional[datetime] = Field(None, description="Час, коли токен був відкликаний")
    revocation_reason: Optional[str] = Field(None, description="Причина відкликання токена")

    user_agent: Optional[str] = Field(None, description="User-Agent клієнта, для якого був виданий токен")
    ip_address: Optional[str] = Field(None, description="IP-адреса клієнта (представлена як рядок)")
    last_used_at: Optional[datetime] = Field(None, description="Час останнього використання токена")

    # `created_at` з AuditDatesSchema використовується як час видачі токена (`issued_at`).

    # user: Optional[UserPublicSchema] = None # Інформація про користувача, якому належить токен

# --- Схема для запиту на оновлення access токена за допомогою refresh токена ---
class RefreshTokenRequestSchema(BaseSchema):
    """
    Схема для запиту на оновлення access токена.
    Refresh токен зазвичай передається в тілі запиту або в httpOnly cookie.
    """
    refresh_token: str = Field(..., description="Дійсний Refresh токен")


# TODO: Переконатися, що схеми відповідають моделі `RefreshTokenModel`.
# `RefreshTokenModel` має: id, user_id, hashed_token, expires_at, is_revoked, revoked_at,
# revocation_reason, user_agent, ip_address, last_used_at, created_at, updated_at.
# `RefreshTokenSchema` (для читання) НЕ включає `hashed_token`, що правильно.
# Всі інші поля відображені.
#
# `TokenResponseSchema` - це стандартна відповідь для OAuth2-подібних систем.
# `refresh_token` в `TokenResponseSchema` може бути `Optional`, якщо він передається
# іншим способом (наприклад, в httpOnly cookie, що є більш безпечним).
# Якщо він в тілі відповіді, то він має бути тут.
# `expires_in` - корисне поле для клієнта, щоб знати, коли оновлювати access_token.
#
# `RefreshTokenRequestSchema` для ендпоінта оновлення токенів.
#
# Зв'язок `user` в `RefreshTokenSchema` закоментований, можна додати, якщо потрібно
# показувати інформацію про користувача разом з його токенами (наприклад, для адмінки).
# `ip_address` в схемі як `str`, що відповідає тому, як SQLAlchemy повертає `INET`.
# Все виглядає узгоджено.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` тут фактично є часом видачі (`issued_at`) refresh токена.
# `updated_at` оновлюється при зміні `last_used_at` або `is_revoked`.
# Це коректно.
