# backend/app/src/models/auth/token.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `RefreshTokenModel` для зберігання Refresh токенів.
Refresh токени використовуються для отримання нових Access токенів без необхідності
повторного введення облікових даних користувачем, поки Refresh токен є дійсним.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text # type: ignore
from sqlalchemy.dialects.postgresql import UUID, INET # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime, timedelta # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Успадковуємо від BaseModel для id, created_at, updated_at

class RefreshTokenModel(BaseModel):
    """
    Модель для зберігання Refresh токенів.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запису токена (успадковано).
                        Може використовуватися як jti (JWT ID) самого refresh токена.
        user_id (uuid.UUID): Ідентифікатор користувача, якому належить токен.
        token (str): Сам Refresh токен (захешований або його частина для перевірки).
                     Зберігати повний токен у відкритому вигляді не рекомендується.
                     Краще зберігати його хеш або непрозорий ідентифікатор.
                     Якщо сам `id` запису використовується як `jti` і передається в тілі JWT,
                     то тут можна зберігати, наприклад, хеш від сигнатури токена.
                     Або ж, якщо токен повністю генерується і зберігається тут, то це поле для нього.
                     **Рішення**: будемо зберігати тут унікальний рядок токена, який видається клієнту.
                                  Але в базі він буде захешований.
        hashed_token (str): Захешоване значення refresh токена. Токен, що видається клієнту,
                            хешується перед збереженням. Клієнт надсилає оригінальний токен,
                            сервер хешує його і порівнює з хешем в базі.
        expires_at (datetime): Дата та час закінчення терміну дії токена.
        is_revoked (bool): Прапорець, чи був токен відкликаний (наприклад, при виході з системи або зміні пароля).
        user_agent (str | None): User-Agent клієнта, для якого був виданий токен.
        ip_address (INET | None): IP-адреса клієнта.

        # Додаткові поля для безпеки та аудиту
        issued_at (datetime): Час видачі токена (може бути `created_at` з BaseModel).
        last_used_at (datetime | None): Час останнього використання токена.
        revoked_at (datetime | None): Час, коли токен був відкликаний.
        revocation_reason (str | None): Причина відкликання токена.

        created_at (datetime): Дата та час створення запису (успадковано, відповідає `issued_at`).
        updated_at (datetime): Дата та час останнього оновлення (успадковано, може оновлюватися при `last_used_at`).

    Зв'язки:
        user (relationship): Зв'язок з UserModel.
    """
    __tablename__ = "refresh_tokens"

    user_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Захешоване значення refresh токена.
    # Оригінальний токен генерується, видається клієнту, а його хеш зберігається тут.
    hashed_token: Column[str] = Column(String(255), nullable=False, unique=True, index=True)

    expires_at: Column[DateTime] = Column(DateTime(timezone=True), nullable=False, index=True)

    is_revoked: Column[bool] = Column(Boolean, default=False, nullable=False, index=True)
    revoked_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True)
    revocation_reason: Column[str | None] = Column(String(255), nullable=True) # Наприклад, 'user_logout', 'password_change', 'stolen'

    # Інформація про клієнта для безпеки та можливості відкликання сесій
    user_agent: Column[str | None] = Column(Text, nullable=True)
    ip_address: Column[INET | None] = Column(INET, nullable=True)

    # Час останнього використання токена. Може використовуватися для виявлення неактивних токенів
    # або для реалізації механізму "ковзного" терміну дії.
    last_used_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True)

    # Зв'язок з користувачем
    user = relationship("UserModel", back_populates="refresh_tokens")

    # `created_at` з BaseModel використовується як час видачі токена (`issued_at`).
    # `updated_at` з BaseModel може оновлюватися при зміні `last_used_at` або `is_revoked`.

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі RefreshTokenModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', user_id='{self.user_id}', expires_at='{self.expires_at}', is_revoked='{self.is_revoked}')>"

# TODO: Перевірити відповідність `technical-task.md` та `structure-claude-v3.md`.
# - "Аутентифікація - JWT токени + refresh токени" - ця модель для refresh токенів.
# - `structure-claude-v3.md` вказує `backend/app/src/models/auth/token.py`.
# Назва таблиці `refresh_tokens` є логічною.
# Поля `user_id`, `hashed_token`, `expires_at`, `is_revoked` є ключовими.
# Додаткові поля, такі як `user_agent`, `ip_address`, `last_used_at`, `revoked_at`, `revocation_reason`,
# покращують безпеку та можливості аудиту.
# Зв'язок з `UserModel` визначено.
# Використання `BaseModel` є доречним.
# `ondelete="CASCADE"` для `user_id` означає, що при видаленні користувача його токени також будуть видалені.

# TODO: Розглянути стратегію для `hashed_token`:
# 1. Зберігати хеш від випадково згенерованого рядка, який є самим refresh токеном.
#    При перевірці: клієнт надсилає оригінальний токен, сервер хешує його і порівнює з хешем в базі.
#    Це безпечно, оскільки оригінальний токен не зберігається.
# 2. `id` запису (UUID) використовується як `jti` в JWT refresh токені.
#    Сам JWT refresh токен не зберігається в базі, тільки його `jti` (тобто `id`), `user_id`, `expires_at`, `is_revoked`.
#    При перевірці: валідується JWT, з нього витягується `jti`, шукається запис в БД за `id=jti`.
#    Цей підхід не потребує поля `hashed_token`.
# Поточна реалізація використовує варіант 1, що є поширеною практикою для непрозорих токенів.
# Якщо refresh токени будуть JWT, то поле `hashed_token` може бути непотрібним,
# а `id` буде `jti`. Однак, зберігання `hashed_token` дозволяє мати refresh токени,
# які не є JWT, що може бути простіше в деяких випадках.
# Залишаємо `hashed_token` для гнучкості.

# TODO: Подумати про механізм автоматичного очищення застарілих (expired) та відкликаних (revoked) токенів
# за допомогою фонової задачі (cron).
# Наприклад, токени, `expires_at` яких минув більше ніж N днів тому, або `revoked_at` яких був давно.
# Це допоможе підтримувати розмір таблиці під контролем.
