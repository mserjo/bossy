# backend/app/src/models/files/avatar.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для сутності "Аватар Користувача" (UserAvatar).

Цей модуль визначає модель `UserAvatar`, яка пов'язує користувача (`User`)
з його активним аватаром (`FileRecord`). Це дозволяє користувачам мати
один основний аватар, а також потенційно зберігати історію аватарів (хоча
поточна модель зосереджена на одному активному).
"""
from datetime import datetime, timezone  # timezone для __main__
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Boolean, func  # Boolean для is_active, func для server_default в TimestampedMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів та міксинів
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # `created_at` як час встановлення аватара
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.files.file import FileRecord


class UserAvatar(Base, TimestampedMixin):
    """
    Модель Аватара Користувача.

    Зберігає зв'язок між користувачем та файлом, що використовується як його аватар.
    Поле `created_at` з `TimestampedMixin` використовується як час встановлення (`set_at`).
    Поточна реалізація передбачає один активний аватар на користувача через `unique=True` на `user_id`.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису аватара.
        user_id (Mapped[int]): ID користувача, якому належить аватар (унікальний, зовнішній ключ).
        file_record_id (Mapped[int]): ID запису файлу, що є аватаром (унікальний, зовнішній ключ).
        is_active (Mapped[bool]): Прапорець, чи є цей аватар поточним активним для користувача.
                                  (З `unique=True` на `user_id`, це поле може бути менш критичним,
                                  але корисне для логіки деактивації старого аватара при зміні).

        user (Mapped["User"]): Зв'язок з моделлю `User`.
        file_record (Mapped["FileRecord"]): Зв'язок з моделлю `FileRecord`.
        created_at (Mapped[datetime]): Час встановлення аватара (успадковано).
        updated_at (Mapped[datetime]): Час оновлення запису (успадковано).
    """
    __tablename__ = "user_avatars"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор запису аватара"
    )
    # Один користувач має один запис UserAvatar, що вказує на поточний аватар.
    # Якщо потрібна історія аватарів, unique=True слід прибрати та керувати is_active.
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', name='fk_user_avatar_user_id', ondelete="CASCADE"),
        unique=True,  # Гарантує, що користувач має лише один запис UserAvatar (один активний аватар)
        nullable=False,
        comment="ID користувача, якому належить аватар"
    )
    # Один файл може бути аватаром лише одного користувача (якщо файл не використовується повторно).
    # Якщо один файл може бути аватаром для різних сутностей, unique=True тут не потрібен.
    # Для аватарів користувачів зазвичай унікальність file_record_id є логічною.
    file_record_id: Mapped[int] = mapped_column(
        ForeignKey('file_records.id', name='fk_user_avatar_file_record_id', ondelete="RESTRICT"),
        # Не дозволяти видаляти файл, якщо він є активним аватаром
        unique=True,
        # Гарантує, що один файл використовується лише як один аватар (запобігає спільному використанню одного FileRecord як аватара для різних UserAvatar записів)
        nullable=False,
        comment="ID запису файлу, що є аватаром"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True, comment="Чи є цей аватар поточним активним"
    )
    # `created_at` з TimestampedMixin використовується як `set_at` (час встановлення аватара)

    # --- Зв'язки (Relationships) ---
    user: Mapped["User"] = relationship(back_populates="avatar", lazy="selectin")
    file_record: Mapped["FileRecord"] = relationship(
        lazy="selectin")  # back_populates="user_avatar_link" можна додати до FileRecord

    # Поля для __repr__
    _repr_fields = ["id", "user_id", "file_record_id", "is_active"]  # created_at з TimestampedMixin


if __name__ == "__main__":
    # Демонстраційний блок для моделі UserAvatar.
    logger.info("--- Модель Аватара Користувача (UserAvatar) ---")
    logger.info(f"Назва таблиці: {UserAvatar.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = [
        'id', 'user_id', 'file_record_id', 'is_active',
        'created_at', 'updated_at'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['user', 'file_record']
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_avatar_link = UserAvatar(
        id=1,
        user_id=101,
        file_record_id=1,  # ID запису FileRecord для файлу аватара
        is_active=True
    )
    # Імітуємо часові мітки (created_at - час встановлення)
    example_avatar_link.created_at = datetime.now(tz=timezone.utc)
    example_avatar_link.updated_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра UserAvatar (без сесії):\n  {example_avatar_link}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <UserAvatar(id=1, user_id=101, file_record_id=1, is_active=True, created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
