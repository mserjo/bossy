# backend/app/src/schemas/tasks/proposal.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `TaskProposalModel`.
Схеми використовуються для валідації даних при створенні пропозицій завдань,
їх оновленні (наприклад, зміна статусу адміном) та відображенні.
"""

from pydantic import Field
from typing import Optional, List, Any, ForwardRef, Dict # Додано Dict
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.groups.group import GroupSimpleSchema
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.dictionaries.status import StatusSchema
# from backend.app.src.schemas.tasks.task import TaskSimpleSchema

GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema')
UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
StatusSchema = ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema')
TaskSimpleSchema = ForwardRef('backend.app.src.schemas.tasks.task.TaskSimpleSchema')

# --- Схема для відображення інформації про пропозицію завдання (для читання) ---
class TaskProposalSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення пропозиції завдання/події.
    """
    group_id: uuid.UUID = Field(..., description="ID групи, для якої робиться пропозиція")
    proposed_by_user_id: uuid.UUID = Field(..., description="ID користувача, який зробив пропозицію")

    title: str = Field(..., description="Заголовок або коротка назва запропонованого завдання/події")
    description: str = Field(..., description="Детальний опис пропозиції")
    proposed_task_details: Optional[Dict[str, Any]] = Field(None, description="Запропоновані деталі завдання (JSON)")

    status_id: uuid.UUID = Field(..., description="ID статусу пропозиції")
    admin_review_notes: Optional[str] = Field(None, description="Коментарі адміністратора щодо розгляду")
    reviewed_by_user_id: Optional[uuid.UUID] = Field(None, description="ID адміна, який розглянув пропозицію")
    reviewed_at: Optional[datetime] = Field(None, description="Час розгляду пропозиції")

    created_task_id: Optional[uuid.UUID] = Field(None, description="ID завдання/події, створеного на основі цієї пропозиції")
    bonus_for_proposal_awarded: bool = Field(..., description="Чи були нараховані бонуси за вдалу пропозицію")

    # --- Розгорнуті зв'язки (приклад) ---
    # group: Optional[GroupSimpleSchema] = None
    proposer: Optional[UserPublicSchema] = None
    status: Optional[StatusSchema] = None
    reviewer: Optional[UserPublicSchema] = None
    # created_task: Optional[TaskSimpleSchema] = None


# --- Схема для створення нової пропозиції завдання ---
class TaskProposalCreateSchema(BaseSchema):
    """
    Схема для створення нової пропозиції завдання/події.
    """
    # group_id: uuid.UUID # З URL або контексту
    # proposed_by_user_id: uuid.UUID # З поточного користувача

    title: str = Field(..., min_length=1, max_length=255, description="Заголовок пропозиції")
    description: str = Field(..., min_length=1, description="Детальний опис пропозиції")

    # Запропоновані деталі завдання. Клієнт може надіслати структуру,
    # що відповідає частині TaskCreateSchema.
    # Наприклад: {"task_type_id": "uuid", "bonus_points": 10, "due_date": "iso_datetime_str"}
    proposed_task_details: Optional[Dict[str, Any]] = Field(None, description="Словник із запропонованими деталями завдання")

    # status_id встановлюється сервісом (наприклад, "на розгляді").
    # bonus_for_proposal_awarded за замовчуванням False.


# --- Схема для оновлення пропозиції (зазвичай адміном при розгляді) ---
class TaskProposalUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючої пропозиції завдання (наприклад, зміна статусу адміном).
    """
    status_id: uuid.UUID = Field(..., description="Новий ID статусу пропозиції (наприклад, 'прийнято', 'відхилено')")
    admin_review_notes: Optional[str] = Field(None, description="Коментарі адміністратора")
    # reviewed_by_user_id: uuid.UUID # Встановлюється сервісом з поточного адміна
    # reviewed_at: datetime # Встановлюється сервісом

    # Якщо пропозиція прийнята і створено завдання:
    created_task_id: Optional[uuid.UUID] = Field(None, description="ID завдання, створеного на основі пропозиції (якщо статус 'прийнято')")
    bonus_for_proposal_awarded: Optional[bool] = Field(None, description="Чи нараховано бонус за пропозицію")

    # Користувач-автор зазвичай не може редагувати свою пропозицію після подання,
    # або може, якщо вона ще в статусі "чернетка" (якщо такий статус є).
    # title: Optional[str]
    # description: Optional[str]
    # proposed_task_details: Optional[Dict[str, Any]]


# TaskProposalSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `TaskProposalModel`.
# `TaskProposalModel` успадковує від `BaseModel`.
# `TaskProposalSchema` успадковує від `AuditDatesSchema` і додає всі поля пропозиції.
# Розгорнуті зв'язки додані з `ForwardRef`.
#
# `TaskProposalCreateSchema`:
#   - `group_id` та `proposed_by_user_id` очікуються з контексту/сервісу.
#   - `title`, `description` - основні поля від користувача.
#   - `proposed_task_details` (JSON/Dict) для гнучкості запропонованих атрибутів завдання.
#
# `TaskProposalUpdateSchema` використовується адміном для зміни статусу, додавання коментарів,
# зв'язування зі створеним завданням та позначки про нарахування бонусу.
#
# Все виглядає узгоджено.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` - час створення пропозиції.
# `updated_at` - при зміні статусу або інших полів.
#
# `proposed_task_details` дозволяє користувачеві запропонувати різні атрибути для майбутнього завдання,
# такі як тип, бонуси, термін виконання тощо. Сервіс, що обробляє пропозицію,
# буде використовувати ці дані при створенні `TaskModel`.
#
# Важливо, щоб `status_id` в `TaskProposalUpdateSchema` був валідним ID статусу з довідника.
# Аналогічно для `created_task_id` - має бути валідним ID завдання.
# Ці перевірки виконуються на сервісному рівні.
#
# Все виглядає добре.
