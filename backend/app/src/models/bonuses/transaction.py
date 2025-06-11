# backend/app/src/models/bonuses/transaction.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для сутності "Транзакція по Рахунку" (AccountTransaction).

Цей модуль визначає модель `AccountTransaction`, яка фіксує всі зміни
балансу на рахунках користувачів (`UserAccount`), такі як нарахування бонусів,
списання за нагороди, штрафи тощо.
"""
from datetime import datetime, timezone  # timezone для __main__
from typing import TYPE_CHECKING, Optional
from decimal import Decimal

from sqlalchemy import String, ForeignKey, Text, Numeric, func  # func для server_default в TimestampedMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів та Enum
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # `created_at` як час транзакції
from backend.app.src.core.dicts import TransactionType  # Enum для типів транзакцій
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.bonuses.account import UserAccount
    from backend.app.src.models.tasks.completion import TaskCompletion
    from backend.app.src.models.bonuses.reward import Reward  # Модель Нагороди
    from backend.app.src.models.auth.user import User  # Користувач, що створив транзакцію (якщо є)


class AccountTransaction(Base, TimestampedMixin):
    """
    Модель Транзакції по Рахунку Користувача.

    Зберігає інформацію про кожну операцію, що змінює баланс користувача.
    Поле `created_at` з `TimestampedMixin` використовується як час проведення транзакції.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор транзакції.
        account_id (Mapped[int]): ID рахунку користувача, до якого відноситься транзакція.
        transaction_type (Mapped[str]): Тип транзакції (наприклад, "credit", "debit").
                                        Використовує значення з `core.dicts.TransactionType`.
        amount (Mapped[Decimal]): Сума транзакції. Позитивна для нарахувань, негативна для списань.
                                  Або завжди позитивна, а напрямок визначається `transaction_type`.
                                  (Поточна реалізація: сума як є, тип визначає операцію).
        description (Mapped[Optional[str]]): Опис транзакції (наприклад, "Бонус за завдання Х", "Покупка нагороди Y").
        related_task_completion_id (Mapped[Optional[int]]): ID пов'язаного виконання завдання (якщо транзакція є результатом завдання).
        related_reward_id (Mapped[Optional[int]]): ID пов'язаної отриманої нагороди (якщо транзакція є покупкою нагороди).
        created_by_user_id (Mapped[Optional[int]]): ID користувача (зазвичай адміністратора), який ініціював ручну транзакцію.
                                                    NULL для автоматичних системних транзакцій.

        account (Mapped["UserAccount"]): Зв'язок з рахунком користувача.
        task_completion (Mapped[Optional["TaskCompletion"]]): Зв'язок з виконанням завдання.
        reward (Mapped[Optional["Reward"]]): Зв'язок з отриманою нагородою.
        created_by (Mapped[Optional["User"]]): Зв'язок з користувачем-ініціатором транзакції.
        created_at, updated_at: Успадковано. `created_at` - час транзакції.
    """
    __tablename__ = "account_transactions"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор транзакції"
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey('user_accounts.id', name='fk_account_transaction_account_id', ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID рахунку користувача, до якого відноситься транзакція"
    )

    # Використовуємо значення з Enum TransactionType
    # TODO: Переконатися, що SQLEnum імпортовано та використовується, якщо тип колонки в БД є Enum.
    # transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType), nullable=False)
    transaction_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Тип транзакції (credit, debit, refund тощо)"
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, comment="Сума транзакції"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Опис або призначення транзакції"
    )

    # Зв'язки з іншими сутностями, що могли спричинити транзакцію
    related_task_completion_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('task_completions.id', name='fk_account_transaction_task_completion_id', ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID виконання завдання, що спричинило транзакцію (якщо є)"
    )
    related_reward_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('rewards.id', name='fk_account_transaction_reward_id', ondelete="SET NULL"),
        # 'rewards' - назва таблиці для нагород
        nullable=True,
        index=True,
        comment="ID отриманої нагороди, що спричинила транзакцію (якщо є)"
    )
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('users.id', name='fk_account_transaction_creator_id', ondelete="SET NULL"),
        nullable=True,  # NULL для системних/автоматичних транзакцій
        comment="ID користувача (адміністратора), який створив ручну транзакцію"
    )

    # --- Зв'язки (Relationships) ---
    account: Mapped["UserAccount"] = relationship(back_populates="transactions", lazy="selectin")
    task_completion: Mapped[Optional["TaskCompletion"]] = relationship(
        lazy="selectin")  # Немає back_populates, якщо TaskCompletion не має списку транзакцій
    reward: Mapped[Optional["Reward"]] = relationship(
        lazy="selectin")  # Немає back_populates, якщо Reward не має списку транзакцій
    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_user_id], lazy="selectin")

    # Поля для __repr__
    _repr_fields = ["id", "account_id", "transaction_type", "amount"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі AccountTransaction.
    logger.info("--- Модель Транзакції по Рахунку (AccountTransaction) ---")
    logger.info(f"Назва таблиці: {AccountTransaction.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = [
        'id', 'account_id', 'transaction_type', 'amount', 'description',
        'related_task_completion_id', 'related_reward_id', 'created_by_user_id',
        'created_at', 'updated_at'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['account', 'task_completion', 'reward', 'created_by']
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_transaction = AccountTransaction(
        id=1,
        account_id=1,  # ID рахунку UserAccount
        transaction_type=TransactionType.CREDIT.value,  # Використання значення Enum
        amount=Decimal("25.50"),
        description="Бонус за виконання завдання #123"  # TODO i18n
    )
    # Імітуємо часові мітки
    example_transaction.created_at = datetime.now(tz=timezone.utc)
    example_transaction.updated_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра AccountTransaction (без сесії):\n  {example_transaction}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <AccountTransaction(id=1, account_id=1, transaction_type='credit', amount=Decimal('25.50'), created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
    logger.info(f"Використовується TransactionType Enum для поля 'transaction_type', наприклад: TransactionType.DEBIT = '{TransactionType.DEBIT.value}'")
