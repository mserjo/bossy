# backend/app/src/schemas/groups/group.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `GroupModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні груп.
"""

from pydantic import Field, HttpUrl
from typing import Optional, List, ForwardRef # ForwardRef для циклічних залежностей
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseMainSchema, BaseSchema
# Потрібно буде імпортувати схеми для зв'язків, коли вони будуть готові:
# from backend.app.src.schemas.dictionaries.group_type import GroupTypeSchema
# from backend.app.src.schemas.files.file import FileSchema # Або просто URL для іконки
# from backend.app.src.schemas.groups.settings import GroupSettingsSchema
# from backend.app.src.schemas.groups.membership import GroupMembershipSchema
# from backend.app.src.schemas.tasks.task import TaskSchema
# from backend.app.src.schemas.bonuses.reward import RewardSchema
# from backend.app.src.schemas.bonuses.account import AccountSchema
# from backend.app.src.schemas.groups.poll import PollSchema
# from backend.app.src.schemas.groups.invitation import GroupInvitationSchema

# Використання ForwardRef для уникнення циклічних імпортів з GroupSettingsSchema, GroupMembershipSchema і т.д.
GroupSettingsSchema = ForwardRef('backend.app.src.schemas.groups.settings.GroupSettingsSchema')
GroupMembershipSchema = ForwardRef('backend.app.src.schemas.groups.membership.GroupMembershipSchema')
GroupTypeSchema = ForwardRef('backend.app.src.schemas.dictionaries.group_type.GroupTypeSchema')
TaskSchema = ForwardRef('backend.app.src.schemas.tasks.task.TaskSchema') # Приклад
PollSchema = ForwardRef('backend.app.src.schemas.groups.poll.PollSchema') # Приклад
# ... і так далі для інших зв'язків

# --- Схема для відображення повної інформації про групу (для учасників або адмінів) ---
class GroupSchema(BaseMainSchema):
    """
    Повна схема для представлення групи.
    Успадковує `id, name, description, state_id, group_id (тут NULL), created_at, updated_at, deleted_at, is_deleted, notes`
    від `BaseMainSchema`.
    """
    parent_group_id: Optional[uuid.UUID] = Field(None, description="ID батьківської групи (для ієрархії)")
    group_type_id: Optional[uuid.UUID] = Field(None, description="ID типу групи")
    icon_file_id: Optional[uuid.UUID] = Field(None, description="ID файлу іконки групи")
    # icon_url: Optional[HttpUrl] = Field(None, description="URL іконки групи") # Може генеруватися на основі icon_file_id

    # --- Розгорнуті зв'язки (приклад, потребують відповідних схем та model_rebuild) ---
    # parent_group: Optional['GroupSchema'] = None # Рекурсивний зв'язок
    # child_groups: List['GroupSchema'] = []

    group_type: Optional[GroupTypeSchema] = None
    # settings: Optional[GroupSettingsSchema] = None # Налаштування групи
    # memberships: List[GroupMembershipSchema] = [] # Список учасників та їх ролей

    # tasks: List[TaskSchema] = [] # Завдання в групі (може бути пагінованим окремо)
    # polls: List[PollSchema] = [] # Опитування в групі (може бути пагінованим окремо)

    # `group_id` з `BaseMainSchema` для `GroupModel` завжди буде `None`.

# --- Схема для відображення короткої інформації про групу (наприклад, у списку) ---
class GroupSimpleSchema(BaseMainSchema):
    """
    Спрощена схема для представлення групи (наприклад, у списках).
    """
    parent_group_id: Optional[uuid.UUID] = Field(None, description="ID батьківської групи")
    group_type_id: Optional[uuid.UUID] = Field(None, description="ID типу групи")
    # icon_url: Optional[HttpUrl] = Field(None, description="URL іконки групи")

    # Можна додати кількість учасників, якщо це часто потрібна інформація
    # members_count: Optional[int] = Field(None, description="Кількість учасників у групі")

    # Не включаємо повні списки `memberships`, `tasks` тощо для продуктивності.

# --- Схема для створення нової групи ---
class GroupCreateSchema(BaseSchema):
    """
    Схема для створення нової групи.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Назва групи")
    description: Optional[str] = Field(None, description="Опис групи")

    parent_group_id: Optional[uuid.UUID] = Field(None, description="ID батьківської групи (якщо створюється підгрупа)")
    group_type_id: Optional[uuid.UUID] = Field(None, description="ID типу групи (якщо не дефолтний)")
    # icon_file_id: Optional[uuid.UUID] = Field(None, description="ID файлу іконки (якщо завантажено окремо)")

    # state_id: Optional[uuid.UUID] = Field(None, description="Початковий статус групи (зазвичай 'активна')")
    # notes: Optional[str] = Field(None, description="Додаткові нотатки")

    # Налаштування групи можуть передаватися тут або встановлюватися окремим запитом
    # settings: Optional[GroupSettingsCreateSchema] = None # Потребує GroupSettingsCreateSchema

    # При створенні групи, користувач, що її створює, автоматично стає адміном.
    # Це обробляється на сервісному рівні.

