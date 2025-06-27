# backend/app/src/services/files/file_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `FileService` для управління файлами та їх метаданими.
Включає логіку завантаження, отримання, видалення файлів та їх метаданих.
"""
from typing import List, Optional, IO, Tuple, AsyncGenerator
import uuid
import os
import shutil # Для операцій з файлами/каталогами
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from fastapi import UploadFile, HTTPException

from backend.app.src.models.files.file import FileModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.files.file import FileCreateSchema, FileUpdateSchema, FileSchema
from backend.app.src.repositories.files.file import FileRepository, file_repository
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.config.settings import settings # Для шляхів зберігання
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN
from backend.app.src.core.dicts import FileCategoryEnum # Для роботи з категоріями

class FileService(BaseService[FileRepository]):
    """
    Сервіс для управління файлами.
    """

    def _get_storage_path(self) -> Path:
        """Повертає базовий шлях до локального сховища файлів."""
        base_path_str = settings.file_storage.LOCAL_STORAGE_BASE_PATH
        # Переконуємося, що шлях абсолютний або відносно кореня проекту
        base_path = Path(base_path_str)
        if not base_path.is_absolute():
            base_path = settings.app.BASE_DIR / base_path
        return base_path

    def _ensure_storage_dir_exists(self, file_path: Path) -> None:
        """Переконується, що каталог для збереження файлу існує."""
        directory = file_path.parent
        if not directory.exists():
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Створено каталог для файлів: {directory}")
            except OSError as e:
                self.logger.error(f"Не вдалося створити каталог '{directory}': {e}")
                raise HTTPException(status_code=500, detail=f"Помилка сервера при створенні каталогу для файлу: {e}")


    async def _save_local_file(self, file: UploadFile, sub_path: str, filename: str) -> Tuple[Path, str]:
        """
        Зберігає завантажений файл локально.
        Повертає повний шлях до збереженого файлу та відносний шлях для БД.
        """
        base_storage_path = self._get_storage_path()
        # Створюємо унікальний підкаталог для файлу (наприклад, на основі перших символів UUID або дати)
        # або використовуємо переданий sub_path.
        # Для простоти, поки що sub_path може бути категорією або user_id.
        # filename має бути унікальним або санітизованим.

        # Генеруємо унікальне ім'я файлу, щоб уникнути колізій, зберігаючи розширення.
        original_filename_stem, original_filename_ext = os.path.splitext(filename)
        unique_filename = f"{uuid.uuid4()}{original_filename_ext}"

        relative_file_path = Path(sub_path) / unique_filename
        full_file_path = base_storage_path / relative_file_path

        self._ensure_storage_dir_exists(full_file_path)

        try:
            with open(full_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            self.logger.error(f"Помилка збереження файлу '{full_file_path}': {e}")
            # TODO: Видалити частково збережений файл, якщо помилка
            raise HTTPException(status_code=500, detail=f"Помилка сервера при збереженні файлу: {e}")
        finally:
            await file.close() # Завжди закриваємо файл

        return full_file_path, str(relative_file_path) # Повертаємо відносний шлях для storage_path

    async def upload_file(
        self, db: AsyncSession, *,
        file_to_upload: UploadFile,
        current_user: UserModel,
        category: FileCategoryEnum, # Категорія файлу
        group_id_context: Optional[uuid.UUID] = None, # Якщо файл стосується групи
        is_public: bool = False,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> FileModel:
        """
        Обробляє завантаження файлу: зберігає файл, створює запис метаданих.
        """
        if not file_to_upload.filename:
            raise BadRequestException("Ім'я файлу не може бути порожнім.")

        # Визначаємо підшлях для збереження на основі категорії та, можливо, ID користувача/групи
        # Наприклад: "avatars/user_uuid/", "task_attachments/task_uuid/"
        # Поки що просто категорія як підшлях.
        sub_path_for_storage = category.value.lower()
        if category == FileCategoryEnum.USER_AVATAR:
            sub_path_for_storage = f"avatars/{current_user.id}"
        elif category == FileCategoryEnum.GROUP_ICON and group_id_context:
            sub_path_for_storage = f"group_icons/{group_id_context}"
        # TODO: Додати логіку для інших категорій

        # Зберігаємо файл фізично
        # `_save_local_file` повертає (повний_локальний_шлях, відносний_шлях_для_БД)
        _full_local_path, storage_path_for_db = await self._save_local_file(
            file=file_to_upload,
            sub_path=sub_path_for_storage,
            filename=file_to_upload.filename
        )

        # Отримуємо розмір файлу
        file_size = os.path.getsize(_full_local_path)

        # TODO: Визначення MIME-типу може бути уточнено (наприклад, з `file.content_type` або бібліотекою `python-magic`)
        mime_type = file_to_upload.content_type or "application/octet-stream"

        # Створюємо запис метаданих в БД
        file_create_schema = FileCreateSchema(
            storage_path=storage_path_for_db,
            original_filename=file_to_upload.filename,
            mime_type=mime_type,
            file_size_bytes=file_size,
            uploaded_by_user_id=current_user.id,
            group_context_id=group_id_context,
            file_category_code=category.value,
            metadata=custom_metadata,
            is_public=is_public
        )
        return await self.repository.create(db, obj_in=file_create_schema)

    async def get_file_by_id(self, db: AsyncSession, file_id: uuid.UUID, current_user: Optional[UserModel] = None) -> FileModel:
        file_meta = await self.repository.get(db, id=file_id)
        if not file_meta:
            raise NotFoundException(f"Файл з ID {file_id} не знайдено.")

        # TODO: Перевірка прав доступу до файлу, якщо він не публічний.
        # if not file_meta.is_public and current_user:
        #     # Логіка перевірки, чи має current_user доступ (наприклад, він власник, або це в контексті його групи/завдання)
        #     can_access = False
        #     if file_meta.uploaded_by_user_id == current_user.id: can_access = True
        #     # ... інші перевірки ...
        #     if not can_access:
        #         raise ForbiddenException("Ви не маєте доступу до цього файлу.")
        # elif not file_meta.is_public and not current_user: # Анонімний доступ до непублічного файлу
        #      raise ForbiddenException("Доступ до цього файлу заборонено.")

        return file_meta

    async def delete_file(self, db: AsyncSession, *, file_id: uuid.UUID, current_user: UserModel) -> FileModel:
        """
        Видаляє метадані файлу та сам файл зі сховища.
        """
        file_meta = await self.get_file_by_id(db, file_id=file_id) # Перевірка існування

        # Перевірка прав на видалення
        can_delete = False
        if current_user.user_type_code == USER_TYPE_SUPERADMIN:
            can_delete = True
        elif file_meta.uploaded_by_user_id == current_user.id:
            can_delete = True
        # TODO: Додати перевірку, чи є користувач адміном групи, якщо файл належить групі.
        # from backend.app.src.services.groups.group_membership_service import group_membership_service
        # if file_meta.group_context_id and await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=file_meta.group_context_id):
        #    can_delete = True

        if not can_delete:
            raise ForbiddenException("Ви не маєте прав видаляти цей файл.")

        # Фізичне видалення файлу
        base_storage_path = self._get_storage_path()
        full_file_path_to_delete = base_storage_path / file_meta.storage_path
        try:
            if full_file_path_to_delete.is_file():
                full_file_path_to_delete.unlink()
                self.logger.info(f"Файл '{full_file_path_to_delete}' успішно видалено зі сховища.")
                # TODO: Видалити порожні батьківські каталоги, якщо потрібно.
            else:
                self.logger.warning(f"Файл '{full_file_path_to_delete}' для видалення не знайдено у сховищі.")
        except Exception as e:
            self.logger.error(f"Помилка при фізичному видаленні файлу '{full_file_path_to_delete}': {e}")
            # Вирішити, чи продовжувати видалення метаданих, якщо файл не вдалося видалити.
            # Поки що продовжуємо, але з логуванням помилки.

        # Видалення метаданих з БД
        deleted_meta = await self.repository.delete(db, id=file_id)
        if not deleted_meta: # Малоймовірно, якщо get_file_by_id спрацював
            raise NotFoundException(f"Не вдалося видалити метадані файлу {file_id} (можливо, вже видалено).")
        return deleted_meta # Повертаємо метадані видаленого файлу


    async def get_file_stream(self, db: AsyncSession, file_id: uuid.UUID, current_user: Optional[UserModel] = None) -> Tuple[Path, str, str]: # type: ignore
        """
        Отримує потік даних файлу для віддачі клієнту.
        Повертає шлях до файлу, його original_filename та mime_type.
        """
        file_meta = await self.get_file_by_id(db, file_id=file_id, current_user=current_user) # Перевірка прав всередині

        base_storage_path = self._get_storage_path()
        full_file_path = base_storage_path / file_meta.storage_path

        if not full_file_path.is_file():
            self.logger.error(f"Файл не знайдено у сховищі за шляхом: {full_file_path} (запис ID: {file_id})")
            raise NotFoundException("Файл не знайдено у сховищі.")

        return full_file_path, file_meta.original_filename, file_meta.mime_type

    # TODO: Додати методи для оновлення метаданих файлу (FileUpdateSchema).
    # async def update_file_meta(self, db: AsyncSession, *, file_id: uuid.UUID, obj_in: FileUpdateSchema, current_user: UserModel) -> FileModel: ...

file_service = FileService(file_repository)

# TODO: Реалізувати логіку для інших типів сховищ (S3, Google Cloud Storage), якщо FILE_STORAGE_TYPE != "local".
#       Це потребуватиме окремих методів _save_s3_file, _delete_s3_file тощо,
#       та відповідних налаштувань в settings.py.
#
# TODO: Додати більш надійне визначення MIME-типу (наприклад, бібліотека python-magic).
#
# TODO: Реалізувати логіку видалення порожніх каталогів після видалення останнього файлу з них.
#
# TODO: Узгодити логіку прав доступу в `get_file_by_id` та `get_file_stream`.
#
# Все виглядає як хороший початок для FileService.
# Основні операції: завантаження (збереження + метадані), отримання, видалення.
# Важливою є обробка шляхів, перевірка прав та фізичне управління файлами.
