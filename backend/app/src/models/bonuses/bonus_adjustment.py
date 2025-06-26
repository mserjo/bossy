# backend/app/src/models/bonuses/bonus_adjustment.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `BonusAdjustmentModel`
для ручного коригування бонусів адміністратором.
Це дозволяє додавати або списувати бонуси користувачам поза стандартними процесами
(виконання завдань, купівля нагород).
"""

from sqlalchemy import Column, ForeignKey, Numeric, Text, String # type: ignore # Для mapped_column у ForeignKey
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column # type: ignore
from typing import Optional, List, TYPE_CHECKING
import uuid # Для роботи з UUID
from decimal import Decimal # Для Numeric полів

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

if TYPE_CHECKING:
    from backend.app.src.models.bonuses.account import AccountModel
    from backend.app.src.models.auth.user import UserModel
    from backend.app.src.models.bonuses.transaction import TransactionModel


class BonusAdjustmentModel(BaseModel):
    """
    Модель для ручного коригування бонусів.
    (Атрибути id, created_at, updated_at, created_by_user_id, updated_by_user_id успадковані)
    `created_by_user_id` тут може інтерпретуватися як `adjusted_by_user_id`.
    """
    __tablename__ = "bonus_adjustments"

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Адміністратор, який зробив коригування.
    # Якщо created_by_user_id з BaseModel використовується для цього, то це поле може бути зайвим.
    # Якщо ж потрібне окреме поле, то воно тут.
    # Для узгодження з попередніми версіями, залишаю adjusted_by_user_id.
    adjusted_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_bonus_adjustments_admin_id", ondelete="SET NULL"), nullable=False, index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Посилання на транзакцію, яка була створена в результаті цього коригування.
    transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.id", name="fk_bonus_adjustments_transaction_id", ondelete="SET NULL"), nullable=True, unique=True, index=True)


    # --- Зв'язки (Relationships) ---
    account: Mapped["AccountModel"] = relationship(back_populates="adjustments")

    admin: Mapped["UserModel"] = relationship(foreign_keys=[adjusted_by_user_id], back_populates="made_bonus_adjustments")

    # Зв'язок з TransactionModel. У TransactionModel має бути зворотний зв'язок.
    # Наприклад, в TransactionModel: source_adjustment: Mapped[Optional["BonusAdjustmentModel"]] = relationship(back_populates="transaction")
    # Тоді тут:
    transaction: Mapped[Optional["TransactionModel"]] = relationship(foreign_keys=[transaction_id], back_populates="source_adjustment")


    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}', account_id='{self.account_id}', amount='{self.amount}')>"

# Примітки:
# - Використано TYPE_CHECKING для імпорту типів моделей для Mapped, щоб уникнути реальних циклічних імпортів.
# - `ondelete` стратегії: CASCADE для account_id, SET NULL для adjusted_by_user_id та transaction_id.
# - `back_populates` вказані для узгодження з відповідними моделями.
# - `adjusted_by_user_id` залишено як окреме поле, хоча `created_by_user_id` з `BaseModel`
#   міг би використовуватися, якщо б це завжди був той самий користувач.
#   Наявність окремого поля дає більше гнучкості.
#
# Все готово.
