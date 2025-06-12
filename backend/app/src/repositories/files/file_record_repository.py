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
from backend.app.src.config import logger # Використання спільного логера

# from backend.app.src.core.dicts import FileType as FileTypeEnum # Для фільтрації за purpose
# або from backend.app.src.models.files.file import FileTypeEnum, якщо він визначений у моделі

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

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `FileRecord`.
        """
        super().__init__(model=FileRecord)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_file_path(self, session: AsyncSession, file_path: str) -> Optional[FileRecord]:
        """
        Отримує запис файлу за його унікальним шляхом/ключем.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            file_path (str): Шлях до файлу або ключ в об'єктному сховищі.

        Returns:
            Optional[FileRecord]: Екземпляр моделі `FileRecord`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання FileRecord за file_path: {file_path}")
        stmt = select(self.model).where(self.model.file_path == file_path)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні FileRecord за file_path {file_path}: {e}", exc_info=True)
            return None

    async def get_files_by_uploader(
            self,
            session: AsyncSession,
            uploader_user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[FileRecord], int]:
        """
        Отримує список файлів, завантажених вказаним користувачем, з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            uploader_user_id (int): ID користувача, який завантажив файли.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[FileRecord], int]: Кортеж зі списком записів файлів та їх загальною кількістю.
        """
        logger.debug(f"Отримання файлів для uploader_user_id: {uploader_user_id}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"uploader_user_id": uploader_user_id}
        sort_by_field = "created_at"
        sort_order_str = "desc"  # Новіші файли першими

        try:
            items = await super().get_multi(
                session=session,
                skip=skip,
                limit=limit,
                filters=filters_dict,
                sort_by=sort_by_field,
                sort_order=sort_order_str
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} файлів для uploader_user_id: {uploader_user_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні файлів для uploader_user_id {uploader_user_id}: {e}", exc_info=True)
            return [], 0

    async def get_files_by_purpose(
            self,
            session: AsyncSession,
            purpose: str,  # Очікується значення з FileTypeEnum
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[FileRecord], int]:
        """
        Отримує список файлів за вказаним призначенням з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            purpose (str): Призначення файлу.
                           # TODO: [Enum Validation] Переконатися, що 'purpose' передається як Enum.value
                           #       або валідується відповідно до `technical_task.txt` / `structure-claude-v2.md`.
                           #       Розглянути використання FileTypeEnum з `backend.app.src.models.files.file`.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[FileRecord], int]: Кортеж зі списком записів файлів та їх загальною кількістю.
        """
        logger.debug(f"Отримання файлів за призначенням: {purpose}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"purpose": purpose}
        sort_by_field = "created_at"
        sort_order_str = "desc" # Новіші файли першими

        try:
            items = await super().get_multi(
                session=session,
                skip=skip,
                limit=limit,
                filters=filters_dict,
                sort_by=sort_by_field,
                sort_order=sort_order_str
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} файлів за призначенням: {purpose}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні файлів за призначенням {purpose}: {e}", exc_info=True)
            return [], 0


if __name__ == "__main__":
    # Демонстраційний блок для FileRecordRepository.
    logger.info("--- Репозиторій Записів Файлів (FileRecordRepository) ---")

    logger.info("Для тестування FileRecordRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.") # type: ignore
    logger.info(f"Він успадковує методи від BaseRepository для моделі {FileRecord.__name__}.") # type: ignore
    logger.info(f"  Очікує схему створення: {FileRecordCreateSchema.__name__}") # type: ignore
    logger.info(f"  Очікує схему оновлення: {FileRecordUpdateSchema.__name__} (зараз порожня)") # type: ignore

    logger.info("\nСпецифічні методи:") # type: ignore
    logger.info("  - get_by_file_path(session: AsyncSession, file_path: str)") # type: ignore
    logger.info("  - get_files_by_uploader(session: AsyncSession, uploader_user_id: int, skip: int = 0, limit: int = 100)") # type: ignore
    logger.info("  - get_files_by_purpose(session: AsyncSession, purpose: str, skip: int = 0, limit: int = 100)") # type: ignore

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.") # type: ignore
    logger.info("TODO: Інтегрувати Enum 'FileType' для аргументу `purpose` в get_files_by_purpose.") # type: ignore
