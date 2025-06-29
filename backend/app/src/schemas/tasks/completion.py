# backend/app/src/schemas/tasks/completion.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `TaskCompletionModel`.
Схеми використовуються для валідації даних при фіксації виконання завдань,
оновленні статусу перевірки та відображенні інформації про виконання.
"""

from pydantic import Field, model_validator
from typing import Optional, List, Any, ForwardRef, Dict # Додано Dict
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.tasks.task import TaskSimpleSchema
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.teams.team import TeamSimpleSchema
# from backend.app.src.schemas.dictionaries.status import StatusSchema

from typing import TYPE_CHECKING # Додано TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.src.schemas.tasks.task import TaskSimpleSchema
    from backend.app.src.schemas.auth.user import UserPublicSchema
    from backend.app.src.schemas.teams.team import TeamSimpleSchema
    from backend.app.src.schemas.dictionaries.status import StatusSchema

# TaskSimpleSchema = ForwardRef('backend.app.src.schemas.tasks.task.TaskSimpleSchema') # Перенесено
# UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema') # Перенесено
# TeamSimpleSchema = ForwardRef('backend.app.src.schemas.teams.team.TeamSimpleSchema') # Перенесено
# StatusSchema = ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema') # Перенесено

# --- Схема для відображення інформації про виконання завдання (для читання) ---
class TaskCompletionSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення запису про виконання завдання.
    """
    task_id: uuid.UUID = Field(..., description="ID завдання, яке виконується/виконано")
    user_id: Optional[uuid.UUID] = Field(None, description="ID користувача, який виконав завдання")
    team_id: Optional[uuid.UUID] = Field(None, description="ID команди, яка виконала завдання")

    status_id: uuid.UUID = Field(..., description="ID статусу виконання")

    started_at: Optional[datetime] = Field(None, description="Час, коли завдання взято в роботу")
    submitted_for_review_at: Optional[datetime] = Field(None, description="Час, коли надіслано на перевірку")
    completed_at: Optional[datetime] = Field(None, description="Час підтвердження виконання (або фактичного завершення)")

    reviewed_by_user_id: Optional[uuid.UUID] = Field(None, description="ID адміна, який перевірив виконання")
    reviewed_at: Optional[datetime] = Field(None, description="Час перевірки")
    review_notes: Optional[str] = Field(None, description="Коментарі адміна щодо перевірки")

    bonus_points_awarded: Optional[float] = Field(None, description="Фактично нараховані бонусні бали")
    penalty_points_applied: Optional[float] = Field(None, description="Фактично застосовані штрафні бали")

    completion_notes: Optional[str] = Field(None, description="Коментарі виконавця щодо виконання")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Список метаданих файлів-додатків (JSON)") # Або схема для файлу

    # --- Розгорнуті зв'язки (приклад) ---
    task: Optional['TaskSimpleSchema'] = Field(None, description="Інформація про завдання") # Рядкове посилання
    user: Optional['UserPublicSchema'] = Field(None, description="Інформація про користувача-виконавця") # Рядкове посилання
    team: Optional['TeamSimpleSchema'] = Field(None, description="Інформація про команду-виконавця") # Рядкове посилання
    status: Optional['StatusSchema'] = Field(None, description="Розгорнутий статус виконання") # Рядкове посилання
    reviewer: Optional['UserPublicSchema'] = Field(None, description="Інформація про користувача, який перевірив завдання") # Рядкове посилання


# --- Схема для створення запису про взяття завдання в роботу (початок виконання) ---
class TaskCompletionStartSchema(BaseSchema):
    """
    Схема для фіксації початку виконання завдання користувачем.
    """
    # task_id: uuid.UUID # З URL
    # user_id: uuid.UUID # З поточного користувача
    # team_id: Optional[uuid.UUID] # Якщо завдання командне і береться командою
    # status_id: uuid.UUID # Встановлюється сервісом (наприклад, "в роботі")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Час початку роботи над завданням")
    # completion_notes: Optional[str] # Можливо, нотатки на початку

