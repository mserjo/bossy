# backend/app/src/repositories/dictionaries/bonus_type.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `BonusTypeModel`.
Надає методи для взаємодії з таблицею типів бонусів в базі даних.
"""

from backend.app.src.models.dictionaries.bonus_type import BonusTypeModel
from backend.app.src.schemas.dictionaries.bonus_type import BonusTypeCreateSchema, BonusTypeUpdateSchema
from backend.app.src.repositories.dictionaries.base_dict import BaseDictionaryRepository

class BonusTypeRepository(BaseDictionaryRepository[BonusTypeModel, BonusTypeCreateSchema, BonusTypeUpdateSchema]):
    """
    Репозиторій для роботи з моделлю типів бонусів.
    Успадковує всі базові CRUD-операції та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """
    # Додаткові методи, специфічні для типів бонусів, можуть бути додані тут.
    # Наприклад, отримання всіх типів, що дозволяють дробові значення.
    # async def get_types_allowing_decimals(self, db: AsyncSession) -> List[BonusTypeModel]:
    #     statement = select(self.model).where(self.model.allow_decimal == True)
    #     result = await db.execute(statement)
    #     return result.scalars().all()
    pass

bonus_type_repository = BonusTypeRepository(BonusTypeModel)

# TODO: Реалізувати специфічні методи, якщо вони будуть потрібні.
#
# Все виглядає добре.
