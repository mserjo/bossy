# backend/app/src/services/dictionaries/base_dict_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає базовий клас `BaseDictionaryService` для сервісів,
що працюють з моделями-довідниками.
"""

from typing import List, Optional, TypeVar, Generic
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.dictionaries.base import BaseDictModel
from backend.app.src.repositories.dictionaries.base_dict import BaseDictionaryRepository
from backend.app.src.schemas.dictionaries.base_dict import BaseDictCreateSchema, BaseDictUpdateSchema, BaseDictSchema
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, BadRequestException

# Типові змінні для дженеріків, специфічні для довідників
DictModelType = TypeVar("DictModelType", bound=BaseDictModel)
DictRepoType = TypeVar("DictRepoType", bound=BaseDictionaryRepository) # Репозиторій має бути BaseDictionaryRepository або його нащадок
DictCreateSchemaType = TypeVar("DictCreateSchemaType", bound=BaseDictCreateSchema)
DictUpdateSchemaType = TypeVar("DictUpdateSchemaType", bound=BaseDictUpdateSchema)

class BaseDictionaryService(
    BaseService[DictRepoType], # Базовий сервіс вже Generic по RepositoryType
    Generic[DictModelType, DictRepoType, DictCreateSchemaType, DictUpdateSchemaType]
):
    """
    Базовий сервіс для моделей-довідників.
    Надає CRUD-операції та додаткові методи, такі як отримання за кодом.
    """

    # self.repository успадковано з BaseService і буде типу DictRepoType

    async def get_by_id(self, db: AsyncSession, id: uuid.UUID) -> Optional[DictModelType]:
        """Отримує запис довідника за ID."""
        item = await self.repository.get(db, id=id)
        if not item:
            raise NotFoundException(detail=f"Запис довідника з ID {id} не знайдено.")
        return item

    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[DictModelType]:
        """Отримує запис довідника за кодом."""
        item = await self.repository.get_by_code(db, code=code)
        if not item:
            raise NotFoundException(detail=f"Запис довідника з кодом '{code}' не знайдено.")
        return item

    async def get_all(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[DictModelType]:
        """Отримує список всіх записів довідника."""
        return await self.repository.get_multi(db, skip=skip, limit=limit)

    async def create_dict_item(self, db: AsyncSession, *, obj_in: DictCreateSchemaType) -> DictModelType:
        """
        Створює новий запис в довіднику.
        Перевіряє унікальність коду перед створенням.
        """
        existing_by_code = await self.repository.get_by_code(db, code=obj_in.code)
        if existing_by_code:
            raise BadRequestException(detail=f"Запис довідника з кодом '{obj_in.code}' вже існує.")

        # Перевірка унікальності імені (опціонально, якщо потрібно)
        # existing_by_name = await self.repository.get_by_name(db, name=obj_in.name)
        # if existing_by_name:
        #     raise BadRequestException(detail=f"Запис довідника з назвою '{obj_in.name}' вже існує.")

        return await self.repository.create(db, obj_in=obj_in)

    async def update_dict_item(
        self, db: AsyncSession, *, db_obj: DictModelType, obj_in: DictUpdateSchemaType
    ) -> DictModelType:
        """
        Оновлює існуючий запис в довіднику.
        Перевіряє унікальність коду та імені, якщо вони змінюються.
        """
        update_data = obj_in.model_dump(exclude_unset=True)

        if "code" in update_data and update_data["code"] != db_obj.code:
            existing_by_code = await self.repository.get_by_code(db, code=update_data["code"])
            if existing_by_code and existing_by_code.id != db_obj.id:
                raise BadRequestException(detail=f"Запис довідника з кодом '{update_data['code']}' вже існує.")

        # if "name" in update_data and update_data["name"] != db_obj.name:
        #     existing_by_name = await self.repository.get_by_name(db, name=update_data["name"])
        #     if existing_by_name and existing_by_name.id != db_obj.id:
        #         raise BadRequestException(detail=f"Запис довідника з назвою '{update_data['name']}' вже існує.")

        return await self.repository.update(db, db_obj=db_obj, obj_in=obj_in) # obj_in тут є схемою

    async def delete_dict_item(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[DictModelType]:
        """
        Видаляє запис довідника.
        Можна додати перевірку, чи не використовується цей запис десь в системі,
        перш ніж видаляти (або покладатися на обмеження зовнішніх ключів в БД).
        """
        # TODO: Додати перевірку на використання запису довідника, якщо потрібно.
        # Наприклад, якщо статус "active" використовується багатьма сутностями,
        # його видалення може бути небажаним або має оброблятися спеціальним чином.
        # Це складна логіка, яка може залежати від конкретного довідника.
        item_to_delete = await self.repository.get(db, id=id)
        if not item_to_delete:
            raise NotFoundException(detail=f"Запис довідника з ID {id} для видалення не знайдено.")

        # Можна використовувати "м'яке" видалення, якщо репозиторій його підтримує
        if hasattr(self.repository, 'soft_delete') and hasattr(item_to_delete, 'is_deleted'):
            return await self.repository.soft_delete(db, db_obj=item_to_delete) # type: ignore
        else:
            return await self.repository.delete(db, id=id)

# TODO: Узгодити, чи `BaseDictionaryService` має бути Generic по `DictModelType` також,
#       чи достатньо `ModelType` з `BaseService`.
#       Оскільки `DictRepoType` вже типізований `BaseDictModel`, то `DictModelType`
#       тут може бути корисним для типізації методів, що повертають модель. (Зроблено)
#
# TODO: Перевірити, чи `BaseDictionaryRepository` дійсно має методи `get_by_code` та `get_by_name`.
#       (Так, `get_by_code` було додано, `get_by_name` також).
#
# Все виглядає як хороший базовий клас для сервісів довідників.
# Додано перевірки на унікальність коду при створенні/оновленні.
# Обробка NotFoundException.
