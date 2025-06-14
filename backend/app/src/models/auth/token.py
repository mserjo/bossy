# backend/app/src/models/auth/token.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для сутності "Токен Оновлення" (RefreshToken).

Цей модуль визначає модель `RefreshToken`, яка використовується для зберігання
токенів оновлення JWT. Токени оновлення дозволяють користувачам отримувати
нові токени доступу без повторного введення облікових даних.
"""
from datetime import datetime
from typing import TYPE_CHECKING, List  # List тут не потрібен, якщо немає зворотного зв'язку List

from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import Base  # Успадковуємо від Base, а не BaseMainModel
from backend.app.src.models.mixins import TimestampedMixin  # Додаємо часові мітки
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User  # Для зв'язку user


class RefreshToken(Base, TimestampedMixin):
    """
    Модель токена оновлення.

    Зберігає токени оновлення, пов'язані з користувачами, їх термін дії
    та часові мітки створення/оновлення.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису токена.
        token (Mapped[str]): Сам JWT токен оновлення (хешований або зашифрований у продакшені).
                              Для простоти тут зберігається як є, але це НЕБЕЗПЕЧНО для реальних систем.
                              TODO: Розглянути хешування або шифрування значення токена перед збереженням.
        user_id (Mapped[int]): Зовнішній ключ до користувача, якому належить токен.
        expires_at (Mapped[datetime]): Дата та час закінчення терміну дії токена.
        user (Mapped["User"]): Зв'язок з моделлю User.
        created_at, updated_at: Успадковано від `TimestampedMixin`.
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор токена оновлення"
    )
    # TODO: У продакшені значення `token` слід хешувати перед збереженням для безпеки.
    #       Довжина 512 обрана з запасом для JWT. Якщо хешується, довжина може бути іншою (наприклад, 255 для SHA256 hex).
    token: Mapped[str] = mapped_column(
        String(512), unique=True, index=True, nullable=False,
        comment="Значення токена оновлення (в реальності - його хеш)"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', name='fk_refresh_token_user_id', ondelete='CASCADE'),
        nullable=False,
        comment="ID користувача, якому належить токен"
    )
    expires_at: Mapped[datetime] = mapped_column(
        nullable=False, comment="Час закінчення терміну дії токена"
    )

    # Зв'язок з користувачем
    user: Mapped["User"] = relationship(back_populates="refresh_tokens", lazy="selectin")

    # Поля для __repr__
    # `id` автоматично додається через Base.__repr__
    # `created_at`, `updated_at` успадковуються з TimestampedMixin._repr_fields
    _repr_fields = ("user_id", "expires_at")


if __name__ == "__main__":
    # Демонстраційний блок для моделі RefreshToken.
    logger.info("--- Модель Токена Оновлення (RefreshToken) ---")
    logger.info(f"Назва таблиці: {RefreshToken.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = ['id', 'token', 'user_id', 'expires_at', 'created_at', 'updated_at']
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    logger.info(f"  - user (до User)")

    # Приклад створення екземпляра (без взаємодії з БД)
    from datetime import timedelta

    # Потрібно імітувати User для зв'язку, якщо __repr__ його використовує,
    # але наш __repr__ з Base використовує лише mapped_column поля.

    example_token = RefreshToken(
        id=1,
        token="some_very_long_refresh_jwt_token_string_example_value",
        user_id=101,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    # Імітуємо часові мітки, які зазвичай встановлює БД або міксин
    example_token.created_at = datetime.now(timezone.utc)
    example_token.updated_at = datetime.now(timezone.utc)

    logger.info(f"\nПриклад екземпляра RefreshToken (без сесії):\n  {example_token}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <RefreshToken(id=1, user_id=101, expires_at=..., created_at=..., updated_at=...)>
    # Поле 'token' не включено в _repr_fields за замовчуванням через його довжину та чутливість.

    logger.info("\nВАЖЛИВО: У реальному застосунку поле 'token' повинно зберігатися хешованим!")
    logger.info("Примітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
