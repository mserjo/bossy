# backend/app/src/schemas/teams/team.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `TeamModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні команд.
"""

from pydantic import Field, HttpUrl
from typing import Optional, List, ForwardRef
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseMainSchema, BaseSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.groups.group import GroupSimpleSchema (group_id вже є)
# from backend.app.src.schemas.files.file import FileSchema (або URL іконки)
# from backend.app.src.schemas.teams.membership import TeamMembershipSchema
# from backend.app.src.schemas.tasks.task import TaskSimpleSchema (для tasks_assigned)

UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
TeamMembershipSchema = ForwardRef('backend.app.src.schemas.teams.membership.TeamMembershipSchema')
TaskSimpleSchema = ForwardRef('backend.app.src.schemas.tasks.task.TaskSimpleSchema') # Приклад

# --- Схема для відображення повної інформації про команду ---
class TeamSchema(BaseMainSchema):
    """
    Повна схема для представлення команди.
    Успадковує `id, name, description, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes`
    від `BaseMainSchema`.
    """
    # `group_id` з BaseMainSchema - ID групи, до якої належить команда.

    leader_user_id: Optional[uuid.UUID] = Field(None, description="ID користувача-лідера (капітана) команди")
    icon_file_id: Optional[uuid.UUID] = Field(None, description="ID файлу іконки команди")
    # icon_url: Optional[HttpUrl] = Field(None, description="URL іконки команди") # Може генеруватися

    max_members: Optional[int] = Field(None, ge=1, description="Максимальна кількість учасників у команді (NULL - без обмежень)")

    # --- Розгорнуті зв'язки (приклад) ---
    leader: Optional[UserPublicSchema] = None
    # group: Optional[GroupSimpleSchema] = None # `group_id` вже є
    # state: Optional[StatusSchema] = None # `state_id` вже є

    memberships: List[TeamMembershipSchema] = Field(default_factory=list, description="Список учасників команди та їх ролей (якщо є)")
    # tasks_assigned: List[TaskSimpleSchema] = [] # Завдання, призначені цій команді (зазвичай отримуються окремо)

    # Додаткове поле для зручності: кількість учасників
    members_count: Optional[int] = Field(None, description="Поточна кількість учасників у команді (обчислюване поле)")


# --- Схема для відображення короткої інформації про команду (наприклад, у списку) ---
class TeamSimpleSchema(BaseMainSchema):
    """
    Спрощена схема для представлення команди.
    """
    leader_user_id: Optional[uuid.UUID] = Field(None, description="ID лідера команди")
    # icon_url: Optional[HttpUrl] = Field(None, description="URL іконки команди")
    max_members: Optional[int] = Field(None, ge=1)
    members_count: Optional[int] = Field(None, description="Кількість учасників")

    # Не включаємо повні списки `memberships`, `tasks_assigned`.


# --- Схема для створення нової команди ---
class TeamCreateSchema(BaseSchema):
    """
    Схема для створення нової команди.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Назва команди")
    description: Optional[str] = Field(None, description="Опис команди")
    # group_id: uuid.UUID # З URL або контексту

    leader_user_id: Optional[uuid.UUID] = Field(None, description="ID користувача, який буде лідером команди (має бути членом групи)")
    # icon_file_id: Optional[uuid.UUID] = Field(None, description="ID файлу іконки (якщо завантажено окремо)")
    max_members: Optional[int] = Field(None, ge=1, description="Максимальна кількість учасників")

    state_id: Optional[uuid.UUID] = Field(None, description="Початковий статус команди (зазвичай 'активна')")
    notes: Optional[str] = Field(None, description="Додаткові нотатки")

    # При створенні команди, лідер (якщо вказаний) автоматично додається до учасників.
    # Це обробляється на сервісному рівні.


# --- Схема для оновлення існуючої команди ---
class TeamUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючої команди.
    Всі поля опціональні.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)

    leader_user_id: Optional[uuid.UUID] = Field(None) # Зміна лідера
    icon_file_id: Optional[uuid.UUID] = Field(None)
    max_members: Optional[int] = Field(None, ge=1) # Дозволяємо NULL для зняття обмеження

    state_id: Optional[uuid.UUID] = Field(None) # Зміна статусу (наприклад, розформування)
    notes: Optional[str] = Field(None)
    is_deleted: Optional[bool] = Field(None) # Для "м'якого" видалення

# TeamSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `TeamModel`.
# `TeamModel` успадковує від `BaseMainModel`.
# `TeamSchema` та `TeamSimpleSchema` успадковують від `BaseMainSchema`.
# Поля: `leader_user_id`, `icon_file_id`, `max_members` додані.
# Зв'язки (leader, memberships, tasks_assigned) відображені з `ForwardRef`.
# `icon_url` та `members_count` - як приклади похідних/агрегованих полів.
#
# Схеми `Create` та `Update` містять відповідні поля.
# `group_id` з `BaseMainSchema` для `TeamModel` має бути NOT NULL (забезпечується логікою сервісу).
#
# Важливо: `leader_user_id` в `TeamCreateSchema` - користувач має бути учасником групи.
# Призначення лідера також має створювати запис в `TeamMembershipModel` для цього лідера.
#
# `tasks_assigned` в `TeamSchema` закоментовано, оскільки це зазвичай окремий запит.
# `members_count` в `TeamSchema` може бути корисним, якщо обчислюється сервісом.
#
# Все виглядає узгоджено.
# `AuditDatesSchema` (через `BaseMainSchema`) надає `id, created_at, updated_at`.
# `deleted_at`, `is_deleted`, `notes` також успадковані.
# `name` та `description` з `BaseMainSchema` використовуються для назви та опису команди.
# `state_id` для статусу команди.
# `group_id` для прив'язки до групи.
# Все виглядає добре.
