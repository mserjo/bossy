# backend/app/src/repositories/files/file_record_repository.py
"""
Репозиторій для моделі "Запис Файлу" (FileRecord).

Цей модуль визначає клас `FileRecordRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з записами про завантажені файли.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel as PydanticBaseModel  # Для UpdateSchemaType

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.files.file import FileRecord
from backend.app.src.schemas.files.file import FileRecordCreateSchema
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# from backend.app.src.core.dicts import FileType as FileTypeEnum # Для фільтрації за purpose

# Записи файлів зазвичай не оновлюються після створення (окрім, можливо, metadata або purpose).
# Якщо потрібне оновлення, можна створити більш конкретну схему.
class FileRecordUpdateSchema(PydanticBaseModel):
    # Наприклад, якщо дозволено оновлювати лише metadata або purpose:
    # metadata: Optional[Dict[str, Any]] = None
    # purpose: Optional[str] = None # TODO: Використати FileTypeEnum.value
    pass


class FileRecordRepository(BaseRepository[FileRecord, FileRecordCreateSchema, FileRecordUpdateSchema]):
    """
    Репозиторій для управління записами файлів (`FileRecord`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання файлів за шляхом, завантажувачем або призначенням.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `FileRecord`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=FileRecord)

    async def get_by_file_path(self, file_path: str) -> Optional[FileRecord]:
        """
        Отримує запис файлу за його унікальним шляхом/ключем.

        Args:
            file_path (str): Шлях до файлу або ключ в об'єктному сховищі.

        Returns:
            Optional[FileRecord]: Екземпляр моделі `FileRecord`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(self.model.file_path == file_path)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_files_by_uploader(
            self,
            uploader_user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[FileRecord], int]:
        """
        Отримує список файлів, завантажених вказаним користувачем, з пагінацією.

        Args:
            uploader_user_id (int): ID користувача, який завантажив файли.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[FileRecord], int]: Кортеж зі списком записів файлів та їх загальною кількістю.
        """
        filters = [self.model.uploader_user_id == uploader_user_id]
        order_by = [self.model.created_at.desc()]  # Новіші файли першими
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)

    async def get_files_by_purpose(
            self,
            purpose: str,  # Очікується значення з FileTypeEnum
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[FileRecord], int]:
        """
        Отримує список файлів за вказаним призначенням з пагінацією.

        Args:
            purpose (str): Призначення файлу (значення з `core.dicts.FileType`).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[FileRecord], int]: Кортеж зі списком записів файлів та їх загальною кількістю.
        """
        # TODO: Переконатися, що 'purpose' передається як Enum.value або валідується відповідно.
        filters = [self.model.purpose == purpose]
        order_by = [self.model.created_at.desc()]
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)


if __name__ == "__main__":
    # Демонстраційний блок для FileRecordRepository.
    logger.info("--- Репозиторій Записів Файлів (FileRecordRepository) ---")

    logger.info("Для тестування FileRecordRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {FileRecord.__name__}.")
    logger.info(f"  Очікує схему створення: {FileRecordCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {FileRecordUpdateSchema.__name__} (зараз порожня)")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_file_path(file_path: str)")
    logger.info("  - get_files_by_uploader(uploader_user_id: int, skip: int = 0, limit: int = 100)")
    logger.info("  - get_files_by_purpose(purpose: str, skip: int = 0, limit: int = 100)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    logger.info("TODO: Інтегрувати Enum 'FileType' для аргументу `purpose` в get_files_by_purpose.")
