# backend/app/src/api/graphql/mutations/file.py
# -*- coding: utf-8 -*-
"""
GraphQL мутації (Mutations), пов'язані з файлами.
Основна мутація тут - це завантаження файлів.
"""

import strawberry
from typing import Optional

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.file import FileRecordType
# Можливо, специфічні інпути, якщо потрібно передавати метадані разом з файлом
# from backend.app.src.api.graphql.types.file import FileUploadWithMetadataInput

# TODO: Імпортувати сервіси
# from backend.app.src.services.files.file_service import FileService # Загальний сервіс
# from backend.app.src.services.files.avatar_service import AvatarService # Якщо завантаження аватара тут
# from backend.app.src.core.dependencies import get_current_active_user

@strawberry.type
class FileMutations:
    """
    Клас, що групує GraphQL мутації для роботи з файлами.
    """

    @strawberry.mutation(description="Завантажити файл до системи.")
    async def upload_file(
        self,
        info: strawberry.Info,
        file: strawberry.scalars.Upload = strawberry.field(description="Файл для завантаження."),
        file_type: Optional[str] = strawberry.field(default=None, description="Тип файлу (напр., 'group_icon', 'task_attachment', 'reward_image')."),
        related_entity_id: Optional[strawberry.ID] = strawberry.field(default=None, description="ID пов'язаної сутності (якщо є).")
    ) -> Optional[FileRecordType]:
        """
        Завантажує файл та зберігає його в системі.
        Повертає інформацію про збережений файл.
        Права доступу на завантаження та прив'язку до сутності мають перевірятися в сервісі.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова.")
        #
        # # TODO: Валідація типу та розміру файлу (можна в сервісі)
        # # file_content = await file.read()
        # # filename = file.filename
        # # content_type = file.content_type
        #
        # file_service = FileService(context.db_session)
        #
        # entity_db_id = None
        # if related_entity_id is not strawberry.UNSET and related_entity_id is not None:
        #     # Потрібно визначити тип сутності для правильного розкодування ID
        #     # Це може бути складно, якщо related_entity_id може бути різними типами Node.
        #     # Можливо, краще передавати related_entity_type як окремий аргумент.
        #     # Або сервіс приймає GraphQL ID і сам розбирається.
        #     # entity_db_id = Node.decode_id_to_int(related_entity_id, "UnknownTypeYet") # Потрібен тип
        #     pass # Припустимо, сервіс приймає strawberry.ID або обробляє це
        #
        # file_record_model = await file_service.upload_general_file_graphql(
        #     uploaded_file=file, # Передаємо об'єкт Upload напряму
        #     uploader_id=current_user.id,
        #     file_type=file_type,
        #     related_entity_id_str=str(related_entity_id) if related_entity_id else None, # Передаємо як рядок
        #     request_base_url=str(context.request.base_url) # Для генерації URL
        # )
        # return FileRecordType.from_orm(file_record_model) if file_record_model else None
        raise NotImplementedError("Завантаження файлу ще не реалізовано.")

    # Примітка: Мутація для завантаження аватара користувача може бути в UserMutations
    # для кращої логічної організації (uploadMyAvatar).
    # Якщо вона тут, то буде схожа на uploadFile, але з фіксованим file_type='avatar'
    # і related_entity_id буде user_id поточного користувача.

    # @strawberry.mutation(description="Видалити файл.")
    # async def delete_file(self, info: strawberry.Info, file_id: strawberry.ID) -> bool:
    #     """Видаляє файл за його ID. Потрібні відповідні права."""
    #     # ... логіка видалення ...
    #     pass

# Експорт класу для агрегації в mutations/__init__.py
__all__ = [
    "FileMutations",
]
