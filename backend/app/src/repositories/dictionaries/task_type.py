# backend/app/src/repositories/dictionaries/task_type.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `TaskTypeModel`.
Надає методи для взаємодії з таблицею типів завдань/подій в базі даних.
"""

from backend.app.src.models.dictionaries.task_type import TaskTypeModel
from backend.app.src.schemas.dictionaries.task_type import TaskTypeCreateSchema, TaskTypeUpdateSchema
from backend.app.src.repositories.dictionaries.base_dict import BaseDictionaryRepository

class TaskTypeRepository(BaseDictionaryRepository[TaskTypeModel, TaskTypeCreateSchema, TaskTypeUpdateSchema]):
    """
    Репозиторій для роботи з моделлю типів завдань/подій.
    Успадковує всі базові CRUD-операції та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """
    # Додаткові методи, специфічні для типів завдань, можуть бути додані тут.
    # Наприклад, отримання всіх типів, які є "подіями" (is_event=True).
    # async def get_event_types(self, db: AsyncSession) -> List[TaskTypeModel]:
    #     statement = select(self.model).where(self.model.is_event == True)
    #     result = await db.execute(statement)
    #     return result.scalars().all()
    pass

task_type_repository = TaskTypeRepository(TaskTypeModel)

# TODO: Реалізувати специфічні методи, якщо вони будуть визначені як необхідні
# (наприклад, для фільтрації типів завдань за їх характеристиками: is_event, is_penalty_type).
#
# Все виглядає добре.
