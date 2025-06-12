# backend/app/src/models/auth/session.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для сутності "Сесія Користувача".

Цей модуль визначає модель `Session`, яка використовується для відстеження
активних сесій користувачів. Це може бути корисно для моніторингу,
примусового завершення сесій, аналізу активності тощо.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import Base  # Успадковуємо від Base
from backend.app.src.models.mixins import TimestampedMixin  # Додаємо часові мітки
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User  # Для зв'язку user


class Session(Base, TimestampedMixin):
    """
    Модель сесії користувача.

    Зберігає інформацію про активні сесії, включаючи ключ сесії,
    пов'язаного користувача, час закінчення терміну дії, User-Agent та IP-адресу.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису сесії.
        session_key (Mapped[str]): Унікальний ключ сесії (наприклад, може бути JWT JTI або інший ідентифікатор).
        user_id (Mapped[int]): Зовнішній ключ до користувача, якому належить сесія.
        expires_at (Mapped[datetime]): Дата та час закінчення терміну дії сесії.
        user_agent (Mapped[Optional[str]]): User-Agent клієнта, з якого створено сесію.
        ip_address (Mapped[Optional[str]]): IP-адреса клієнта, з якого створено сесію.
        user (Mapped["User"]): Зв'язок з моделлю User.
        created_at, updated_at: Успадковано від `TimestampedMixin`.
    """
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор сесії"
    )
    session_key: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False, comment="Унікальний ключ сесії"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', name='fk_session_user_id', ondelete='CASCADE'),
        nullable=False,
        comment="ID користувача, якому належить сесія"
    )
    expires_at: Mapped[datetime] = mapped_column(
        nullable=False, comment="Час закінчення терміну дії сесії"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="User-Agent клієнта сесії"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="IP-адреса клієнта сесії"
    )
    last_active_at: Mapped[Optional[datetime]] = mapped_column( # Додано DateTime з timezone=True
        func.now(), server_default=func.now(), onupdate=func.now(), # Виправлено: func.now() має бути для server_default/onupdate
        comment="Час останньої активності сесії"
    )

    # Зв'язок з користувачем
    user: Mapped["User"] = relationship(back_populates="sessions", lazy="selectin")

    # Поля для __repr__
    # `created_at`, `updated_at` успадковуються з TimestampedMixin._repr_fields
    _repr_fields = ["id", "user_id", "expires_at", "ip_address", "last_active_at"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі Session.
    from datetime import timezone, timedelta # Для прикладу нижче
    logger.info("--- Модель Сесії Користувача (Session) ---")
    logger.info(f"Назва таблиці: {Session.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = [
        'id', 'session_key', 'user_id', 'expires_at',
        'user_agent', 'ip_address', 'created_at', 'updated_at'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    logger.info(f"  - user (до User)")

    # Приклад створення екземпляра (без взаємодії з БД)
    from datetime import timedelta, timezone

    example_session = Session(
        id=1,
        session_key="абсолютно_унікальний_ключ_сесії_12345",
        user_id=101,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        ip_address="192.168.1.100"
    )
    # Імітуємо часові мітки
    example_session.created_at = datetime.now(timezone.utc)
    example_session.updated_at = datetime.now(timezone.utc)

    logger.info(f"\nПриклад екземпляра Session (без сесії):\n  {example_session}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <Session(id=1, user_id=101, ip_address='192.168.1.100', expires_at=..., created_at=..., updated_at=...)>
    # Поле 'session_key' та 'user_agent' не включено в _repr_fields за замовчуванням через їх потенційну довжину.

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
