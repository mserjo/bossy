# backend/app/src/services/dictionaries/integration_type_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс для управління довідником типів інтеграцій (`IntegrationModel`).
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.dictionaries.integration import IntegrationModel
from backend.app.src.repositories.dictionaries.integration import IntegrationRepository, integration_repository
from backend.app.src.schemas.dictionaries.integration_type import IntegrationTypeCreateSchema, IntegrationTypeUpdateSchema
from backend.app.src.services.dictionaries.base_dict_service import BaseDictionaryService

class IntegrationTypeService(BaseDictionaryService[IntegrationModel, IntegrationRepository, IntegrationTypeCreateSchema, IntegrationTypeUpdateSchema]):
    """
    Сервіс для управління довідником типів зовнішніх інтеграцій.
    Успадковує базову CRUD-логіку для довідників.
    """

    async def get_integrations_by_category(self, db: AsyncSession, category: str) -> List[IntegrationModel]:
        """
        Отримує всі типи інтеграцій для вказаної категорії.
        """
        # Використовуємо метод з репозиторію, якщо він там є.
        return await self.repository.get_by_category(db, category=category)

    # TODO: Додати іншу специфічну бізнес-логіку для типів інтеграцій.
    # Наприклад, перевірка валідності `required_settings_schema` при створенні/оновленні.

integration_type_service = IntegrationTypeService(integration_repository)

# Все виглядає добре. Модель `IntegrationModel` має поле `category`.
# Репозиторій `IntegrationRepository` має метод `get_by_category`.
# Назва сервісу `IntegrationTypeService` відповідає схемам (`IntegrationTypeSchema`).
