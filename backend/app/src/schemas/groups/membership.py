# backend/app/src/schemas/groups/membership.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `GroupMembershipModel`.
Схеми використовуються для валідації даних при додаванні/оновленні учасників групи
та відображенні інформації про членство.
"""

from pydantic import Field
from typing import Optional, List, ForwardRef
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema # IdentifiedSchema, TimestampedSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.groups.group import GroupSimpleSchema
# from backend.app.src.schemas.dictionaries.user_role import UserRoleSchema
# from backend.app.src.schemas.dictionaries.status import StatusSchema

UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema')
UserRoleSchema = ForwardRef('backend.app.src.schemas.dictionaries.user_role.UserRoleSchema')
StatusSchema = ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema')


# --- Схема для відображення інформації про членство в групі (для читання) ---
class GroupMembershipSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення членства користувача в групі.
    `created_at` використовується як `joined_at`.
    """
    user_id: uuid.UUID = Field(..., description="ID користувача")
    group_id: uuid.UUID = Field(..., description="ID групи")
    user_role_id: uuid.UUID = Field(..., description="ID ролі користувача в цій групі")

    status_in_group_id: Optional[uuid.UUID] = Field(None, description="ID специфічного статусу користувача в групі")
    notes: Optional[str] = Field(None, description="Нотатки щодо членства")

    # --- Розгорнуті зв'язки (приклад) ---
    user: Optional[UserPublicSchema] = None
    # group: Optional[GroupSimpleSchema] = None # Зазвичай не потрібно, бо ми вже в контексті групи або користувача
    role: Optional[UserRoleSchema] = None
    status_in_group: Optional[StatusSchema] = None

# --- Схема для створення нового запису про членство (наприклад, адміном) ---
class GroupMembershipCreateSchema(BaseSchema):
    """
    Схема для додавання користувача до групи.
    """
    user_id: uuid.UUID = Field(..., description="ID користувача, якого додають до групи")
    # group_id: uuid.UUID # Зазвичай group_id відомий з контексту (ендпоінт /groups/{group_id}/members)
    user_role_id: uuid.UUID = Field(..., description="ID ролі, яка призначається користувачеві в групі")

    status_in_group_id: Optional[uuid.UUID] = Field(None, description="Початковий статус користувача в групі (якщо є)")
    notes: Optional[str] = Field(None, description="Нотатки щодо членства")

# --- Схема для оновлення інформації про членство (наприклад, зміна ролі адміном) ---
class GroupMembershipUpdateSchema(BaseSchema):
    """
    Схема для оновлення ролі або статусу користувача в групі.
    """
    user_role_id: Optional[uuid.UUID] = Field(None, description="Новий ID ролі користувача в групі")
    status_in_group_id: Optional[uuid.UUID] = Field(None, description="Новий ID статусу користувача в групі")
    notes: Optional[str] = Field(None, description="Нові нотатки щодо членства")

    # `user_id` та `group_id` зазвичай не змінюються для існуючого запису членства.
    # Якщо потрібно перевести користувача в іншу групу, це видалення старого членства і створення нового.

# GroupMembershipSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `GroupMembershipModel`.
# `GroupMembershipModel` успадковує від `BaseModel` (id, created_at, updated_at).
# `GroupMembershipSchema` успадковує від `AuditDatesSchema` і додає `user_id, group_id, user_role_id, status_in_group_id, notes`.
# Розгорнуті зв'язки `user`, `role`, `status_in_group` додані з використанням `ForwardRef`.
# Зв'язок `group` закоментований, оскільки зазвичай ця інформація є в контексті запиту.
#
# `GroupMembershipCreateSchema` містить `user_id`, `user_role_id`. `group_id` очікується з URL.
# `GroupMembershipUpdateSchema` дозволяє оновлювати `user_role_id`, `status_in_group_id`, `notes`.
#
# `created_at` з `AuditDatesSchema` використовується як `joined_at`.
# Все виглядає узгоджено.
#
# Важливо: `GroupMembershipCreateSchema` не містить `group_id`, оскільки передбачається,
# що ендпоінт для додавання учасника буде виглядати приблизно так:
# `POST /groups/{group_id}/members`
# і `group_id` буде братися з шляху. Якщо ж буде інший ендпоінт,
# то `group_id` потрібно буде додати до схеми створення.
# Поки що залишаю так.
#
# Для розгорнутих зв'язків (`user`, `role`, `status_in_group`) в `GroupMembershipSchema`
# потрібно буде імпортувати відповідні схеми та викликати `GroupMembershipSchema.model_rebuild()`
# в кінці файлу `__init__.py` пакету `schemas.groups` або глобально,
# щоб Pydantic міг коректно розпізнати типи з `ForwardRef`.
# Pydantic v2 може обробляти це автоматично.
# Все виглядає добре.
