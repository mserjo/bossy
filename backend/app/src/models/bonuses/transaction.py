# backend/app/src/models/bonuses/transaction.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `TransactionModel` для зберігання всіх транзакцій
по рахунках користувачів. Транзакції фіксують будь-які зміни балансу:
нарахування бонусів за завдання, списання за нагороди, штрафи, перекази тощо.
"""

from sqlalchemy import Column, ForeignKey, Numeric, Text, String, DateTime, Index  # type: ignore # Для mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column # type: ignore
from typing import Optional, Dict, Any, List, TYPE_CHECKING # Додано List
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом
from decimal import Decimal # Для Numeric полів

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

if TYPE_CHECKING:
    from backend.app.src.models.bonuses.account import AccountModel
    from backend.app.src.models.auth.user import UserModel
    from backend.app.src.models.bonuses.bonus_adjustment import BonusAdjustmentModel


class TransactionModel(BaseModel):
    """
    Модель для транзакцій по рахунках користувачів.
    (Атрибути id, created_at, updated_at, created_by_user_id, updated_by_user_id успадковані)
    """
    __tablename__ = "transactions"

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    transaction_type_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    source_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    # TODO: Додати індекс на (source_entity_type, source_entity_id) через міграції.

    related_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_transactions_related_user_id", ondelete="SET NULL"), nullable=True, index=True)

    # Перейменовано з 'metadata' для уникнення конфлікту з зарезервованим іменем SQLAlchemy
    additional_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    balance_after_transaction: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    # --- Зв'язки (Relationships) ---
    account: Mapped["AccountModel"] = relationship(back_populates="transactions", lazy="selectin")
    # TODO: Узгодити back_populates="related_transactions" з UserModel
    related_user: Mapped[Optional["UserModel"]] = relationship(foreign_keys=[related_user_id], back_populates="related_transactions", lazy="selectin")

    # Зв'язок з BonusAdjustmentModel (якщо транзакція створена через коригування)
    # Потрібно додати `bonus_adjustment = relationship(back_populates="transaction")` в BonusAdjustmentModel
    # І тут:
    source_adjustment: Mapped[Optional["BonusAdjustmentModel"]] = relationship(back_populates="transaction", lazy="selectin")

    __table_args__ = (
        Index('ix_transactions_source_entity', 'source_entity_type', 'source_entity_id'),
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}', account_id='{self.account_id}', amount='{self.amount}', type='{self.transaction_type_code}')>"

# Примітки до змін:
# - Переведено на стиль SQLAlchemy 2.0 (Mapped, mapped_column).
# - Використано `Decimal` для `amount` та `balance_after_transaction`.
# - `ondelete="CASCADE"` для `account_id`.
# - `ondelete="SET NULL"` для `related_user_id`.
# - Узгоджено `back_populates` для `account` та `related_user` (з TODO для UserModel).
# - Додано зворотний зв'язок `source_adjustment` до `BonusAdjustmentModel`.
#
# Питання `bonus_type_code` в транзакції:
# Поточна `AccountModel` має `bonus_type_code`. Отже, валюта транзакції визначається
# валютою рахунку на момент транзакції. Якщо `AccountModel.bonus_type_code`
# може змінюватися, це може призвести до неконсистентності історії, якщо не реалізовано
# механізм конвертації або створення нових рахунків.
# Якщо ж `AccountModel.bonus_type_code` фіксований для рахунку, то все гаразд.
# Для більшої надійності історії, особливо якщо типи бонусів можуть еволюціонувати
# або група може змінювати свій основний тип бонусів, зберігання
# `bonus_type_code_at_transaction_time` в `TransactionModel` було б кращим рішенням.
# Але це ускладнює модель `AccountModel.balance`, якщо він один.
# Поки що залишаю без `bonus_type_code` в `TransactionModel`, покладаючись на
# `AccountModel.bonus_type_code`.
#
# Все готово.
