# backend/app/src/services/dictionaries/task_type_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс для управління довідником типів завдань/подій (`TaskTypeModel`).
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.dictionaries.task_type import TaskTypeModel
from backend.app.src.repositories.dictionaries.task_type import TaskTypeRepository, task_type_repository
from backend.app.src.schemas.dictionaries.task_type import TaskTypeCreateSchema, TaskTypeUpdateSchema
from backend.app.src.services.dictionaries.base_dict_service import BaseDictionaryService

class TaskTypeService(BaseDictionaryService[TaskTypeModel, TaskTypeRepository, TaskTypeCreateSchema, TaskTypeUpdateSchema]):
    """
    Сервіс для управління довідником типів завдань/подій.
    Успадковує базову CRUD-логіку для довідників.
    """

    async def get_event_types(self, db: AsyncSession) -> List[TaskTypeModel]:
        """
        Отримує всі типи завдань, які є подіями (is_event=True).
        """
        # Цей метод може бути реалізований в репозиторії,
        # але для прикладу додамо його сюди, якщо репозиторій не має такого методу.
        # Якщо TaskTypeRepository має get_event_types, то:
        # return await self.repository.get_event_types(db)

        # Пряма реалізація, якщо в репозиторії немає:
        all_types = await self.repository.get_multi(db, limit=1000) # Отримати всі
        event_types = [t for t in all_types if t.is_event]
        return event_types

    async def get_penalty_types(self, db: AsyncSession) -> List[TaskTypeModel]:
        """
        Отримує всі типи завдань, які є штрафами (is_penalty_type=True).
        """
        all_types = await self.repository.get_multi(db, limit=1000)
        penalty_types = [t for t in all_types if t.is_penalty_type]
        return penalty_types

    # TODO: Додати іншу специфічну бізнес-логіку для типів завдань, якщо потрібно.
    # Наприклад, перевірка, чи можна призначити певний тип завдання команді або індивідуально.

task_type_service = TaskTypeService(task_type_repository)

# Все виглядає добре. Додано приклади специфічних методів.
# Важливо, щоб модель TaskTypeModel мала поля is_event, is_penalty_type,
# які були додані на попередніх етапах.
