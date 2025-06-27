# backend/app/src/services/dictionaries/status_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс для управління довідником статусів (`StatusModel`).
"""

from backend.app.src.models.dictionaries.status import StatusModel
from backend.app.src.repositories.dictionaries.status import StatusRepository, status_repository
from backend.app.src.schemas.dictionaries.status import StatusCreateSchema, StatusUpdateSchema
from backend.app.src.services.dictionaries.base_dict_service import BaseDictionaryService

class StatusService(BaseDictionaryService[StatusModel, StatusRepository, StatusCreateSchema, StatusUpdateSchema]):
    """
    Сервіс для управління довідником статусів.
    Успадковує базову CRUD-логіку для довідників.
    """
    # Тут можна додати специфічні для статусів методи бізнес-логіки, якщо потрібно.
    # Наприклад, перевірка, чи можна змінити статус певної сутності з X на Y,
    # або отримання списку доступних наступних статусів.
    # Але така логіка може бути і в сервісах, що працюють з основними сутностями.
    pass

status_service = StatusService(status_repository)

# TODO: Додати специфічну бізнес-логіку для статусів, якщо вона виходить
#       за рамки стандартних CRUD операцій та перевірок унікальності коду.
#       Наприклад, перевірка, чи є статус системним і чи можна його редагувати/видаляти.
#
# Все виглядає добре для базового сервісу статусів.
