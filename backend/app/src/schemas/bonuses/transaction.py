# backend/app/src/schemas/bonuses/transaction.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `TransactionModel`.
Схеми використовуються для валідації даних при створенні транзакцій
(хоча вони зазвичай створюються внутрішньою логікою системи) та для їх відображення.
"""

from pydantic import Field
from typing import Optional, List, Any, Dict # Забрано ForwardRef
import uuid
from datetime import datetime
from decimal import Decimal # Використовуємо Decimal

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.src.schemas.bonuses.account import AccountSchema
    from backend.app.src.schemas.auth.user import UserPublicSchema

# --- Схема для відображення інформації про транзакцію (для читання) ---
class TransactionSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення транзакції по рахунку.
    """
    account_id: uuid.UUID = Field(..., description="ID рахунку, до якого відноситься транзакція")
    amount: Decimal = Field(..., description="Сума транзакції (позитивна для нарахувань, від'ємна для списань)")
    transaction_type_code: str = Field(..., max_length=100, description="Код типу транзакції")
    description: Optional[str] = Field(None, description="Опис транзакції")

    source_entity_type: Optional[str] = Field(None, max_length=100, description="Тип сутності, що спричинила транзакцію")
    source_entity_id: Optional[uuid.UUID] = Field(None, description="ID сутності-джерела")

    related_user_id: Optional[uuid.UUID] = Field(None, description="ID пов'язаного користувача (наприклад, для 'подяки')")

    additional_data: Optional[Dict[str, Any]] = Field(None, description="Додаткові структуровані дані (JSON), раніше 'metadata'") # Перейменовано
    balance_after_transaction: Optional[Decimal] = Field(None, description="Баланс рахунку після цієї транзакції")

    # --- Розгорнуті зв'язки (приклад) ---
    account: Optional['AccountSchema'] = Field(None, description="Рахунок, до якого відноситься транзакція") # Рядкове посилання
    related_user: Optional['UserPublicSchema'] = Field(None, description="Пов'язаний користувач (наприклад, для 'подяки')") # Рядкове посилання

    # Валюта транзакції визначається з AccountModel.bonus_type_code
    # для account_id, до якого належить транзакція.
    # Якщо б AccountModel не мав bonus_type_code, то його треба було б додати сюди.

# --- Схема для створення транзакції (зазвичай використовується внутрішньо системою) ---
class TransactionCreateSchema(BaseSchema):
    """
    Схема для створення нової транзакції.
    Зазвичай створюється сервісною логікою, а не напряму через API користувачем.
    """
    account_id: uuid.UUID = Field(..., description="ID рахунку")
    amount: Decimal = Field(..., description="Сума транзакції")
    transaction_type_code: str = Field(..., max_length=100, description="Код типу транзакції")
    description: Optional[str] = Field(None, description="Опис")

    source_entity_type: Optional[str] = Field(None, max_length=100, description="Тип сутності-джерела")
    source_entity_id: Optional[uuid.UUID] = Field(None, description="ID сутності-джерела")

    related_user_id: Optional[uuid.UUID] = Field(None, description="ID пов'язаного користувача")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Додаткові дані (JSON), раніше 'metadata'") # Перейменовано

    # `balance_after_transaction` розраховується сервісом при створенні транзакції.
    # `created_at`, `updated_at`, `id` встановлюються автоматично.

# --- Схема для оновлення транзакції (зазвичай транзакції незмінні) ---
# Транзакції зазвичай є незмінними записами (immutable).
# Якщо потрібно виправити помилкову транзакцію, створюється нова коригуюча транзакція.
# Тому `TransactionUpdateSchema` може не знадобитися.
# class TransactionUpdateSchema(BaseSchema):
#     """
#     Схема для оновлення транзакції (використовується рідко, транзакції зазвичай незмінні).
#     """
#     description: Optional[str] = Field(None)
#     metadata: Optional[Dict[str, Any]] = Field(None)
#     # Інші поля (amount, account_id, type) зазвичай не змінюються.

# TransactionSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `TransactionModel`.
# `TransactionModel` успадковує від `BaseModel`.
# `TransactionSchema` успадковує від `AuditDatesSchema` і додає всі поля транзакції.
# Використання `Decimal` для `amount` та `balance_after_transaction`.
#
# `TransactionCreateSchema` містить поля, необхідні для створення транзакції сервісом.
# `balance_after_transaction` розраховується і встановлюється сервісом.
#
# `TransactionUpdateSchema` закоментована, оскільки транзакції зазвичай незмінні.
#
# Розгорнуті зв'язки в `TransactionSchema` (account, related_user) додані з `ForwardRef`.
#
# Валюта транзакції:
# Як обговорювалося для `AccountModel`, поточна реалізація `TransactionModel`
# НЕ містить `bonus_type_code`. Це означає, що валюта транзакції
# неявно визначається полем `AccountModel.bonus_type_code` для `account_id`,
# до якого належить ця транзакція.
# Це припущення працює, якщо `AccountModel.bonus_type_code` є стабільним для рахунку,
# або якщо вся логіка конвертації/обробки змін типу валюти групи
# реалізована так, що це прозоро для транзакцій.
# Якщо це припущення невірне, то `TransactionModel` та її схеми
# повинні будуть включати `bonus_type_code_at_transaction_time`.
# Поки що залишаю як є, згідно з поточним станом `AccountModel`.
#
# Все виглядає узгоджено з моделлю `TransactionModel`.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` - час створення транзакції.
# `updated_at` - зазвичай не змінюється.
#
# `source_entity_type` та `source_entity_id` дозволяють зв'язати транзакцію
# з джерелом (виконання завдання, купівля нагороди, ручне коригування тощо).
# `related_user_id` для операцій типу "подяка".
# `metadata` для додаткової інформації.
# `transaction_type_code` для класифікації операції.
# Все виглядає добре.

# TransactionSchema.model_rebuild() # Виклик перенесено до __init__.py пакету bonuses
# TransactionCreateSchema.model_rebuild() # Зазвичай не потрібно для схем без ForwardRef
