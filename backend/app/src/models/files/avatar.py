# backend/app/src/models/files/avatar.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `AvatarModel` для зберігання інформації
про аватари користувачів. Аватар - це специфічний тип файлу (`FileModel`),
пов'язаний з користувачем (`UserModel`).
"""
from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, Boolean, Index, text # type: ignore # Замінено UniqueConstraint на Index
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column  # type: ignore # Додано mapped_column
import uuid # Для роботи з UUID

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import UserModel
    from backend.app.src.models.files.file import FileModel


class AvatarModel(BaseModel):
    """
    Модель для зв'язку користувача з його аватаром (файлом).
    Кожен користувач може мати один активний аватар. Можлива історія аватарів.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запису аватара (успадковано).
        user_id (uuid.UUID): Ідентифікатор користувача, якому належить аватар.
        file_id (uuid.UUID): Ідентифікатор файлу (з FileModel), який є аватаром.
        is_current (bool): Прапорець, чи є цей аватар поточним (активним) для користувача.
                           Дозволяє зберігати історію аватарів.

        created_at (datetime): Дата та час встановлення аватара (успадковано).
        updated_at (datetime): Дата та час останнього оновлення (успадковано).

    Зв'язки:
        user (relationship): Зв'язок з UserModel.
        file (relationship): Зв'язок з FileModel.
    """
    __tablename__ = "avatars"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Посилання на запис у FileModel, де зберігаються метадані файлу аватара.
    # TODO: Замінити "files.id" на константу або імпорт моделі FileModel.
    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    # `unique=True` для file_id було знято, оскільки унікальність має бути на (user_id, is_current=True).
    # Унікальність `file_id` в `FileModel.storage_path` вже є.

    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    # Якщо `is_current` = True, то це поточний аватар користувача.
    # Має бути лише один запис з `is_current=True` для кожного `user_id`.

    # --- Зв'язки (Relationships) ---
    # TODO: Узгодити back_populates="avatars" з UserModel
    user: Mapped["UserModel"] = relationship(foreign_keys=[user_id], back_populates="avatars", lazy="selectin")

    # TODO: Узгодити back_populates="avatar_entry" з FileModel
    file: Mapped["FileModel"] = relationship(foreign_keys=[file_id], back_populates="avatar_entry", lazy="selectin")

    # Обмеження унікальності:
    # Для кожного user_id може бути лише один аватар з is_current = True.
    # Це реалізується через частковий унікальний індекс.
    # Важливо: для часткового індексу поле `is_current` має бути частиною самого UniqueConstraint.
    # Однак, логіка "тільки один is_current=True на user_id" краще реалізується так:
    # UniqueConstraint('user_id', name='uq_user_current_avatar', postgresql_where=text("is_current IS TRUE"))
    # Або через виключення (exclusion constraint), якщо БД підтримує.
    # Використовуємо Index для часткового унікального індексу.
    __table_args__ = (
        Index(
            'ix_user_current_avatar_unique', # Назва індексу
            user_id,                       # Поле для індексування
            unique=True,
            postgresql_where=(is_current.is_(True)) # Умова для часткового індексу
        ),
    )

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі AvatarModel.
        """
        return f"<{self.__class__.__name__}(user_id='{self.user_id}', file_id='{self.file_id}', is_current='{self.is_current}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "підтримка завантаження файлів (аватари...)" - ця модель зв'язує користувача з файлом аватара.

# TODO: Узгодити назву таблиці `avatars` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля: `user_id`, `file_id`, `is_current`.
# `ondelete="CASCADE"` для зовнішніх ключів.
# `UniqueConstraint` для `(user_id, is_current=True)` забезпечує, що користувач має лише один активний аватар.
# Зв'язки визначені.
# Все виглядає логічно для управління аватарами користувачів, включаючи можливість зберігання історії.
# При завантаженні нового аватара, попередній запис AvatarModel для цього користувача
# (де is_current=True) має отримати is_current=False, а для нового запису is_current=True.
# Це реалізується на сервісному рівні.
# `FileModel` для цього аватара матиме `file_category_code = "USER_AVATAR"`.
# Поле `file_id` тут НЕ унікальне глобально, бо один файл теоретично може бути використаний
# (хоча для аватарів це малоймовірно, кожен завантажує свій).
# Але якщо є дефолтні аватари, то один `file_id` може бути у багатьох записах `AvatarModel`
# (але лише в одному з `is_current=True` для кожного користувача).
# Тому `unique=True` для `file_id` було знято.
# Головне обмеження - `UniqueConstraint('user_id', name='uq_user_current_avatar', postgresql_where=(is_current == True))`.
# Воно гарантує, що для кожного `user_id` існує не більше одного запису, де `is_current` встановлено в `True`.
# Це дозволяє мати історію аватарів (старі записи з `is_current=False`) і один активний.
# `postgresql_where` - специфічно для PostgreSQL, для інших БД синтаксис може відрізнятися.
# Alembic має генерувати відповідний DDL.
