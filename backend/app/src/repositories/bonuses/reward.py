# backend/app/src/repositories/bonuses/reward.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `RewardModel`.
Надає методи для управління нагородами, доступними в групах.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.bonuses.reward import RewardModel
from backend.app.src.schemas.bonuses.reward import RewardCreateSchema, RewardUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class RewardRepository(BaseRepository[RewardModel, RewardCreateSchema, RewardUpdateSchema]):
    """
    Репозиторій для роботи з моделлю нагород (`RewardModel`).
    """

    async def get_rewards_for_group(
        self, db: AsyncSession, *, group_id: uuid.UUID,
        only_available: bool = True, # Повертати лише доступні (активні та з наявною кількістю)
        skip: int = 0, limit: int = 100
    ) -> List[RewardModel]:
        """
        Отримує список нагород для вказаної групи.
        """
        from backend.app.src.models.dictionaries.status import StatusModel # Для фільтрації за статусом
        from backend.app.src.core.constants import STATUS_ACTIVE_CODE # Припускаючи, що є код для активного статусу

        statement = select(self.model).where(self.model.group_id == group_id)

        if only_available:
            # TODO: Узгодити, як визначається "доступність" нагороди.
            #       - Статус (state_id) має бути активним.
            #       - quantity_available > 0 (або NULL).
            #       - is_deleted = False (це вже обробляється в BaseRepository, якщо там є фільтр).
            # Поки що припускаємо фільтр за активним статусом та кількістю.
            statement = statement.join(StatusModel, self.model.state_id == StatusModel.id).where(
                StatusModel.code == STATUS_ACTIVE_CODE # Або інший код активного статусу для нагород
            )
            statement = statement.where(
                (self.model.quantity_available > 0) | (self.model.quantity_available == None) # type: ignore
            )
            statement = statement.where(self.model.is_deleted == False) # type: ignore

        statement = statement.order_by(self.model.name).options( # type: ignore
            selectinload(self.model.icon_file),
            selectinload(self.model.bonus_type_details) # Для відображення валюти
        ).offset(skip).limit(limit)

        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_reward_with_details(self, db: AsyncSession, reward_id: uuid.UUID) -> Optional[RewardModel]:
        """
        Отримує нагороду з деталями (іконка, тип бонусу).
        """
        statement = select(self.model).where(self.model.id == reward_id).options(
            selectinload(self.model.icon_file),
            selectinload(self.model.bonus_type_details),
            selectinload(self.model.state),
            selectinload(self.model.group)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def decrement_quantity_available(
        self, db: AsyncSession, *, reward_obj: RewardModel, quantity_to_decrement: int = 1
    ) -> Optional[RewardModel]:
        """
        Зменшує доступну кількість нагороди.
        Повертає оновлений об'єкт, або None, якщо кількість не може бути зменшена
        (наприклад, якщо quantity_available стане < 0 і не є NULL).
        Цей метод має використовуватися в межах транзакції разом зі створенням запису про "покупку".
        """
        if reward_obj.quantity_available is not None:
            if reward_obj.quantity_available < quantity_to_decrement:
                # Недостатня кількість (це має перевірятися сервісом заздалегідь)
                return None
            reward_obj.quantity_available -= quantity_to_decrement
            db.add(reward_obj)
            await db.commit() # Можливо, commit тут не потрібен, якщо це частина більшої транзакції сервісу
            await db.refresh(reward_obj)
        # Якщо quantity_available is None (необмежена), то нічого не робимо
        return reward_obj

    # `create` успадкований. `RewardCreateSchema` має містити необхідні поля.
    # `group_id` встановлюється сервісом.
    async def create_reward_in_group(
        self, db: AsyncSession, *, obj_in: RewardCreateSchema, group_id: uuid.UUID
    ) -> RewardModel:
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(group_id=group_id, **obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # `update` та `delete` (включаючи soft_delete) успадковані.

reward_repository = RewardRepository(RewardModel)

# TODO: Переконатися, що `RewardCreateSchema` та `RewardUpdateSchema` коректно визначені.
#       `group_id` в `RewardCreateSchema` не потрібен, оскільки передається в `create_reward_in_group`.
#       `bonus_type_code` має бути валідним кодом з `BonusTypeModel`.
#
# TODO: Логіка перевірки `max_per_user` при "покупці" нагороди має бути на сервісному рівні.
#
# TODO: Фільтр `only_available` в `get_rewards_for_group` потребує узгодження
#       з тим, як визначається активний статус нагороди (наприклад, код з `StatusModel`).
#       Поки що використовується `STATUS_ACTIVE_CODE`.
#
# Все виглядає добре. Надано методи для отримання та створення/оновлення нагород.
# `decrement_quantity_available` - важливий метод для процесу "покупки".
# `CheckConstraint` для `group_id IS NOT NULL` в `RewardModel` вже додано.
