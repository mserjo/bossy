# backend/app/src/repositories/files/file.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `FileModel`.
Надає методи для управління метаданими завантажених файлів.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.files.file import FileModel
from backend.app.src.schemas.files.file import FileCreateSchema, FileUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class FileRepository(BaseRepository[FileModel, FileCreateSchema, FileUpdateSchema]):
    """
    Репозиторій для роботи з моделлю файлів (`FileModel`).
    """

    async def get_by_storage_path(self, db: AsyncSession, *, storage_path: str) -> Optional[FileModel]:
        """
        Отримує запис файлу за його шляхом у сховищі.

        :param db: Асинхронна сесія бази даних.
        :param storage_path: Шлях до файлу в сховищі.
        :return: Об'єкт FileModel або None.
        """
        statement = select(self.model).where(self.model.storage_path == storage_path)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_files_by_category(
        self, db: AsyncSession, *, category_code: str,
        skip: int = 0, limit: int = 100
    ) -> List[FileModel]:
        """
        Отримує список файлів за вказаною категорією.

        :param db: Асинхронна сесія бази даних.
        :param category_code: Код категорії файлу.
        :param skip: Кількість записів для пропуску.
        :param limit: Максимальна кількість записів.
        :return: Список об'єктів FileModel.
        """
        statement = select(self.model).where(self.model.file_category_code == category_code)
        statement = statement.order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_files_for_user(
        self, db: AsyncSession, *, user_id: uuid.UUID,
        category_code: Optional[str] = None,
        skip: int = 0, limit: int = 100
    ) -> List[FileModel]:
        """
        Отримує список файлів, завантажених вказаним користувачем,
        опціонально фільтруючи за категорією.
        """
        statement = select(self.model).where(self.model.uploaded_by_user_id == user_id)
        if category_code:
            statement = statement.where(self.model.file_category_code == category_code)
        statement = statement.order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    # `create`, `get`, `update`, `delete` успадковані.
    # `FileCreateSchema` має містити всі необхідні поля для створення запису FileModel.
    # `FileUpdateSchema` для оновлення метаданих.

file_repository = FileRepository(FileModel)

# TODO: Розглянути методи для пошуку файлів за `original_filename` (з урахуванням ilike).
# TODO: Якщо буде реалізовано "м'яке" видалення для FileModel, додати відповідні методи.
#       (Наразі FileModel успадковує від BaseModel, яка не має is_deleted/deleted_at).
#
# Все виглядає добре. Надано основні методи для роботи з метаданими файлів.
# Фізичне завантаження/видалення файлів зі сховища - це відповідальність сервісного шару.
