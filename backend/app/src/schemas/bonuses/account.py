# backend/app/src/schemas/bonuses/account.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `AccountModel`.
Схеми використовуються для валідації даних при відображенні інформації про рахунки користувачів.
Створення та оновлення рахунків (зміна балансу) зазвичай відбувається через транзакції,
а не прямими запитами до моделі рахунку, хоча початкове створення рахунку може бути окремою операцією.
"""

from pydantic import Field
from typing import Optional, List, ForwardRef
import uuid
from datetime import datetime
from decimal import Decimal # Використовуємо Decimal для точності фінансових даних

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.groups.group import GroupSimpleSchema
# from backend.app.src.schemas.bonuses.transaction import TransactionSchema
# from backend.app.src.schemas.dictionaries.bonus_type import BonusTypeSchema (якщо bonus_type_code розгортається)

UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema')
TransactionSchema = ForwardRef('backend.app.src.schemas.bonuses.transaction.TransactionSchema')
BonusTypeSchema = ForwardRef('backend.app.src.schemas.dictionaries.bonus_type.BonusTypeSchema')

# --- Схема для відображення інформації про рахунок (для читання) ---
class AccountSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення рахунку користувача.
    """
    user_id: uuid.UUID = Field(..., description="ID користувача, якому належить рахунок")
    group_id: uuid.UUID = Field(..., description="ID групи, в межах якої діє цей рахунок")
    balance: Decimal = Field(..., description="Поточний баланс бонусів на рахунку")

    # `bonus_type_code` береться з моделі AccountModel.
    # Це код типу бонусів (наприклад, "POINTS", "STARS"), який був актуальним для групи
    # на момент створення або останнього оновлення рахунку (якщо він змінюється).
    # Або ж, якщо рахунок завжди в одній валюті, то це її код.
    bonus_type_code: str = Field(..., description="Код типу бонусів для цього рахунку (з довідника BonusTypeModel.code)")

    # --- Розгорнуті зв'язки (приклад) ---
    user: Optional[UserPublicSchema] = None
    group: Optional[GroupSimpleSchema] = None
    # bonus_type: Optional[BonusTypeSchema] = None # Розгорнута інформація про тип бонусу

    # Список транзакцій зазвичай не включається сюди повністю, а отримується окремим запитом з пагінацією.
    # transactions: List[TransactionSchema] = Field(default_factory=list)


# --- Схема для створення рахунку (зазвичай виконується сервісом автоматично) ---
class AccountCreateSchema(BaseSchema):
    """
    Схема для створення нового рахунку.
    Зазвичай рахунки створюються автоматично при додаванні користувача до групи.
    Ця схема може використовуватися, якщо потрібно створити рахунок вручну або для тестування.
    """
    user_id: uuid.UUID = Field(..., description="ID користувача")
    group_id: uuid.UUID = Field(..., description="ID групи")
    balance: Decimal = Field(default=Decimal('0.00'), description="Початковий баланс (за замовчуванням 0)")
    bonus_type_code: str = Field(..., description="Код типу бонусів (має відповідати активному типу бонусів групи)")
    # `bonus_type_code` тут має бути переданий, оскільки він зберігається в `AccountModel`.
    # Сервіс, що створює рахунок, має взяти цей код з налаштувань групи.

# --- Схема для оновлення рахунку (зазвичай не використовується напряму; баланс змінюється через транзакції) ---
# Якщо потрібне пряме оновлення балансу (наприклад, адміном для коригування):
class AccountUpdateSchema(BaseSchema):
    """
    Схема для оновлення рахунку (наприклад, пряме коригування балансу адміном).
    УВАГА: Зміна балансу напряму без транзакції порушує аудит.
    Краще використовувати `BonusAdjustmentModel` та відповідні транзакції.
    Це схема для крайніх випадків або якщо логіка це дозволяє.
    """
    balance: Optional[Decimal] = Field(None, description="Новий баланс рахунку")
    # bonus_type_code: Optional[str] = Field(None, description="Новий код типу бонусів (зміна типу валюти - складна операція)")
    # Зміна `bonus_type_code` для існуючого рахунку зазвичай не робиться.
    # Якщо група змінює тип бонусів, це має оброблятися спеціальною логікою
    # (конвертація, створення нового рахунку тощо).

# AccountSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `AccountModel`.
# `AccountModel` (після обговорень) має: id, user_id, group_id, balance (Numeric), bonus_type_code (str),
# created_at, updated_at.
# `AccountSchema` успадковує від `AuditDatesSchema` і додає ці поля.
# Використання `Decimal` в Pydantic для `Numeric` полів SQLAlchemy є правильною практикою для точності.
#
# `AccountCreateSchema`:
#   - `user_id`, `group_id`, `bonus_type_code` - обов'язкові.
#   - `balance` - з дефолтом 0.
#   - `bonus_type_code` має встановлюватися сервісом на основі активного типу бонусів групи.
#
# `AccountUpdateSchema` (для прямого оновлення балансу):
#   - Дозволяє оновлювати `balance`.
#   - Зміна `bonus_type_code` закоментована, бо це складна операція.
#   - Наголошено, що пряма зміна балансу без транзакції - погана практика.
#     Для коригувань краще використовувати `BonusAdjustmentModel`.
#
# Розгорнуті зв'язки в `AccountSchema` (user, group, bonus_type) додані з `ForwardRef`.
# Список транзакцій закоментований (зазвичай отримується окремо).
# Все виглядає узгоджено з поточною структурою `AccountModel`.
#
# Важливо: `bonus_type_code` в `AccountSchema` та `AccountCreateSchema`
# передбачає, що цей код береться з довідника `BonusTypeModel.code`.
# Зв'язок `bonus_type: Optional[BonusTypeSchema]` в `AccountSchema`
# дозволить розгорнути інформацію про цей тип бонусу, якщо потрібно.
#
# Все виглядає добре.
