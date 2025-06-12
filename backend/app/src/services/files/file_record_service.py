# backend/app/src/services/files/file_record_service.py
"""
Сервіс для управління метаданими файлів (FileRecord).

Відповідає за створення, отримання, оновлення та видалення записів про файли в базі даних.
Фактичне завантаження або видалення файлів зі сховища координується з іншими сервісами
(наприклад, FileUploadService).
"""
from typing import List, Optional # Any, Tuple видалено
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Оновлено імпорт
from sqlalchemy.orm import selectinload, noload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.files.file import FileRecord
from backend.app.src.models.auth.user import User
from backend.app.src.models.groups.group import Group

from backend.app.src.schemas.files.file import (
    FileRecordCreate,
    FileRecordUpdate,
    FileRecordResponse
)
from backend.app.src.config import logger  # Використання спільного логера з конфігу
from backend.app.src.config import settings


# from .file_upload_service import FileUploadService # Розглянути переміщення імпорту, якщо немає циркулярності

class FileRecordService(BaseService): # type: ignore
    """
    Сервіс для управління записами метаданих файлів (сутності FileRecord).
    Обробляє CRUD-операції для цих записів. Фактичне зберігання/видалення файлів
    зазвичай координується з FileUploadService або утилітою для роботи зі сховищем.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("FileRecordService ініціалізовано.")

    async def get_file_record_by_id(self, file_id: UUID, load_relations: bool = True) -> Optional[FileRecordResponse]:
        """
        Отримує запис файлу за його ID.
        За замовчуванням завантажує пов'язані сутності uploader_user та group.

        :param file_id: ID запису файлу.
        :param load_relations: Чи завантажувати пов'язані сутності.
        :return: Pydantic схема FileRecordResponse або None, якщо не знайдено.
        """
        logger.debug(f"Спроба отримання запису файлу за ID: {file_id}")
        try:
            query = select(FileRecord)
            if load_relations:
                options_to_load = []
                if hasattr(FileRecord, 'uploader_user'):
                    options_to_load.append(selectinload(FileRecord.uploader_user).options(selectinload(User.user_type)))
                if hasattr(FileRecord, 'group'):
                    options_to_load.append(selectinload(FileRecord.group))
                if options_to_load:
                    query = query.options(*options_to_load)
            else:
                if hasattr(FileRecord, 'uploader_user'): query = query.options(noload(FileRecord.uploader_user))
                if hasattr(FileRecord, 'group'): query = query.options(noload(FileRecord.group))

            stmt = query.where(FileRecord.id == file_id)
            record_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

            if record_db:
                logger.info(f"Запис файлу з ID '{file_id}' (Ім'я: '{record_db.file_name}') знайдено.")
                return FileRecordResponse.model_validate(record_db)
            logger.info(f"Запис файлу з ID '{file_id}' не знайдено.")
            return None
        except Exception as e:
            logger.error(f"Помилка при отриманні запису файлу ID {file_id}: {e}", exc_info=settings.DEBUG)
            return None

    async def create_file_record(self, record_data: FileRecordCreate,
                                 uploader_user_id: Optional[UUID] = None) -> FileRecordResponse: # type: ignore
        """
        Створює новий запис файлу.
        Зазвичай викликається *після* успішного завантаження файлу до сховища.
        `record_data` повинен містити `storage_path` та іншу метаінформацію.
        `uploader_user_id` з параметра має пріоритет над `record_data.uploader_user_id`.

        :param record_data: Дані для створення запису (Pydantic схема).
        :param uploader_user_id: ID користувача, що завантажив файл (опціонально, може бути в record_data).
        :return: Pydantic схема створеного FileRecordResponse.
        :raises ValueError: Якщо пов'язані сутності не знайдено або шлях зберігання не унікальний. # i18n
        """
        logger.debug(f"Спроба створення нового запису для файлу: '{record_data.file_name}'")

        effective_uploader_user_id = uploader_user_id or record_data.uploader_user_id

        if effective_uploader_user_id and not await self.db_session.get(User, effective_uploader_user_id):
            # i18n
            raise ValueError(f"Користувача-завантажувача з ID '{effective_uploader_user_id}' не знайдено.")
        if record_data.group_id and not await self.db_session.get(Group, record_data.group_id):
            # i18n
            raise ValueError(f"Групу з ID '{record_data.group_id}' не знайдено.")

        # Перевірка унікальності storage_path
        # TODO: Уточнити, чи storage_path має бути глобально унікальним, чи унікальним в межах uploader/group/entity.
        # Поки що припускаємо глобальну унікальність.
        stmt_path_check = select(FileRecord.id).where(FileRecord.storage_path == record_data.storage_path)
        if (await self.db_session.execute(stmt_path_check)).scalar_one_or_none():
            msg = f"Запис файлу зі шляхом зберігання '{record_data.storage_path}' вже існує."  # i18n
            logger.warning(msg)
            raise ValueError(msg)

        # Створення запису FileRecord
        # created_at, updated_at встановлюються автоматично моделлю/БД
        new_record_db = FileRecord(
            **record_data.model_dump(exclude_unset=True),  # Pydantic v2
            uploader_user_id=effective_uploader_user_id  # Пріоритет параметра функції
            # `created_at` та `updated_at` повинні встановлюватися автоматично моделлю
        )

        self.db_session.add(new_record_db)
        try:
            await self.commit()
            # Оновлюємо для завантаження зв'язків для відповіді
            # Використовуємо get_file_record_by_id для консистентного завантаження зв'язків
            created_record_response = await self.get_file_record_by_id(new_record_db.id, load_relations=True)
            if not created_record_response:  # Малоймовірно, якщо коміт пройшов успішно
                logger.error(f"Не вдалося отримати щойно створений запис файлу ID {new_record_db.id} після коміту.")
                # i18n
                raise RuntimeError("Помилка створення запису файлу: не вдалося отримати після збереження.")

            logger.info(f"Запис файлу '{new_record_db.file_name}' (ID: {new_record_db.id}) успішно створено.")
            return created_record_response
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності '{record_data.file_name}': {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося створити запис файлу через конфлікт даних.")  # i18n
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка '{record_data.file_name}': {e}", exc_info=settings.DEBUG)
            raise

    async def update_file_record_metadata(
            self,
            file_id: UUID,
            metadata_update_data: FileRecordUpdate,
            # TODO: Додати current_user_id для аудиту, якщо поле updated_by_user_id є в моделі FileRecord
            # current_user_id: Optional[UUID] = None
    ) -> Optional[FileRecordResponse]:
        """Оновлює метадані запису файлу (наприклад, ім'я, опис)."""
        # logger.debug(f"Спроба оновлення метаданих для запису файлу ID: {file_id} користувачем ID: {current_user_id or 'System'}")
        logger.debug(f"Спроба оновлення метаданих для запису файлу ID: {file_id}")

        record_db = await self.db_session.get(FileRecord, file_id)
        if not record_db:
            logger.warning(f"Запис файлу ID '{file_id}' не знайдено для оновлення метаданих.")
            return None

        update_data = metadata_update_data.model_dump(exclude_unset=True)  # Pydantic v2

        updated_fields_count = 0
        # Поля, які не можна оновлювати цим методом (або взагалі)
        restricted_fields = {'id', 'storage_path', 'uploader_user_id', 'created_at', 'group_id',
                             'file_type', 'size_bytes', 'entity_type', 'entity_id'}
        # TODO: Уточнити список полів, які не можна змінювати, згідно ТЗ.

        for field, value in update_data.items():
            if field in restricted_fields:
                logger.warning(f"Спроба оновлення обмеженого поля '{field}' для запису ID '{file_id}' проігноровано.")
                continue
            if hasattr(record_db, field):
                setattr(record_db, field, value)
                updated_fields_count += 1
            else:  # Поле з Pydantic схеми не існує в моделі SQLAlchemy
                logger.warning(f"Поле '{field}' не знайдено в моделі FileRecord для оновлення запису ID '{file_id}'.")

        if updated_fields_count == 0:
            logger.info(f"Не надано полів для оновлення або зміни не потрібні для запису ID '{file_id}'.")
            return await self.get_file_record_by_id(file_id)  # Повертаємо поточний стан

        # if hasattr(record_db, 'updated_by_user_id') and current_user_id:
        #     record_db.updated_by_user_id = current_user_id
        if hasattr(record_db, 'updated_at'):  # Модель повинна автоматично оновлювати updated_at
            record_db.updated_at = datetime.now(timezone.utc)

        self.db_session.add(record_db)
        try:
            await self.commit()
            # logger.info(f"Метадані для запису файлу ID '{file_id}' оновлено користувачем ID '{current_user_id or 'System'}'.")
            logger.info(f"Метадані для запису файлу ID '{file_id}' успішно оновлено.")
            # Повертаємо оновлений запис з усіма зв'язками
            return await self.get_file_record_by_id(file_id, load_relations=True)
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка оновлення метаданих для запису ID '{file_id}': {e}", exc_info=settings.DEBUG)
            raise

    async def delete_file_record(
            self,
            file_id: UUID,
            # current_user_id: Optional[UUID] = None, # Для аудиту
            delete_from_storage: bool = True  # Чи видаляти також фізичний файл
    ) -> bool:
        """
        Видаляє запис файлу з бази даних.
        Опціонально може ініціювати видалення файлу зі сховища.
        """
        # logger.debug(f"Користувач ID '{current_user_id or 'System'}' намагається видалити запис файлу ID: {file_id}. Видалення зі сховища: {delete_from_storage}")
        logger.debug(f"Спроба видалення запису файлу ID: {file_id}. Видалення зі сховища: {delete_from_storage}")

        record_db = await self.db_session.get(FileRecord, file_id)
        if not record_db:
            logger.warning(f"Запис файлу ID '{file_id}' не знайдено для видалення.")
            return False

        storage_path_to_delete = getattr(record_db, 'storage_path', None)

        await self.db_session.delete(record_db)
        try:
            await self.commit()
            # logger.info(f"Запис файлу ID '{file_id}' (Шлях: {storage_path_to_delete}) видалено з БД користувачем '{current_user_id or 'System'}'.")
            logger.info(f"Запис файлу ID '{file_id}' (Шлях: {storage_path_to_delete}) успішно видалено з БД.")
        except IntegrityError as e:  # Якщо запис файлу використовується (наприклад, FK в User.avatar_id)
            await self.rollback()
            logger.error(
                f"Помилка цілісності при видаленні запису файлу ID '{file_id}': {e}. Можливо, він використовується.",
                exc_info=settings.DEBUG)
            # i18n
            raise ValueError(f"Запис файлу '{record_db.file_name}' використовується і не може бути видалений.")
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка коміту видалення запису файлу ID '{file_id}' з БД: {e}", exc_info=settings.DEBUG)
            return False  # Помилка БД, не продовжуємо до видалення зі сховища

        if delete_from_storage and storage_path_to_delete:
            logger.info(f"Ініціювання видалення фактичного файлу зі сховища за шляхом: {storage_path_to_delete}")
            # TODO: Реалізувати логіку видалення файлу зі сховища.
            #  - Порядок операцій: спочатку видалити файл, потім запис з БД, або навпаки?
            #    Якщо спочатку файл: що робити, якщо видалення запису з БД не вдалося? Файл буде "сиротою".
            #    Якщо спочатку запис з БД (як зараз): що робити, якщо видалення файлу не вдалося? Файл буде "сиротою" без запису.
            #    Потрібна стратегія для обробки таких випадків (наприклад, фонові завдання для очищення).
            #  - Для локального сховища: os.remove(full_path_to_file). Потрібен FileUploadService.
            try:
                from .file_upload_service import FileUploadService  # Локальний імпорт для уникнення циркулярності
                upload_service = FileUploadService()  # FileUploadService не потребує db_session для delete_actual_file
                await upload_service.delete_actual_file(storage_path_to_delete)
                logger.info(f"Фактичний файл за шляхом '{storage_path_to_delete}' успішно видалено.")
            except Exception as e:
                logger.error(
                    f"Помилка при видаленні файлу '{storage_path_to_delete}' зі сховища: {e}. Запис в БД вже видалено.",
                    exc_info=True)  # i18n log
                # Запис в БД вже видалено. Потрібен механізм для обробки таких "файлів-сиріт".
        elif delete_from_storage and not storage_path_to_delete:
            logger.warning(
                f"Прапорець delete_from_storage встановлено, але шлях зберігання для запису ID '{file_id}' не визначено.")

        return True

    async def list_file_records(
            self,
            uploader_user_id: Optional[UUID] = None,
            group_id: Optional[UUID] = None,
            entity_type: Optional[str] = None,  # Додано фільтр
            entity_id: Optional[UUID] = None,  # Додано фільтр
            mime_type_pattern: Optional[str] = None,  # Наприклад, 'image/%'
            skip: int = 0,
            limit: int = 100
    ) -> List[FileRecordResponse]:
        """Перелічує записи файлів з можливістю фільтрації та пагінації."""
        logger.debug(
            f"Перелік записів файлів: користувач={uploader_user_id}, група={group_id}, тип_сутності='{entity_type}', ID_сутності={entity_id}, MIME='{mime_type_pattern}'")

        query = select(FileRecord)
        options_to_load = []
        if hasattr(FileRecord, 'uploader_user'): options_to_load.append(
            selectinload(FileRecord.uploader_user).options(selectinload(User.user_type)))
        if hasattr(FileRecord, 'group'): options_to_load.append(selectinload(FileRecord.group))
        if options_to_load: query = query.options(*options_to_load)

        conditions = []
        if uploader_user_id: conditions.append(FileRecord.uploader_user_id == uploader_user_id)
        if group_id: conditions.append(FileRecord.group_id == group_id)
        if entity_type: conditions.append(FileRecord.entity_type == entity_type)
        if entity_id: conditions.append(FileRecord.entity_id == entity_id)
        if mime_type_pattern: conditions.append(FileRecord.mime_type.ilike(mime_type_pattern))  # type: ignore

        if conditions:
            query = query.where(*conditions)

        # TODO: Додати можливість передачі параметрів сортування (sort_by, sort_order)
        stmt = query.order_by(FileRecord.created_at.desc()).offset(skip).limit(limit)

        records_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [FileRecordResponse.model_validate(r) for r in records_db]  # Pydantic v2
        logger.info(f"Отримано {len(response_list)} записів файлів.")
        return response_list


logger.debug(f"{FileRecordService.__name__} (сервіс записів файлів) успішно визначено.")
