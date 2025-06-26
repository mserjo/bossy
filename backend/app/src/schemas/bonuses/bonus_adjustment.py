# backend/app/src/schemas/bonuses/bonus_adjustment.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `BonusAdjustmentModel`.
Схеми використовуються для валідації даних при створенні ручних коригувань бонусів
адміністратором та для відображення інформації про такі коригування.
"""

from pydantic import Field
from typing import Optional, List, ForwardRef
import uuid
from datetime import datetime
from decimal import Decimal # Використовуємо Decimal

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.bonuses.account import AccountSchema
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.bonuses.transaction import TransactionSchema

AccountSchema = ForwardRef('backend.app.src.schemas.bonuses.account.AccountSchema')
UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
TransactionSchema = ForwardRef('backend.app.src.schemas.bonuses.transaction.TransactionSchema')

# --- Схема для відображення інформації про ручне коригування бонусів (для читання) ---
class BonusAdjustmentSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення ручного коригування бонусів.
    """
    account_id: uuid.UUID = Field(..., description="ID рахунку, для якого зроблено коригування")
    adjusted_by_user_id: uuid.UUID = Field(..., description="ID адміністратора, який виконав коригування")
    amount: Decimal = Field(..., description="Сума коригування (позитивна для додавання, від'ємна для списання)")
    reason: str = Field(..., description="Причина або опис коригування")
    transaction_id: Optional[uuid.UUID] = Field(None, description="ID створеної транзакції, що відображає це коригування")

    # --- Розгорнуті зв'язки (приклад) ---
    account: Optional[AccountSchema] = Field(None, description="Рахунок, до якого застосовано коригування")
    admin: Optional[UserPublicSchema] = Field(None, description="Адміністратор, який виконав коригування")
    transaction: Optional[TransactionSchema] = Field(None, description="Пов'язана транзакція, що відображає коригування")


# --- Схема для створення нового ручного коригування бонусів ---
class BonusAdjustmentCreateSchema(BaseSchema):
    """
    Схема для створення нового ручного коригування бонусів.
    """
    account_id: uuid.UUID = Field(..., description="ID рахунку, для якого проводиться коригування")
    # adjusted_by_user_id: uuid.UUID # Встановлюється сервісом з поточного адміністратора
    amount: Decimal = Field(..., description="Сума коригування (може бути позитивною або від'ємною)")
    reason: str = Field(..., min_length=1, description="Причина коригування (обов'язково)")

    # transaction_id не передається при створенні, а встановлюється сервісом
    # після успішного створення відповідної транзакції.

    # Валідатор, щоб сума не була нульовою
    @Field('amount')
    def amount_must_not_be_zero(cls, value: Decimal) -> Decimal:
        if value == Decimal('0'):
            raise ValueError("Сума коригування не може бути нульовою.")
        return value

# --- Схема для оновлення ручного коригування бонусів (зазвичай не використовується) ---
# Ручні коригування, як і транзакції, зазвичай є незмінними записами.
# Якщо потрібно змінити, створюється нове коригування, що компенсує попереднє.
# Тому `BonusAdjustmentUpdateSchema` може не знадобитися.
# class BonusAdjustmentUpdateSchema(BaseSchema):
#     """
#     Схема для оновлення ручного коригування бонусів (використовується рідко).
#     """
#     reason: Optional[str] = Field(None, min_length=1)
#     # Інші поля (amount, account_id, admin_id, transaction_id) зазвичай не змінюються.

# BonusAdjustmentSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `BonusAdjustmentModel`.
# `BonusAdjustmentModel` успадковує від `BaseModel`.
# `BonusAdjustmentSchema` успадковує від `AuditDatesSchema` і додає поля коригування.
# Розгорнуті зв'язки `admin` та `transaction` додані з `ForwardRef`.
#
# `BonusAdjustmentCreateSchema`:
#   - `account_id`, `amount`, `reason` - основні поля.
#   - `adjusted_by_user_id` встановлюється сервісом.
#   - `transaction_id` встановлюється сервісом після створення транзакції.
#   - Валідатор для `amount`.
#
# `BonusAdjustmentUpdateSchema` закоментована, оскільки такі записи зазвичай незмінні.
#
# Все виглядає узгоджено.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` - час створення коригування.
# `updated_at` - зазвичай не змінюється.
#
# Ця модель та схеми дозволяють адміністраторам вносити обґрунтовані зміни
# до балансів користувачів, і кожна така зміна супроводжується створенням
# відповідної транзакції для повного аудиту.
#
# Назва файлу `bonus_adjustment.py` та схеми `BonusAdjustmentSchema`
# відповідають моделі `BonusAdjustmentModel`.
#
# Все виглядає добре.

BonusAdjustmentSchema.model_rebuild()
BonusAdjustmentCreateSchema.model_rebuild()
