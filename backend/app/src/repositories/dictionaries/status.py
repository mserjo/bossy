# backend/app/src/repositories/dictionaries/status.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `StatusModel`.
Надає методи для взаємодії з таблицею статусів в базі даних.
"""

from backend.app.src.models.dictionaries.status import StatusModel
from backend.app.src.schemas.dictionaries.status import StatusCreateSchema, StatusUpdateSchema
from backend.app.src.repositories.dictionaries.base_dict import BaseDictionaryRepository

class StatusRepository(BaseDictionaryRepository[StatusModel, StatusCreateSchema, StatusUpdateSchema]):
    """
    Репозиторій для роботи з моделлю статусів.
    Успадковує всі базові CRUD-операції та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """
    # Модель вже визначена в BaseRepository через Generic[ModelType]
    # self.model = StatusModel (це встановлюється в __init__ BaseRepository)
    pass

# Створюємо екземпляр репозиторію для можливого використання в залежностях FastAPI
# або для прямого імпорту в сервісах.
# Це полегшує тестування шляхом мокання цього екземпляра.
status_repository = StatusRepository(StatusModel)

# TODO: Додати специфічні для StatusRepository методи, якщо вони будуть потрібні.
# Наприклад, отримання статусу за замовчуванням для певної сутності,
# або перевірка, чи є статус системним (незмінним).
#
# Поки що базових методів з BaseDictionaryRepository достатньо.
# `get(id)`, `get_by_code(code)`, `get_by_name(name)`, `get_multi()`, `create()`, `update()`, `delete()`.
#
# Все виглядає добре.
