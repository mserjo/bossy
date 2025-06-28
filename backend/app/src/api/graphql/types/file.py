# backend/app/src/api/graphql/types/file.py
# -*- coding: utf-8 -*-
"""
GraphQL типи, пов'язані з файлами.
"""

import strawberry
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from backend.app.src.api.graphql.types.base import Node, TimestampsInterface

if TYPE_CHECKING:
    from backend.app.src.api.graphql.types.user import UserType # Якщо файл завантажено користувачем

@strawberry.type
class FileRecordType(Node, TimestampsInterface):
    """
    GraphQL тип, що представляє запис про завантажений файл.
    """
    id: strawberry.ID
    filename: str = strawberry.field(description="Оригінальна назва файлу.")
    content_type: Optional[str] = strawberry.field(description="MIME тип файлу.")
    size_bytes: int = strawberry.field(description="Розмір файлу в байтах.")

    url: str = strawberry.field(description="Публічний URL для доступу до файлу.")
    # Або, якщо URL генерується динамічно:
    # @strawberry.field
    # async def url(self, info: strawberry.Info) -> str:
    #     # TODO: Реалізувати генерацію URL на основі ID або шляху
    #     # Потрібен доступ до request.base_url з info.context
    #     pass

    file_type: Optional[str] = strawberry.field(description="Категорія файлу (напр., 'avatar', 'group_icon', 'task_attachment').")
    related_entity_id: Optional[strawberry.ID] = strawberry.field(description="ID пов'язаної сутності (якщо є).")

    uploader: Optional["UserType"] = strawberry.field(description="Користувач, що завантажив файл.")

    created_at: datetime
    updated_at: datetime # Може не змінюватися після створення
    # db_id: strawberry.Private[int]


# Специфічний тип для аватара, якщо він має додаткові поля або логіку
# Або можна просто використовувати FileRecordType з file_type='avatar'
@strawberry.type
class UserAvatarType: # Не успадковує Node, якщо це просто обгортка над URL або FileRecordType
    """GraphQL тип, що представляє аватар користувача."""
    user: "UserType" = strawberry.field(description="Користувач, якому належить аватар.")
    avatar_url: Optional[str] = strawberry.field(description="URL поточного аватара користувача.")
    # Можливо, посилання на FileRecordType, якщо аватари зберігаються як загальні файли
    # file_record: Optional[FileRecordType] = strawberry.field(description="Запис файлу аватара.")
    updated_at: Optional[datetime] = strawberry.field(description="Час останнього оновлення аватара.")


# --- Вхідні типи (Input Types) для мутацій ---
# Для завантаження файлів через GraphQL зазвичай використовується скаляр Upload.
# Мутація буде приймати цей скаляр.

# @strawberry.input
# class FileUploadInput: # Загальний інпут для завантаження
#     file: strawberry.scalars.Upload = strawberry.field(description="Файл для завантаження.")
#     file_type: Optional[str] = strawberry.UNSET # 'group_icon', 'task_attachment'
#     related_entity_id: Optional[strawberry.ID] = strawberry.UNSET


__all__ = [
    "FileRecordType",
    "UserAvatarType",
    # "FileUploadInput",
]
