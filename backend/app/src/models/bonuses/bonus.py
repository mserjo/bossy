# backend/app/src/models/bonuses/bonus.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `BonusAdjustmentModel`
для ручного коригування бонусів адміністратором.
Це дозволяє додавати або списувати бонуси користувачам поза стандартними процесами
(виконання завдань, купівля нагород).
"""

from sqlalchemy import Column, ForeignKey, Numeric, Text, String # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

class BonusAdjustmentModel(BaseModel):
    """
    Модель для ручного коригування бонусів.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор коригування (успадковано).
        account_id (uuid.UUID): Рахунок користувача, якому проводиться коригування.
        adjusted_by_user_id (uuid.UUID): Адміністратор, який виконав коригування.
        amount (Numeric): Сума коригування (позитивна для додавання, від'ємна для списання).
        reason (Text): Причина або опис коригування.
        transaction_id (uuid.UUID | None): Посилання на створену транзакцію в TransactionModel.

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення (успадковано).
    """
    __tablename__ = "bonus_adjustments"

    account_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Адміністратор, який зробив коригування
    # TODO: Замінити "users.id" на константу або імпорт моделі UserModel.
    adjusted_by_user_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_bonus_adjustments_admin_id", ondelete="SET NULL"), nullable=False, index=True)

    amount: Column[Numeric] = Column(Numeric(12, 2), nullable=False)
    reason: Column[str] = Column(Text, nullable=False)

    # Посилання на транзакцію, яка була створена в результаті цього коригування.
    # Може бути `nullable=True`, якщо транзакція створюється окремо,
    # але краще, щоб було `nullable=False` і `unique=True` для жорсткого зв'язку.
    # TODO: Замінити "transactions.id" на константу або імпорт моделі TransactionModel.
    transaction_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("transactions.id", name="fk_bonus_adjustments_transaction_id", ondelete="SET NULL"), nullable=True, unique=True, index=True)


    # --- Зв'язки (Relationships) ---
    account = relationship("AccountModel") # back_populates="adjustments" буде в AccountModel
    admin = relationship("UserModel", foreign_keys=[adjusted_by_user_id]) # back_populates="made_bonus_adjustments" буде в UserModel
    transaction = relationship("TransactionModel", foreign_keys=[transaction_id]) # back_populates="source_adjustment" буде в TransactionModel

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}', account_id='{self.account_id}', amount='{self.amount}')>"

# Ця модель відрізняється від початкової ідеї "BonusModel" як правил нарахування.
# Натомість, це інструмент для адміністраторів для прямого впливу на баланси.
# Правила нарахування бонусів інтегровані в TaskModel (bonus_points, penalty_points)
# та RewardModel (cost_points).
#
# Подумаємо, чи потрібна ця модель, чи достатньо просто створювати транзакцію
# з типом "MANUAL_ADJUSTMENT" і заповнювати `source_entity_type='system_adjustment'`
# або `source_entity_type='admin_action'` та `source_entity_id=admin_user_id`.
# Наявність окремої моделі `BonusAdjustmentModel` може бути корисною для:
# 1. Більш детального аудиту саме ручних коригувань.
# 2. Зберігання специфічної інформації про коригування (наприклад, запит на коригування, якщо такий процес є).
# 3. Чіткого розділення логіки.
#
# Якщо `TransactionModel.description` та `TransactionModel.metadata` достатньо для фіксації
# деталей ручного коригування, то ця модель може бути надлишковою.
#
# Поки що залишаю цю модель, оскільки вона може додати структуру для ручних операцій.
# Якщо виявиться зайвою, її можна буде видалити або об'єднати логіку з транзакціями.
#
# Важливо: кожне коригування має створювати відповідну транзакцію.
# Поле `transaction_id` забезпечує цей зв'язок.
# `ondelete="SET NULL"` для `transaction_id` означає, що якщо транзакція видаляється (що малоймовірно),
# запис про коригування залишається, але втрачає прямий зв'язок.
# Можливо, краще `ondelete="RESTRICT"` або `nullable=False` і гарантувати, що транзакція не видаляється.
# Або ж, якщо коригування видаляється, то і транзакція (CASCADE), але це нелогічно.
# Якщо `transaction_id` є `nullable=False, unique=True`, то це сильний зв'язок.
# Поки що `nullable=True, unique=True` для гнучкості на етапі розробки.
# `ondelete="SET NULL"` для `adjusted_by_user_id` - якщо адмін видаляється, запис про коригування залишається.
# `ondelete="CASCADE"` для `account_id` - якщо рахунок видаляється, коригування по ньому теж.
#
# `transaction_type_code` для відповідної транзакції буде щось на кшталт
# 'MANUAL_CREDIT' або 'MANUAL_DEBIT'.
# `source_entity_type` в транзакції буде 'bonus_adjustment', а `source_entity_id` - ID цього запису.
# Це виглядає послідовно.
