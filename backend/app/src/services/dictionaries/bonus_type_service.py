# backend/app/src/services/dictionaries/bonus_type_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс для управління довідником типів бонусів (`BonusTypeModel`).
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.dictionaries.bonus_type import BonusTypeModel
from backend.app.src.repositories.dictionaries.bonus_type import BonusTypeRepository, bonus_type_repository
from backend.app.src.schemas.dictionaries.bonus_type import BonusTypeCreateSchema, BonusTypeUpdateSchema
from backend.app.src.services.dictionaries.base_dict_service import BaseDictionaryService

class BonusTypeService(BaseDictionaryService[BonusTypeModel, BonusTypeRepository, BonusTypeCreateSchema, BonusTypeUpdateSchema]):
    """
    Сервіс для управління довідником типів бонусів.
    Успадковує базову CRUD-логіку для довідників.
    """

    async def get_types_allowing_decimals(self, db: AsyncSession) -> List[BonusTypeModel]:
        """
        Отримує всі типи бонусів, які дозволяють дробові значення.
        """
        # Приклад, якщо такий метод є в репозиторії:
        # return await self.repository.get_types_allowing_decimals(db)

        # Пряма реалізація:
        all_types = await self.repository.get_multi(db, limit=1000)
        decimal_types = [t for t in all_types if t.allow_decimal]
        return decimal_types

    # TODO: Додати іншу специфічну бізнес-логіку для типів бонусів.
    # Наприклад, отримання типу бонусів за замовчуванням для нових груп.

bonus_type_service = BonusTypeService(bonus_type_repository)

# Все виглядає добре. Модель `BonusTypeModel` має поле `allow_decimal`.
