# backend/app/src/models/bonuses/bonus_adjustment.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `BonusAdjustmentModel` для фіксації
ручних коригувань бонусних рахунків адміністраторами.
"""
from typing import Optional
from decimal import Decimal
import uuid

from sqlalchemy import Column, ForeignKey, Numeric, Text, String # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column # type: ignore

from backend.app.src.models.base import BaseModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import UserModel
    from backend.app.src.models.bonuses.account import AccountModel
    from backend.app.src.models.bonuses.transaction import TransactionModel

class BonusAdjustmentModel(BaseModel):
    """
    Модель для ручних коригувань бонусних рахунків.
    (Атрибути id, created_at, updated_at, created_by_user_id, updated_by_user_id успадковані)
    `created_by_user_id` тут буде ID адміністратора, що виконав коригування.
    """
    __tablename__ = "bonus_adjustments"

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", name="fk_bonus_adjustments_account_id", ondelete="RESTRICT"), nullable=False, index=True)
    adjusted_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_bonus_adjustments_admin_id", ondelete="RESTRICT"), nullable=False, index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False) # Сума коригування (може бути +/-)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Причина коригування

    # Посилання на транзакцію, яка була створена в результаті цього коригування.
    # Зв'язок один-до-одного. BonusAdjustment створює одну Transaction.
    transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.id", name="fk_bonus_adjustments_transaction_id", ondelete="SET NULL"), nullable=True, unique=True)

    # --- Зв'язки (Relationships) ---
    account: Mapped["AccountModel"] = relationship(back_populates="adjustments")
    admin: Mapped["UserModel"] = relationship(foreign_keys=[adjusted_by_user_id], back_populates="made_bonus_adjustments")

    # Зв'язок з транзакцією
    transaction: Mapped[Optional["TransactionModel"]] = relationship(back_populates="source_adjustment")


    def __repr__(self) -> str:
        return f"<BonusAdjustmentModel(id='{self.id}', account_id='{self.account_id}', amount='{self.amount}')>"

# Примітки:
# - `ondelete="RESTRICT"` для `account_id` та `adjusted_by_user_id`, щоб не можна було видалити
#   рахунок або адміна, якщо є пов'язані коригування. Можливо, краще `SET NULL` для `adjusted_by_user_id`,
#   якщо адмін може бути видалений, а історія коригувань має залишитися. Поки що RESTRICT.
# - `transaction_id` є `nullable=True` та `unique=True`. `ondelete="SET NULL"`, щоб коригування
#   залишилося, навіть якщо транзакція випадково видалена (хоча транзакції зазвичай не видаляються).
# - `created_by_user_id` з BaseModel тут буде тим самим, що й `adjusted_by_user_id`.
#   Можна розглянути можливість не дублювати або використовувати одне з них.
#   Поки що залишаю обидва, `created_by_user_id` - стандартне поле аудиту,
#   `adjusted_by_user_id` - більш семантично для цієї моделі.
#   Або ж `adjusted_by_user_id` можна прибрати і покладатися на `created_by_user_id`.
#   Для узгодженості з іншими "creator" полями, залишаю `adjusted_by_user_id`.
#
# Зв'язок `transaction` з `TransactionModel` узгоджено.
# Зв'язок `admin` з `UserModel` (де `adjusted_by_user_id` є FK) потребує `made_bonus_adjustments` в `UserModel`.
# Зв'язок `account` з `AccountModel` потребує `adjustments` в `AccountModel`.
# Ці зворотні зв'язки вже є в `UserModel` та `AccountModel` (перевірено в попередніх кроках).
#
# Файл `backend/app/src/models/bonuses/__init__.py` має бути оновлений.
#
# Все готово для цього файлу.
