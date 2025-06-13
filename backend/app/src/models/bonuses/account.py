# backend/app/src/models/bonuses/account.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для сутності "Рахунок Користувача" (UserAccount).

Цей модуль визначає модель `UserAccount`, яка представляє баланс бонусів
(або іншої внутрішньої валюти) для кожного користувача в межах кожної групи.
"""
from datetime import datetime  # Необхідно для TYPE_CHECKING та __main__
from typing import TYPE_CHECKING, List, Optional
from decimal import Decimal

from sqlalchemy import String, ForeignKey, Numeric, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів та міксинів
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # Для відстеження часу створення/оновлення рахунку
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.groups.group import Group
    from backend.app.src.models.bonuses.transaction import AccountTransaction


class UserAccount(Base, TimestampedMixin):
    """
    Модель Рахунку Користувача.

    Зберігає поточний баланс користувача в певній групі, а також валюту цього балансу.
    Кожен користувач має окремий рахунок для кожної групи, до якої він належить.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор рахунку.
        user_id (Mapped[int]): ID користувача, якому належить рахунок.
        group_id (Mapped[int]): ID групи, в межах якої ведеться цей рахунок.
        balance (Mapped[Decimal]): Поточний баланс на рахунку.
        currency (Mapped[str]): Назва валюти/одиниць виміру бонусів (наприклад, "бали").

        user (Mapped["User"]): Зв'язок з моделлю `User`.
        group (Mapped["Group"]): Зв'язок з моделлю `Group`.
        transactions (Mapped[List["AccountTransaction"]]): Список транзакцій по цьому рахунку.
        created_at, updated_at: Успадковано від `TimestampedMixin`.
    """
    __tablename__ = "user_accounts"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор рахунку користувача"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', name='fk_user_account_user_id', ondelete="CASCADE"),
        nullable=False,
        comment="ID користувача, якому належить рахунок"
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey('groups.id', name='fk_user_account_group_id', ondelete="CASCADE"),
        nullable=False,
        comment="ID групи, до якої прив'язаний рахунок"
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False, comment="Поточний баланс на рахунку"
    )
    # TODO i18n: Локалізація значення за замовчуванням 'бали' для поля currency.
    currency: Mapped[str] = mapped_column(
        String(10), default='бали', nullable=False, comment="Валюта рахунку (наприклад, бали, очки)"
    )

    # Обмеження та індекси
    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', name='uq_user_group_account'),
        # Кожен користувач має лише один рахунок на групу
        Index('ix_user_accounts_user_group_balance', 'user_id', 'group_id', 'balance'),
    # Індекс для швидкого пошуку балансу
    )

    # --- Зв'язки (Relationships) ---
    user: Mapped["User"] = relationship(lazy="selectin")  # back_populates="accounts" можна додати до User
    group: Mapped["Group"] = relationship(lazy="selectin")  # back_populates="user_accounts" можна додати до Group

    transactions: Mapped[List["AccountTransaction"]] = relationship(
        back_populates="account", cascade="all, delete-orphan", lazy="selectin"
    )

    # Поля для __repr__
    # `id` автоматично додається через Base.__repr__
    # `created_at`, `updated_at` успадковуються з TimestampedMixin._repr_fields
    _repr_fields = ("user_id", "group_id", "balance", "currency")


if __name__ == "__main__":
    # Демонстраційний блок для моделі UserAccount.
    logger.info("--- Модель Рахунку Користувача (UserAccount) ---")
    logger.info(f"Назва таблиці: {UserAccount.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = [
        'id', 'user_id', 'group_id', 'balance', 'currency',
        'created_at', 'updated_at'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['user', 'group', 'transactions']
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_account = UserAccount(
        id=1,
        user_id=101,
        group_id=202,
        balance=Decimal("150.75"),
        currency="бали"
    )
    # Імітуємо часові мітки
    example_account.created_at = datetime.now(
        tz=datetime.now().astimezone().tzinfo)  # Використовуємо локальний часовий пояс для прикладу
    example_account.updated_at = datetime.now(tz=datetime.now().astimezone().tzinfo)

    logger.info(f"\nПриклад екземпляра UserAccount (без сесії):\n  {example_account}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <UserAccount(id=1, user_id=101, group_id=202, balance=Decimal('150.75'), currency='бали', created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
