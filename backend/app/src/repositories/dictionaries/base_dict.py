# backend/app/src/repositories/dictionaries/base_dict.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає базовий клас `BaseDictionaryRepository` для репозиторіїв,
що працюють з моделями-довідниками (`BaseDictModel`).
Він успадковує `BaseRepository` і може додавати специфічні методи для довідників,
наприклад, отримання запису за полем `code`.
"""

from typing import Optional, TypeVar, Generic
from sqlalchemy import select # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.dictionaries.base import BaseDictModel # Базова модель для довідників
from backend.app.src.repositories.base import BaseRepository, CreateSchemaType, UpdateSchemaType

# Типова змінна для моделі довідника
DictModelType = TypeVar("DictModelType", bound=BaseDictModel)

class BaseDictionaryRepository(
    BaseRepository[DictModelType, CreateSchemaType, UpdateSchemaType],
    Generic[DictModelType, CreateSchemaType, UpdateSchemaType]
):
    """
    Базовий репозиторій для моделей-довідників.
    Успадковує CRUD-операції від `BaseRepository` та додає метод `get_by_code`.
    """

    # Модель вже ініціалізується в BaseRepository, тут нічого не потрібно додавати в __init__

    async def get_by_code(self, db: AsyncSession, *, code: str) -> Optional[DictModelType]:
        """
        Отримує запис довідника за його унікальним символьним кодом.

        :param db: Асинхронна сесія бази даних.
        :param code: Символьний код для пошуку.
        :return: Об'єкт моделі довідника або None, якщо запис не знайдено.
        """
        try:
            statement = select(self.model).where(self.model.code == code)
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Помилка отримання {self.model.__name__} за кодом '{code}': {e}", exc_info=True)
            # Не кидаємо DatabaseErrorException тут, щоб сервіс міг обробити None
            return None


    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[DictModelType]:
        """
        Отримує запис довідника за його назвою.
        УВАГА: Назва може бути не унікальною, цей метод поверне перший знайдений.
        Для унікального пошуку краще використовувати `get_by_code` або `get`.

        :param db: Асинхронна сесія бази даних.
        :param name: Назва для пошуку.
        :return: Об'єкт моделі довідника або None, якщо запис не знайдено.
        """
        try:
            statement = select(self.model).where(self.model.name == name)
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Помилка отримання {self.model.__name__} за назвою '{name}': {e}", exc_info=True)
            return None

    # TODO: Розглянути додавання інших спільних методів для довідників, якщо потрібно.
    # Наприклад, отримання всіх активних записів (якщо є поле is_active або state_id).
    # async def get_all_active(self, db: AsyncSession) -> List[DictModelType]:
    #     statement = select(self.model).where(self.model.is_deleted == False) # Або по state_id
    #     result = await db.execute(statement)
    #     return result.scalars().all()

# TODO: Переконатися, що `BaseDictModel` (модель) має поле `code` та `name`,
#       що використовується в методах `get_by_code` та `get_by_name`.
#       (Так, `BaseDictModel` має `code`, а `name` успадковується з `BaseMainModel`).
# TODO: Узгодити використання `CreateSchemaType` та `UpdateSchemaType` з конкретними
#       схемами довідників, які будуть успадковувати `BaseDictCreateSchema` та `BaseDictUpdateSchema`.
#       Це робиться при визначенні конкретних репозиторіїв:
#       `class StatusRepository(BaseDictionaryRepository[StatusModel, StatusCreateSchema, StatusUpdateSchema]): ...`
#
# Все виглядає як хороший базовий клас для репозиторіїв довідників.
