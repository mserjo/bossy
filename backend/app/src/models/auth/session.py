# backend/app/src/models/auth/session.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `SessionModel` для зберігання інформації про активні сесії користувачів.
Хоча система використовує JWT токени, які є stateless, ця модель може бути корисною для:
1.  Відстеження активних сесій (пристроїв/браузерів, з яких увійшов користувач).
2.  Можливості для користувача переглядати свої активні сесії та примусово завершувати їх (відкликати Refresh токени, пов'язані з сесією).
3.  Збору аудиторської інформації про входи в систему.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text # type: ignore
from sqlalchemy.dialects.postgresql import UUID, INET # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Успадковуємо від BaseModel

class SessionModel(BaseModel):
    """
    Модель для зберігання інформації про сесії користувачів.
    Кожен запис може представляти активний вхід користувача з певного пристрою/браузера.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор сесії (успадковано).
        user_id (uuid.UUID): Ідентифікатор користувача, якому належить сесія.
        refresh_token_id (uuid.UUID | None): Ідентифікатор Refresh токена, пов'язаного з цією сесією.
                                             Може бути NULL, якщо сесія не використовує refresh токени
                                             або якщо це інший тип сесії.
        user_agent (str | None): User-Agent клієнта (браузер, мобільний додаток).
        ip_address (INET | None): IP-адреса, з якої була розпочата сесія.
        last_activity_at (datetime): Час останньої активності в межах цієї сесії.
        expires_at (datetime | None): Час, коли сесія (або пов'язаний з нею токен) закінчується.
                                     Може бути таким же, як `expires_at` у RefreshTokenModel.
        is_active (bool): Прапорець, чи є сесія наразі активною. Може змінюватися при виході.

        created_at (datetime): Дата та час створення сесії (час входу) (успадковано).
        updated_at (datetime): Дата та час останнього оновлення (наприклад, при оновленні `last_activity_at`) (успадковано).

    Зв'язки:
        user (relationship): Зв'язок з UserModel.
        refresh_token (relationship): Зв'язок з RefreshTokenModel (необов'язковий).
    """
    __tablename__ = "sessions"

    user_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Зв'язок з RefreshTokenModel. Сесія може бути тісно пов'язана з одним refresh токеном.
    # Коли refresh токен відкликається, відповідна сесія також може вважатися завершеною.
    # `nullable=True`, оскільки можуть бути інші механізми сесій або просто логування входів.
    # Однак, для JWT-based системи, зв'язок з refresh токеном є логічним.
    # `unique=True` гарантує, що один refresh токен пов'язаний лише з однією сесією.
    refresh_token_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("refresh_tokens.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)

    user_agent: Column[str | None] = Column(Text, nullable=True)
    ip_address: Column[INET | None] = Column(INET, nullable=True)

    # Час останньої активності. Може оновлюватися при кожному запиті з Access токеном,
    # якщо Access токен містить ідентифікатор сесії, або при використанні Refresh токена.
    last_activity_at: Column[DateTime] = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow) # Або func.now()

    # Час закінчення сесії. Може бути пов'язаний з `expires_at` відповідного Refresh токена.
    expires_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True, index=True)

    # Прапорець активності сесії. Може встановлюватися в `False` при виході або відкликанні токена.
    # `is_active` може дублювати `is_revoked` з `RefreshTokenModel`, якщо сесія жорстко прив'язана до токена.
    # Однак, це поле може бути корисним для швидкої перевірки активних сесій.
    # TODO: Узгодити логіку з `RefreshTokenModel.is_revoked`.
    # Можливо, `is_active` тут = `NOT RefreshTokenModel.is_revoked` AND `expires_at > now()`.
    # Поки що залишаємо як окреме поле.
    is_active: Column[bool] = Column(Boolean, default=True, nullable=False, index=True)

    # Зв'язок з користувачем
    user = relationship("UserModel", back_populates="sessions")

    # Зв'язок з Refresh токеном (один-до-одного, оскільки refresh_token_id є unique)
    # Використовуємо back_populates для узгодженості
    refresh_token_details: Mapped[Optional["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel",
        back_populates="session_info", # Має відповідати назві зв'язку в RefreshTokenModel
        foreign_keys=[refresh_token_id],
        uselist=False
    )

    # `created_at` з BaseModel використовується як час початку сесії (входу).
    # `updated_at` з BaseModel може оновлюватися при зміні `last_activity_at` або `is_active`.

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі SessionModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', user_id='{self.user_id}', ip='{self.ip_address}', active='{self.is_active}')>"

# TODO: Перевірити відповідність `technical-task.md` та `structure-claude-v3.md`.
# - `technical-task.md` не згадує явно таблицю сесій, але функціонал "переглядати свої активні сесії та примусово завершувати їх"
#   потребує такого зберігання інформації.
# - `structure-claude-v3.md` вказує `backend/app/src/models/auth/session.py`.
# Назва таблиці `sessions` є логічною.
# Поля `user_id`, `user_agent`, `ip_address`, `last_activity_at`, `expires_at`, `is_active` є доречними.
# Зв'язок з `UserModel` та `RefreshTokenModel` визначено.
# `ondelete="CASCADE"` для `user_id` означає, що при видаленні користувача його сесії також будуть видалені.
# `ondelete="SET NULL"` для `refresh_token_id` означає, що якщо refresh токен видаляється,
# то сесія не видаляється, а просто втрачає зв'язок з цим токеном (може стати неактивною).
# Це дозволяє зберегти історію сесій, навіть якщо токени були видалені.

# TODO: Подумати про механізм очищення застарілих/неактивних сесій (аналогічно до RefreshTokenModel).
# Наприклад, сесії, `expires_at` яких давно минув, або `is_active = False` і `updated_at` був давно.

# TODO: Розглянути, чи потрібен `id` сесії, якщо `refresh_token_id` є унікальним ідентифікатором сесії.
# Якщо сесія завжди пов'язана з refresh токеном, то `refresh_token_id` міг би бути первинним ключем.
# Однак, наявність власного `id` (UUID) для сесії надає більшу гнучкість, якщо в майбутньому
# з'являться сесії, не пов'язані з refresh токенами, або якщо потрібно посилатися на сесію незалежно.
# Поточний підхід з власним `id` та `unique` `refresh_token_id` є прийнятним.
# `BaseModel` надає `id` автоматично.