# --- Схема для подання завдання на перевірку (виконано користувачем) ---
class TaskCompletionSubmitSchema(BaseSchema):
    """
    Схема для подання виконаного завдання на перевірку.
    """
    # task_id: uuid.UUID # З URL
    # user_id: uuid.UUID # З поточного користувача (або визначається з існуючого TaskCompletion запису)
    # team_id: Optional[uuid.UUID]
    # status_id: uuid.UUID # Встановлюється сервісом (наприклад, "на перевірці")
    submitted_for_review_at: datetime = Field(default_factory=datetime.utcnow, description="Час подання на перевірку")
    completion_notes: Optional[str] = Field(None, description="Коментарі виконавця щодо виконання")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Список файлів-додатків (наприклад, [{ 'file_id': 'uuid', 'filename': 'doc.pdf' }])")
    # TODO: Визначити схему для елемента `attachments`, якщо потрібно валідувати структуру.

# --- Схема для перевірки завдання адміністратором ---
class TaskCompletionReviewSchema(BaseSchema):
    """
    Схема для перевірки завдання адміністратором.
    """
    # task_id, user_id/team_id - з URL або існуючого запису TaskCompletion
    new_status_id: uuid.UUID = Field(..., description="Новий ID статусу завдання (наприклад, 'підтверджено', 'відхилено')")
    # reviewed_by_user_id: uuid.UUID # З поточного користувача (адміна)
    reviewed_at: datetime = Field(default_factory=datetime.utcnow, description="Час перевірки")
    review_notes: Optional[str] = Field(None, description="Коментарі адміна (обов'язково, якщо відхилено)")

    bonus_points_awarded: Optional[float] = Field(None, description="Фактично нараховані бонуси (якщо відрізняються від планових)")
    penalty_points_applied: Optional[float] = Field(None, description="Фактично застосовані штрафи (якщо є)")

    @model_validator(mode='after')
    def check_review_notes_if_rejected(cls, data: 'TaskCompletionReviewSchema') -> 'TaskCompletionReviewSchema':
        # Потрібен доступ до коду статусу "відхилено".
        # Припустимо, що сервіс передасть код статусу або перевірить це.
        # Або ж, якщо `new_status_id` відповідає статусу "відхилено", то `review_notes` має бути.
        # Цю логіку краще реалізувати на сервісному рівні, де є доступ до довідника статусів.
        # if data.new_status_code == "REJECTED" and not data.review_notes: # Приклад, якщо є new_status_code
        #     raise ValueError("Коментар (review_notes) є обов'язковим при відхиленні завдання.")
        return data

# TaskCompletionSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `TaskCompletionModel`.
# `TaskCompletionModel` успадковує від `BaseModel`.
# `TaskCompletionSchema` успадковує від `AuditDatesSchema` і додає всі поля виконання.
# Розгорнуті зв'язки додані з `ForwardRef`.
#
# Схеми для різних етапів життєвого циклу виконання:
# - `TaskCompletionStartSchema`: для дії "взяти в роботу".
# - `TaskCompletionSubmitSchema`: для дії "виконано" (надіслати на перевірку).
# - `TaskCompletionReviewSchema`: для дій адміна "підтвердити", "відхилити".
#
# Поля `task_id`, `user_id`, `team_id`, `status_id` в цих схемах (Create/Update типу)
# зазвичай встановлюються сервісом або беруться з контексту запиту (URL, поточний користувач).
# Тому вони можуть бути закоментовані в схемах запиту.
#
# `attachments` як `List[Dict[str, Any]]` - це гнучко, але можна визначити більш строгу схему для елемента списку.
# `float` для `Numeric` полів (бонуси/штрафи).
# Все виглядає узгоджено.
#
# Валідатор `check_review_notes_if_rejected` в `TaskCompletionReviewSchema` потребує
# доступу до кодів статусів, тому його краще реалізувати на сервісному рівні.
# Поки що залишено як приклад.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` - час створення запису про виконання.
# `updated_at` - при зміні статусу, додаванні коментарів тощо.
# Все виглядає добре.

TaskCompletionSchema.model_rebuild()
TaskCompletionStartSchema.model_rebuild()
TaskCompletionSubmitSchema.model_rebuild()
TaskCompletionReviewSchema.model_rebuild()
