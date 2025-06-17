# backend/app/src/services/files/file_upload_service.py
"""
Сервіс для обробки завантаження файлів.

Відповідає за ініціалізацію процесу завантаження, обробку частин файлу,
завершення завантаження (включаючи переміщення файлу до постійного сховища)
та координацію з `FileRecordService` для збереження метаданих файлу.
Наразі реалізовано для локального зберігання файлів.
"""
import os
import aiofiles  # Для асинхронних файлових операцій
import shutil  # Для переміщення файлів
from typing import Optional, Dict, Any, Set
from uuid import uuid4 # UUID видалено
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.utils import secure_filename  # Для очищення імен файлів

from backend.app.src.services.base import BaseService
from backend.app.src.config.settings import settings
from backend.app.src.schemas.files.upload import (
    FileUploadInitiateRequest,
    FileUploadInitiateResponse,
    FileUploadCompleteRequest,
    FileUploadResponse
)
from backend.app.src.schemas.files.file import FileRecordCreate # FileRecordResponse не використовується напряму в цьому файлі
from backend.app.src.services.files.file_record_service import FileRecordService
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)


class FileUploadService(BaseService): # type: ignore видалено
    """
    Сервіс для обробки процесу завантаження файлів.
    Включає ініціалізацію завантажень, обробку завантажених файлів (переміщення з тимчасового
    в постійне сховище) та координацію з FileRecordService для збереження метаданих.
    Зберігання файлів відбувається локально.
    """

    def __init__(self, db_session: AsyncSession, file_record_service: FileRecordService):
        super().__init__(db_session)
        self.file_record_service = file_record_service
        self.local_storage_base_path: Path
        self.temp_upload_dir: Path
        self.permanent_storage_dir: Path
        self.max_file_size_bytes: int
        self.allowed_mime_types: Set[str]
        self._setup_local_storage_paths()
        logger.info("FileUploadService ініціалізовано.")

    def _setup_local_storage_paths(self):
        """
        Налаштовує шляхи локального сховища з конфігурації та забезпечує існування директорій.
        """
        _base_path_str = getattr(settings, 'LOCAL_FILE_STORAGE_PATH', "./static_uploads")
        self.local_storage_base_path = Path(_base_path_str).resolve()  # Робимо шлях абсолютним
        self.temp_upload_dir = self.local_storage_base_path / "temp"
        self.permanent_storage_dir = self.local_storage_base_path / "permanent"

        _max_size_setting = getattr(settings, 'MAX_FILE_SIZE_BYTES', None)
        self.max_file_size_bytes = _max_size_setting if isinstance(_max_size_setting, int) else (
                    10 * 1024 * 1024)  # 10MB за замовчуванням

        _allowed_mimes_setting = getattr(settings, 'ALLOWED_MIME_TYPES', None)
        # TODO: Завантажувати ALLOWED_MIME_TYPES з конфігурації, де вони визначені як множина рядків.
        self.allowed_mime_types = _allowed_mimes_setting if isinstance(_allowed_mimes_setting, set) else \
            {"image/jpeg", "image/png", "image/gif", "application/pdf", "video/mp4"}

        try:
            self.temp_upload_dir.mkdir(parents=True, exist_ok=True)
            self.permanent_storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info(
                f"Шляхи локального сховища ініціалізовано: TEMP='{self.temp_upload_dir}', PERMANENT='{self.permanent_storage_dir}'")
        except Exception as e:
            logger.error(f"Не вдалося створити директорії локального сховища: {e}", exc_info=True)
            # Якщо директорії не створено, сервіс не зможе працювати. Можливо, варто кинути виняток.
            raise RuntimeError(_("file_upload.errors.critical_storage_setup_failed", error_message=str(e)))

    async def initiate_upload(
            self,
            initiate_data: FileUploadInitiateRequest,
            uploader_user_id: int
    ) -> FileUploadInitiateResponse:
        """Ініціює процес завантаження файлу."""
        logger.info(f"Ініціація завантаження для файлу '{initiate_data.file_name}' користувачем ID: {uploader_user_id}.")

        if initiate_data.size_bytes <= 0:
            raise ValueError(_("file_upload.errors.initiate.size_must_be_positive"))
        if initiate_data.size_bytes > self.max_file_size_bytes:
            raise ValueError(
                _("file_upload.errors.initiate.size_exceeds_limit", size=initiate_data.size_bytes, limit=self.max_file_size_bytes))

        if initiate_data.mime_type not in self.allowed_mime_types:
            logger.error(f"MIME тип '{initiate_data.mime_type}' не дозволено. Дозволені: {self.allowed_mime_types}.")
            raise ValueError(_("file_upload.errors.initiate.mime_type_not_allowed", mime_type=initiate_data.mime_type))

        upload_id = uuid4()
        # Для локального сховища, upload_id просто ідентифікує сесію завантаження.
        # Тимчасова директорія для частин файлу (якщо будуть чанки) або для цілого файлу.
        # (Наразі handle_file_data_upload створює цю директорію).
        logger.info(f"ID завантаження '{upload_id}' згенеровано. Очікується надсилання даних.")
        return FileUploadInitiateResponse(upload_id=upload_id,
                                          message=_("file_upload.initiate.success_message"))

    async def handle_file_data_upload(
            self, upload_id: UUID, file_name: str, file_data_chunk: bytes,
            is_last_chunk: bool = True, chunk_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Обробляє отримані дані (або частину даних) файлу."""
        # TODO: Додати перевірку загального розміру файлу при завантаженні частинами.
        logger.info(
            f"Обробка даних для ID завантаження '{upload_id}', файл '{file_name}', чанк: {chunk_number if chunk_number is not None else 'N/A'}, останній: {is_last_chunk}.")

        # Очищення імені файлу для безпеки
        safe_file_name = secure_filename(file_name)
        if not safe_file_name:
            raise ValueError(_("file_upload.errors.invalid_file_name"))

        temp_dir_for_upload = self.temp_upload_dir / str(upload_id)
        try:
            await aiofiles.os.makedirs(temp_dir_for_upload, exist_ok=True) # Замінено на async mkdir
        except Exception as e:
            logger.error(f"Не вдалося створити тимчасову директорію {temp_dir_for_upload} для ID {upload_id}: {e}",
                         exc_info=True)
            raise ValueError(_("file_upload.errors.upload_chunk.prepare_failed", upload_id=str(upload_id)))

        temp_file_path = temp_dir_for_upload / safe_file_name

        try:
            # 'wb' для першого чанку або якщо файл цілий, 'ab' для наступних чанків
            mode = 'wb' if (chunk_number == 1 or chunk_number is None) else 'ab'
            async with aiofiles.open(temp_file_path, mode) as f:
                await f.write(file_data_chunk)
            logger.info(f"Дані записано до тимчасового файлу: {temp_file_path} (режим: {mode})")

            if is_last_chunk:
                return {"status": "success", "message": _("file_upload.upload_chunk.last_chunk_received"),
                        "temp_path": str(temp_file_path)}
            else:
                return {"status": "chunk_received", "message": _("file_upload.upload_chunk.chunk_received", chunk_number=chunk_number),
                        "next_chunk_expected": (chunk_number or 0) + 1}
        except Exception as e:
            logger.error(f"Помилка запису даних для ID '{upload_id}' у {temp_file_path}: {e}", exc_info=True)
            if temp_file_path.exists():  # Спроба очищення, якщо файл було частково створено
                try:
                    os.remove(temp_file_path) # Note: os.remove is synchronous, consider aiofiles.os.remove if truly async needed here
                except Exception as e_del:
                    logger.error(f"Не вдалося очистити частковий тимчасовий файл {temp_file_path}: {e_del}")
            raise ValueError(_("file_upload.errors.upload_chunk.save_failed", upload_id=str(upload_id)))

    async def complete_upload(
            self, upload_id: UUID, completion_data: FileUploadCompleteRequest, uploader_user_id: int
    ) -> FileUploadResponse:
        """Завершує процес завантаження, переміщує файл та створює запис в БД."""
        logger.info(
            f"Завершення завантаження для ID '{upload_id}', файл '{completion_data.file_name}' користувачем ID: {uploader_user_id}.")

        safe_original_filename = secure_filename(completion_data.file_name)
        if not safe_original_filename:
            raise ValueError(_("file_upload.errors.complete.invalid_file_name"))

        temp_file_path = self.temp_upload_dir / str(upload_id) / safe_original_filename
        if not temp_file_path.exists() or not temp_file_path.is_file():
            logger.error(f"Тимчасовий файл для ID '{upload_id}' за шляхом {temp_file_path} не знайдено.")
            raise ValueError(_("file_upload.errors.complete.data_not_found", upload_id=str(upload_id)))

        actual_size = temp_file_path.stat().st_size
        if actual_size != completion_data.size_bytes:
            logger.warning(
                f"Невідповідність розміру файлу для ID '{upload_id}'. Клієнт: {completion_data.size_bytes}, Факт: {actual_size}. Використовується фактичний розмір.")

        # Генерація унікального підкаталогу для постійного зберігання
        permanent_file_subdir_name = str(uuid4())  # Унікальний підкаталог
        permanent_file_target_dir = self.permanent_storage_dir / permanent_file_subdir_name
        await aiofiles.os.makedirs(permanent_file_target_dir, exist_ok=True) # Замінено на async mkdir
        permanent_file_path = permanent_file_target_dir / safe_original_filename

        temp_parent_dir_to_clean = self.temp_upload_dir / str(upload_id)

        try:
            # Використовуємо aiofiles.os.rename для асинхронного переміщення
            await aiofiles.os.rename(str(temp_file_path), str(permanent_file_path))
            logger.info(f"Файл переміщено з '{temp_file_path}' до постійного сховища: '{permanent_file_path}'.")
        except Exception as e:
            logger.error(f"Не вдалося перемістити файл з тимчасового до постійного сховища для ID '{upload_id}': {e}",
                         exc_info=True)
            raise ValueError(_("file_upload.errors.complete.save_failed"))
        finally:  # Очищення тимчасової директорії для цього завантаження
            if await aiofiles.os.path.exists(temp_parent_dir_to_clean): # Замінено на async exists
                try:
                    await self._async_rmtree(temp_parent_dir_to_clean) # Замінено на async rmtree
                    logger.debug(f"Тимчасову директорію {temp_parent_dir_to_clean} очищено.")
                except Exception as e_rm:
                    logger.error(f"Не вдалося очистити тимчасову директорію {temp_parent_dir_to_clean}: {e_rm}")

        # storage_path відносно permanent_storage_dir
        storage_path_for_record = Path(permanent_file_subdir_name) / safe_original_filename
        # file_url відносно STATIC_URL_PATH, який вказує на local_storage_base_path
        # Наприклад, якщо STATIC_URL_PATH = /static/uploads, а local_storage_base_path = ./static_uploads
        # тоді file_url буде /static/uploads/permanent/<UUID_SUBDIR>/<filename>
        # TODO: Перевірити, чи settings.STATIC_URL_PATH визначено та використовується коректно.
        static_url_prefix = getattr(settings, 'STATIC_URL_PATH', '/static').rstrip('/')
        file_url_for_record = f"{static_url_prefix}/permanent/{storage_path_for_record}"

        # TODO: Узгодити дані для створення FileRecord:
        # 1. Схема `FileRecordCreateSchema` повинна включати поля: `storage_path: str`, `file_url: str`, `uploader_user_id: Optional[int]`, `purpose: str`.
        # 2. Поле `purpose` для `FileRecordCreate` потрібно отримати з `FileUploadInitiateRequest` (зберегти upload_id -> purpose десь тимчасово)
        #    або додати `purpose` до схеми `FileUploadCompleteRequest` (що менш імовірно, бо `initiate_data` вже містить `purpose`).
        #    Поточний fallback "UNKNOWN" для purpose є тимчасовим.
        file_record_create_data_dict = {
            "file_name": completion_data.file_name,
            "mime_type": completion_data.mime_type,
            "size_bytes": actual_size,
            "storage_path": str(storage_path_for_record),
            "file_url": file_url_for_record,
            "uploader_user_id": uploader_user_id, # Now int
            "purpose": getattr(completion_data, 'purpose', "UNKNOWN"), # Тимчасовий fallback
            "metadata": getattr(completion_data, 'metadata', None)
        }

        file_record_create_schema_instance = FileRecordCreate(**file_record_create_data_dict)

        try:
            # Використовуємо self.file_record_service
            created_file_record_response = await self.file_record_service.create_file_record(
                record_data=file_record_create_schema_instance
                # uploader_user_id тепер частина record_data і відповідно FileRecordCreateSchema
            )
            if not created_file_record_response: # Додаткова перевірка, якщо create_file_record може повернути None
                 raise ValueError(_("file_upload.errors.complete.file_record_creation_failed_internal"))
        except ValueError as ve:
            logger.error(f"Не вдалося створити запис файлу після завантаження ID '{upload_id}': {ve}", exc_info=True)
            await self.delete_actual_file(str(permanent_file_path))
            raise

        logger.info(
            f"Завантаження ID '{upload_id}' завершено. Створено Запис Файлу ID '{created_file_record_response.id}'.")
        return FileUploadResponse(
            message=_("file_upload.complete.success_message", file_name=created_file_record_response.file_name),
            file_record=created_file_record_response
        )

    async def _async_rmtree(self, directory: Path):
        """Асинхронно видаляє директорію та весь її вміст."""
        logger.debug(f"Асинхронне видалення директорії: {directory}")
        try:
            # Спочатку видаляємо всі файли та піддиректорії
            for item_name in await aiofiles.os.listdir(directory):
                item_path = directory / item_name
                if await aiofiles.os.path.isdir(item_path):
                    await self._async_rmtree(item_path) # Рекурсивний виклик для піддиректорій
                else:
                    await aiofiles.os.remove(item_path) # Видалення файлу
            # Після того, як директорія порожня, видаляємо саму директорію
            await aiofiles.os.rmdir(directory)
            logger.debug(f"Директорію {directory} успішно видалено.")
        except Exception as e:
            logger.error(f"Помилка під час асинхронного видалення директорії {directory}: {e}", exc_info=True)
            # Залежно від стратегії, можна або проковтнути помилку, або підняти її вище
            # raise # Якщо потрібно повідомити про помилку вище

    async def delete_actual_file(self, storage_path: str) -> bool:
        """Видаляє фактичний файл зі сховища."""
        logger.info(f"Спроба видалення фактичного файлу зі сховища: '{storage_path}'")

        abs_file_path: Path
        # Визначаємо, чи шлях абсолютний чи відносний
        if Path(storage_path).is_absolute():
            abs_file_path = Path(storage_path)
        else:  # Якщо відносний, то він відносно permanent_storage_dir
            abs_file_path = (self.permanent_storage_dir / storage_path).resolve()

        # Безпекова перевірка: переконатися, що шлях знаходиться в межах permanent_storage_dir
        if not str(abs_file_path).startswith(str(self.permanent_storage_dir.resolve())):
            logger.error(
                f"Спроба видалення файлу поза визначеною зоною сховища: '{storage_path}' (розв'язано як '{abs_file_path}'). Видалення скасовано.")
            return False

        try:
            if await aiofiles.os.path.isfile(abs_file_path): # Замінено на async версію
                await aiofiles.os.remove(abs_file_path) # Замінено на async версію
                logger.info(f"Локальний файл '{abs_file_path}' успішно видалено.")

                # Спроба видалити батьківську директорію (UUID_SUBDIR), якщо вона порожня
                parent_dir = abs_file_path.parent
                # Переконуємося, що батьківська директорія знаходиться в permanent_storage_dir і не є самою permanent_storage_dir
                if parent_dir != self.permanent_storage_dir and str(parent_dir).startswith(
                        str(self.permanent_storage_dir.resolve())):
                    # Перевірка, чи директорія порожня (aiofiles.os.listdir може бути використано)
                    if not await aiofiles.os.listdir(parent_dir):
                        try:
                            await aiofiles.os.rmdir(parent_dir) # Замінено на async версію
                            logger.info(f"Порожню батьківську директорію '{parent_dir}' видалено.")
                        except OSError as e_rmdir:  # Може бути помилка, якщо директорія не порожня (race condition)
                            logger.warning(
                                f"Не вдалося видалити порожню батьківську директорію '{parent_dir}': {e_rmdir}")
                return True
            else:
                logger.warning(
                    f"Локальний файл не знайдено за шляхом '{abs_file_path}' для видалення (оригінальний шлях: '{storage_path}').")
                return False  # Файл не знайдено, вважаємо операцію неуспішною для видалення
        except Exception as e:
            logger.error(f"Помилка видалення локального файлу '{storage_path}': {e}", exc_info=True)
            return False


logger.debug(f"{FileUploadService.__name__} (сервіс завантаження файлів) успішно визначено.")
