# backend/app/src/repositories/bonuses/transaction.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `TransactionModel`.
Надає методи для створення та отримання транзакцій по рахунках.
Транзакції зазвичай є незмінними (immutable).
"""

from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.bonuses.transaction import TransactionModel
from backend.app.src.schemas.bonuses.transaction import TransactionCreateSchema # TransactionUpdateSchema зазвичай не потрібна
from backend.app.src.repositories.base import BaseRepository
from pydantic import BaseModel as PydanticBaseModel # Заглушка для UpdateSchemaType

class TransactionRepository(BaseRepository[TransactionModel, TransactionCreateSchema, PydanticBaseModel]): # UpdateSchemaType - заглушка
    """
    Репозиторій для роботи з моделлю транзакцій (`TransactionModel`).
    """

    async def get_transactions_for_account(
        self, db: AsyncSession, *, account_id: uuid.UUID,
        skip: int = 0, limit: int = 100,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        transaction_type_code: Optional[str] = None
    ) -> List[TransactionModel]:
        """
        Отримує список транзакцій для вказаного рахунку з можливістю фільтрації.
        """
        statement = select(self.model).where(self.model.account_id == account_id)

        if date_from:
            statement = statement.where(self.model.created_at >= date_from) # type: ignore
        if date_to:
            # Включаємо транзакції до кінця вказаного дня
            from datetime import timedelta
            statement = statement.where(self.model.created_at < (date_to + timedelta(days=1))) # type: ignore
        if transaction_type_code:
            statement = statement.where(self.model.transaction_type_code == transaction_type_code)

        statement = statement.order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        # Можна додати selectinload для account або related_user, якщо потрібно
        # .options(selectinload(self.model.account), selectinload(self.model.related_user))

        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def create_transaction(
        self, db: AsyncSession, *, obj_in: TransactionCreateSchema,
        balance_after: Decimal # Баланс розраховується сервісом і передається сюди
    ) -> TransactionModel:
        """
        Створює новий запис транзакції.
        `balance_after_transaction` має бути розрахований та переданий сервісом.
        """
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(**obj_in_data, balance_after_transaction=balance_after)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # Транзакції зазвичай не оновлюються і не видаляються (хіба що для виправлення помилок).
    # Успадковані `update` та `delete` можуть використовуватися для таких цілей,
    # але це має контролюватися на рівні прав доступу та бізнес-логіки.
    # "М'яке" видалення для транзакцій зазвичай не застосовується.

transaction_repository = TransactionRepository(TransactionModel)

# TODO: Переконатися, що `TransactionCreateSchema` містить всі необхідні поля.
#       (account_id, amount, transaction_type_code; інші опціональні).
#       `balance_after_transaction` не є частиною схеми створення, а передається окремо.
#
# TODO: Розглянути, чи потрібні методи для агрегації даних з транзакцій
#       (наприклад, сума транзакцій за період), чи це краще робити
#       на рівні сервісів або спеціалізованих запитів для звітів.
#       Поки що репозиторій надає базові операції.
#
# Все виглядає добре. `get_transactions_for_account` - основний метод для отримання історії.
# `create_transaction` для запису нових транзакций.
# Валюта транзакції визначається з `AccountModel.bonus_type_code` для `account_id`.
# Якщо `AccountModel` не міститиме `bonus_type_code`, то його потрібно буде додати
# до `TransactionModel` (і схем) як `bonus_type_code_at_transaction_time`.
# Поточна реалізація `AccountModel` МАЄ `bonus_type_code`, тому тут все узгоджено.
