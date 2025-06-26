# backend/app/src/repositories/bonuses/account.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `AccountModel`.
Надає методи для управління рахунками користувачів.
"""

from typing import Optional, List
import uuid
from decimal import Decimal
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.bonuses.account import AccountModel
from backend.app.src.schemas.bonuses.account import AccountCreateSchema, AccountUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class AccountRepository(BaseRepository[AccountModel, AccountCreateSchema, AccountUpdateSchema]):
    """
    Репозиторій для роботи з моделлю рахунків користувачів (`AccountModel`).
    """

    async def get_by_user_and_group(
        self, db: AsyncSession, *, user_id: uuid.UUID, group_id: uuid.UUID
    ) -> Optional[AccountModel]:
        """
        Отримує рахунок користувача для вказаної групи.
        Оскільки UniqueConstraint('user_id', 'group_id') в моделі, має бути не більше одного.
        """
        statement = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.group_id == group_id)
        ).options(
            selectinload(self.model.user),
            selectinload(self.model.group),
            selectinload(self.model.bonus_type_details) # Завантажуємо деталі типу бонусу
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_accounts_for_user(
        self, db: AsyncSession, *, user_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[AccountModel]:
        """
        Отримує всі рахунки для вказаного користувача в різних групах.
        """
        statement = select(self.model).where(self.model.user_id == user_id).options(
            selectinload(self.model.group), # Завантажуємо інформацію про групу
            selectinload(self.model.bonus_type_details)
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_accounts_for_group(
        self, db: AsyncSession, *, group_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[AccountModel]:
        """
        Отримує всі рахунки користувачів у вказаній групі.
        """
        statement = select(self.model).where(self.model.group_id == group_id).options(
            selectinload(self.model.user), # Завантажуємо інформацію про користувача
            selectinload(self.model.bonus_type_details)
        ).order_by(self.model.user_id).offset(skip).limit(limit) # Сортуємо за user_id для консистентності
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def update_balance(
        self, db: AsyncSession, *, account_obj: AccountModel, amount_change: Decimal
    ) -> AccountModel:
        """
        Оновлює баланс рахунку на вказану суму (може бути позитивною або від'ємною).
        Цей метод НЕ створює транзакцію, це має робити сервіс.
        """
        account_obj.balance += amount_change
        db.add(account_obj)
        await db.commit()
        await db.refresh(account_obj)
        return account_obj

    # `create` успадкований. `AccountCreateSchema` має містити `user_id`, `group_id`, `bonus_type_code`.
    # `balance` за замовчуванням 0.
    # `update` успадкований (для оновлення через схему). `AccountUpdateSchema`
    # дозволяє оновлювати `balance`, але це не рекомендовано напряму.
    # `delete` успадкований.

account_repository = AccountRepository(AccountModel)

# TODO: Переконатися, що `AccountCreateSchema` та `AccountUpdateSchema` коректно визначені.
#       `AccountCreateSchema` має отримувати `bonus_type_code` з налаштувань групи на момент створення.
#
# TODO: Розглянути метод `get_or_create_account` для зручності сервісів.
#       (Вже є в GroupSettingsRepository, схожий патерн може бути тут).
#
# Все виглядає добре. Надано методи для отримання рахунків та оновлення балансу.
# Важливо, щоб логіка створення транзакцій та оновлення балансу була атомарною
# на сервісному рівні. Репозиторій лише виконує операції з БД.
# Зв'язок `bonus_type_details` з `BonusTypeModel` через `bonus_type_code` в `AccountModel`
# дозволяє отримати деталі про валюту рахунку.
