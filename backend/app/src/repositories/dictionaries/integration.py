# backend/app/src/repositories/dictionaries/integration.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `IntegrationModel` (довідник типів інтеграцій).
Надає методи для взаємодії з таблицею типів зовнішніх інтеграцій в базі даних.
"""

from typing import List, Optional
from sqlalchemy import select # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.dictionaries.integration import IntegrationModel
from backend.app.src.schemas.dictionaries.integration_type import IntegrationTypeCreateSchema, IntegrationTypeUpdateSchema # Зверніть увагу на назву схеми
from backend.app.src.repositories.dictionaries.base_dict import BaseDictionaryRepository

class IntegrationRepository(BaseDictionaryRepository[IntegrationModel, IntegrationTypeCreateSchema, IntegrationTypeUpdateSchema]):
    """
    Репозиторій для роботи з моделлю типів зовнішніх інтеграцій.
    Успадковує всі базові CRUD-операції та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """
    # Додаткові методи, специфічні для типів інтеграцій, можуть бути додані тут.
    # Наприклад, отримання всіх інтеграцій певної категорії.
    async def get_by_category(self, db: AsyncSession, *, category: str) -> List[IntegrationModel]:
        """
        Отримує список типів інтеграцій за вказаною категорією.

        :param db: Асинхронна сесія бази даних.
        :param category: Категорія інтеграції для пошуку.
        :return: Список об'єктів моделі IntegrationModel.
        """
        statement = select(self.model).where(self.model.category == category)
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

integration_repository = IntegrationRepository(IntegrationModel)

# TODO: Переконатися, що назви схем (IntegrationTypeCreateSchema, IntegrationTypeUpdateSchema)
#       коректно використовуються, оскільки модель називається IntegrationModel,
#       а схеми можуть мати суфікс Type. (Так, вони названі IntegrationType...Schema).
#
# TODO: Реалізувати інші специфічні методи, якщо вони будуть потрібні,
#       наприклад, пошук за `api_docs_url` або іншими специфічними полями `IntegrationModel`.
#
# Все виглядає добре.
