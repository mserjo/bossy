# backend/app/src/services/files/avatar_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `AvatarService` для управління аватарами користувачів.
"""
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from fastapi import UploadFile

from backend.app.src.models.files.avatar import AvatarModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.files.avatar import AvatarCreateSchema, AvatarSchema # UpdateSchema не дуже потрібна
from backend.app.src.repositories.files.avatar import AvatarRepository, avatar_repository
from backend.app.src.services.base import BaseService
from backend.app.src.services.files.file_service import file_service # Для завантаження файлу
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException
from backend.app.src.core.dicts import FileCategoryEnum

class AvatarService(BaseService[AvatarRepository]):
    """
    Сервіс для управління аватарами користувачів.
    """

    async def get_current_avatar_for_user(self, db: AsyncSession, *, user_id: uuid.UUID) -> Optional[AvatarSchema]:
        """
        Отримує поточний аватар користувача.
        Повертає схему AvatarSchema з розгорнутим FileSchema (включаючи file_url).
        """
        avatar_db = await self.repository.get_current_avatar_for_user(db, user_id=user_id)
        if avatar_db:
            # Потрібно завантажити FileModel та сформувати FileSchema з file_url
            if avatar_db.file: # Якщо зв'язок file завантажено
                # file_schema = FileSchema.model_validate(avatar_db.file) # Базове перетворення
                # Тут потрібно додати file_url до FileSchema
                # Це може робити сам FileService.get_file_schema_with_url(file_model)
                # Або ж AvatarSchema має поле file: FileSchema, і FileSchema має file_url

                # Припускаємо, що AvatarSchema.model_validate(avatar_db) коректно обробляє вкладений FileModel
                # і що FileSchema (якщо використовується) генерує file_url.
                # Для простоти, поки що повертаємо модель, а API ендпоінт формує відповідь.
                # Або ж, повертаємо AvatarSchema, яка має FileSchema з file_url.
                # Це залежить від того, як визначена AvatarSchema та FileSchema.
                # Поточна FileSchema має file_url.

                # Потрібен імпорт FileSchema з avatar.py (вже є)
                from backend.app.src.schemas.files.file import FileSchema as ActualFileSchema

                file_schema_with_url = None
                if avatar_db.file:
                    # Формуємо file_url (це має робити FileService або утиліта)
                    # Приклад:
                    # file_url = f"{settings.server.BASE_URL}{settings.file_storage.LOCAL_STORAGE_BASE_URL}/{avatar_db.file.storage_path}"
                    # Поки що не генеруємо URL тут, покладаємося на те, що FileSchema це зробить або API.
                    file_schema_with_url = ActualFileSchema.model_validate(avatar_db.file)
                    # file_schema_with_url.file_url = ... # Встановлюємо URL

                # Створюємо AvatarSchema, передаючи розгорнутий FileSchema
                # Це потребує, щоб AvatarSchema.file мав тип Optional[FileSchema]
                # і щоб FileSchema мала поле file_url.
                # Поточна AvatarSchema має file: Optional[FileSchema]

                # avatar_pydantic = AvatarSchema.model_validate(avatar_db) # Це може не завантажити file_url
                # Краще так:
                return AvatarSchema(
                    id=avatar_db.id,
                    user_id=avatar_db.user_id,
                    file_id=avatar_db.file_id,
                    is_current=avatar_db.is_current,
                    created_at=avatar_db.created_at,
                    updated_at=avatar_db.updated_at,
                    file=file_schema_with_url # Передаємо підготовлену FileSchema
                )
            else: # Малоймовірно, якщо є запис AvatarModel
                self.logger.warning(f"Запис AvatarModel {avatar_db.id} не має пов'язаного файлу.")
        return None


    async def set_user_avatar(
        self, db: AsyncSession, *,
        user_to_update: UserModel, # Користувач, якому встановлюється аватар
        file_to_upload: UploadFile,
        current_user: UserModel # Користувач, який виконує дію (для перевірки прав)
    ) -> AvatarModel:
        """
        Встановлює новий аватар для користувача.
        - Завантажує файл.
        - Створює запис FileModel.
        - Створює запис AvatarModel, позначаючи його як поточний.
        - Деактивує попередній поточний аватар.
        """
        # Перевірка прав: користувач може змінювати свій аватар, або адмін/superuser може змінювати чужий.
        if user_to_update.id != current_user.id and current_user.user_type_code != USER_TYPE_SUPERADMIN:
            # TODO: Додати перевірку, чи є current_user адміном групи, до якої належить user_to_update (якщо потрібно)
            raise ForbiddenException("Ви не маєте прав змінювати аватар цього користувача.")

        # 1. Завантажити файл та створити запис FileModel
        # group_id_context тут не потрібен для аватарів користувачів
        file_meta = await file_service.upload_file(
            db,
            file_to_upload=file_to_upload,
            current_user=user_to_update, # Власником файлу є користувач, якому аватар
            category=FileCategoryEnum.USER_AVATAR,
            is_public=True # Аватари зазвичай публічні
        )

        # 2. Створити запис AvatarModel (використовуємо метод репозиторію, який обробляє is_current)
        # `AvatarRepository.create_avatar_for_user` вже робить деактивацію старих.
        new_avatar_record = await self.repository.create_avatar_for_user(
            db, user_id=user_to_update.id, file_id=file_meta.id
        )

        # TODO: Видалити старий файл аватара зі сховища, якщо він більше не використовується
        #       (якщо це не дефолтний аватар і на нього немає інших посилань AvatarModel).
        #       Це складна логіка, яка потребує підрахунку посилань на FileModel.
        #       Поки що залишаємо старі файли.

        return new_avatar_record

    async def delete_avatar(
        self, db: AsyncSession, *, avatar_id: uuid.UUID, current_user: UserModel
    ) -> Optional[AvatarModel]:
        """
        Видаляє запис AvatarModel.
        Сервіс також має подбати про видалення пов'язаного файлу, якщо він більше не потрібен.
        """
        avatar_to_delete = await self.repository.get(db, id=avatar_id)
        if not avatar_to_delete:
            raise NotFoundException(f"Запис аватара з ID {avatar_id} не знайдено.")

        # Перевірка прав
        if avatar_to_delete.user_id != current_user.id and current_user.user_type_code != USER_TYPE_SUPERADMIN:
            # TODO: Адмін групи?
            raise ForbiddenException("Ви не маєте прав видаляти цей аватар.")

        file_id_to_delete = avatar_to_delete.file_id

        # Видаляємо запис AvatarModel
        deleted_avatar_meta = await self.repository.delete(db, id=avatar_id)

        if deleted_avatar_meta and file_id_to_delete:
            # Перевіряємо, чи файл ще використовується іншими записами AvatarModel
            # (наприклад, якщо це був дефолтний аватар або якщо були помилки і кілька записів посилалися на один файл)
            # Або, якщо це був унікальний аватар, то його можна видаляти.
            # TODO: Реалізувати логіку перевірки використання файлу перед видаленням.
            #       Поки що просто видаляємо файл, якщо вдалося видалити метадані аватара.
            #       Це може бути небезпечно, якщо файл використовується десь ще.
            #       Краще, щоб FileService мав метод "видалити файл, якщо не використовується".
            try:
                self.logger.info(f"Спроба видалити файл {file_id_to_delete} після видалення запису аватара {avatar_id}.")
                # Припускаємо, що current_user має права на видалення файлу, якщо він міг видалити аватар.
                await file_service.delete_file(db, file_id=file_id_to_delete, current_user=current_user)
            except NotFoundException:
                self.logger.warning(f"Файл {file_id_to_delete} для видалення не знайдено (можливо, вже видалено або помилка).")
            except Exception as e:
                self.logger.error(f"Помилка при видаленні файлу {file_id_to_delete} після видалення аватара: {e}")

        return deleted_avatar_meta

    # TODO: Метод для отримання історії аватарів користувача (використовує репозиторій).

avatar_service = AvatarService(avatar_repository)

# TODO: Узгодити логіку генерації `file_url` в `FileSchema` або тут, щоб `get_current_avatar_for_user`
#       повертав повну інформацію, включаючи URL.
#       (Поточна `FileSchema` має поле `file_url`, але воно `Optional` і не заповнюється автоматично).
#
# TODO: Реалізувати більш надійну логіку видалення старих/невикористовуваних файлів аватарів.
#
# Все виглядає як хороший початок для AvatarService.
# Основні операції: встановлення нового аватара (з завантаженням файлу) та отримання поточного.
# Видалення аватара також передбачено.
# Інтеграція з FileService для фізичного управління файлами.
# Перевірка прав.
