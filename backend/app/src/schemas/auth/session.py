# backend/app/src/schemas/auth/session.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `SessionModel`.
Схеми використовуються для відображення інформації про активні сесії користувача,
наприклад, в його профілі для можливості перегляду та завершення сесій.
"""

from pydantic import Field
from typing import Optional, Any
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema # IdentifiedSchema, TimestampedSchema
# Потрібно імпортувати схему RefreshTokenSchema, якщо розгортаємо інформацію про токен
# from backend.app.src.schemas.auth.token import RefreshTokenSchema (приклад)

# --- Схема для відображення інформації про сесію користувача (для читання) ---
class SessionSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення інформації про сесію користувача.
    """
    user_id: uuid.UUID = Field(..., description="Ідентифікатор користувача, якому належить сесія")

    # refresh_token_id: Optional[uuid.UUID] = Field(None, description="ID Refresh токена, пов'язаного з сесією")
    # refresh_token: Optional[RefreshTokenSchema] = None # Розгорнута інформація про токен (якщо потрібно)
    # Зазвичай, деталі refresh токена не показуються користувачу, лише факт наявності сесії.
    # `refresh_token_id` може бути корисним для адмінки або для зв'язку, якщо сесію треба завершити через відкликання токена.
    # Поки що не включаю `refresh_token_id` та `refresh_token` в схему для користувача.
    # Якщо вони потрібні для адмінки, можна створити окрему AdminSessionSchema.
    # Або ж, якщо користувач бачить свої сесії, то `id` самої сесії є ключем для її завершення.

    user_agent: Optional[str] = Field(None, description="User-Agent клієнта (браузер, мобільний додаток)")
    ip_address: Optional[str] = Field(None, description="IP-адреса, з якої була розпочата сесія (представлена як рядок)")

    last_activity_at: datetime = Field(..., description="Час останньої активності в межах цієї сесії")
    expires_at: Optional[datetime] = Field(None, description="Час, коли сесія (або пов'язаний токен) закінчується")
    is_active: bool = Field(..., description="Прапорець, чи є сесія наразі активною")

    # `created_at` з AuditDatesSchema використовується як час початку сесії (входу).
    # `updated_at` оновлюється при зміні `last_activity_at` або `is_active`.

    # @field_validator('ip_address', mode='before')
    # @classmethod
    # def validate_ip_address(cls, value):
    #     # Якщо з БД приходить об'єкт ipaddress.IPv4Address/IPv6Address, конвертуємо в рядок.
    #     # Зазвичай SQLAlchemy повертає рядок.
    #     if value is not None and not isinstance(value, str):
    #         return str(value)
    #     return value

# --- Схема для відповіді зі списком сесій ---
# class SessionListSchema(BaseSchema):
#     items: List[SessionSchema]
#     total: int

# TODO: Переконатися, що схеми відповідають моделі `SessionModel`.
# `SessionModel` має: id, user_id, refresh_token_id, user_agent, ip_address,
# last_activity_at, expires_at, is_active, created_at, updated_at.
#
# `SessionSchema` (для читання користувачем) включає:
# id, user_id, user_agent, ip_address, last_activity_at, expires_at, is_active, created_at, updated_at.
# Поле `refresh_token_id` та розгорнутий `refresh_token` не включені до `SessionSchema`
# для звичайного користувача, оскільки це може бути зайвою технічною інформацією.
# Якщо ця інформація потрібна (наприклад, для адміністрування сесій),
# можна створити розширену `AdminSessionSchema` або додати ці поля як опціональні
# і контролювати їх наявність на рівні ендпоінта.
# Поки що `SessionSchema` призначена для того, що бачить користувач у списку своїх активних сесій.
#
# `ip_address` в схемі як `str`.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# Все виглядає узгоджено.
#
# Немає схем для Create/Update для `SessionModel` з боку API, оскільки сесії
# зазвичай створюються та оновлюються внутрішньою логікою системи під час
# входу, оновлення токенів, виходу або автоматично за тайм-аутом.
# Якщо буде API для примусового завершення сесії, воно буде приймати `session_id`.
# Тому схеми Create/Update тут не потрібні.
# Схема `SessionListSchema` (закоментована) може бути корисною, якщо буде
# окремий ендпоінт для отримання списку сесій, але це можна реалізувати
# і за допомогою стандартної `PaginatedResponse[SessionSchema]`.
# Поки що окрема `SessionListSchema` не потрібна.

SessionSchema.model_rebuild()