# --- Схема для оновлення існуючої групи ---
class GroupUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючої групи.
    Всі поля опціональні.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)

    parent_group_id: Optional[uuid.UUID] = Field(None) # Зміна батьківської групи - складна операція
    group_type_id: Optional[uuid.UUID] = Field(None)
    icon_file_id: Optional[uuid.UUID] = Field(None)

    state_id: Optional[uuid.UUID] = Field(None) # Зміна статусу (наприклад, архівування)
    notes: Optional[str] = Field(None)
    is_deleted: Optional[bool] = Field(None) # Для "м'якого" видалення

    # Налаштування групи оновлюються окремо через схему GroupSettingsUpdateSchema.


# Необхідно викликати model_rebuild() для схем з ForwardRef після того, як всі вони будуть визначені.
# Це зазвичай робиться в кінці файлу `__init__.py` відповідного пакету схем або глобально.
# Pydantic v2 може автоматично обробляти більшість ForwardRef випадків.
# GroupSchema.model_rebuild() # Приклад

# TODO: Переконатися, що схеми відповідають моделі `GroupModel`.
# `GroupModel` успадковує від `BaseMainModel`.
# `GroupSchema` та `GroupSimpleSchema` успадковують від `BaseMainSchema`.
# Поля: `parent_group_id`, `group_type_id`, `icon_file_id` додані.
# Зв'язки (parent_group, child_groups, group_type, settings, memberships, tasks, polls)
# відображені як опціональні поля з типами ForwardRef або будуть додані пізніше.
# `icon_url` - як приклад похідного поля.
# `members_count` - як приклад агрегованого поля для `GroupSimpleSchema`.
#
# Схеми `Create` та `Update` містять відповідні поля.
# `group_id` з `BaseMainSchema` для `GroupModel` завжди буде `None`.
# Валідація полів (min_length, max_length) додана.
# Все виглядає узгоджено.
#
# Важливо: для рекурсивного зв'язку `parent_group: Optional['GroupSchema']` та `child_groups: List['GroupSchema']`
# потрібно буде викликати `GroupSchema.model_rebuild()` після визначення всіх залежних схем,
# або покладатися на автоматичну обробку ForwardRef в Pydantic v2.
# Поки що залишено з ForwardRef.
#
# Розгортання повних списків (memberships, tasks, polls) в `GroupSchema` може бути надмірним
# для деяких запитів. Ці дані краще отримувати окремими ендпоінтами з пагінацією.
# Тому в `GroupSchema` ці поля можуть бути закоментовані або містити лише ID/кількість.
# Поки що залишено як приклад повного розгортання, але з коментарем.
# `GroupSimpleSchema` є кращим варіантом для списків груп.
# Налаштування групи (`settings`) зазвичай є частиною `GroupSchema`, оскільки це один-до-одного.
# Учасники (`memberships`) також часто потрібні разом з інформацією про групу.
#
# `icon_file_id` - це ID файлу. Потрібен буде механізм для отримання URL цього файлу.
# Це може бути реалізовано через property в моделі або сервісом,
# і потім додано до схеми як `icon_url`.
# Поки що схема містить `icon_file_id`.
#
# Все виглядає добре як початковий набір схем для груп.
