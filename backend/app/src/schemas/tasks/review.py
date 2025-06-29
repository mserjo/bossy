# backend/app/src/schemas/tasks/review.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `TaskReviewModel`.
Схеми використовуються для валідації даних при створенні, оновленні
(якщо дозволено) та відображенні відгуків та рейтингів на завдання/події.
"""

from pydantic import Field, conint, model_validator
from typing import Optional, List, Any, ForwardRef
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.tasks.task import TaskSimpleSchema
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.dictionaries.status import StatusSchema (якщо є модерація відгуків)

from typing import TYPE_CHECKING # Додано TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.src.schemas.tasks.task import TaskSimpleSchema
    from backend.app.src.schemas.auth.user import UserPublicSchema
    # from backend.app.src.schemas.dictionaries.status import StatusSchema

# TaskSimpleSchema = ForwardRef('backend.app.src.schemas.tasks.task.TaskSimpleSchema') # Перенесено
# UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema') # Перенесено
# StatusSchema = ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema') # Перенесено

# --- Схема для відображення інформації про відгук на завдання (для читання) ---
class TaskReviewSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення відгуку та рейтингу на завдання/подію.
    """
    task_id: uuid.UUID = Field(..., description="ID завдання/події, до якого залишено відгук")
    user_id: uuid.UUID = Field(..., description="ID користувача, який залишив відгук")

    rating: Optional[conint(ge=1, le=5)] = Field(None, description="Рейтинг, виставлений користувачем (від 1 до 5)")
    comment: Optional[str] = Field(None, description="Текстовий коментар відгуку")

    # status_id: Optional[uuid.UUID] = Field(None, description="ID статусу відгуку (якщо є модерація)")

    # --- Розгорнуті зв'язки (приклад) ---
    task: Optional['TaskSimpleSchema'] = Field(None, description="Завдання, до якого залишено відгук") # Рядкове посилання
    user: Optional['UserPublicSchema'] = Field(None, description="Користувач, який залишив відгук") # Рядкове посилання
    # status: Optional['StatusSchema'] = None # Якщо є модерація відгуків


# --- Схема для створення нового відгуку на завдання ---
class TaskReviewCreateSchema(BaseSchema):
    """
    Схема для створення нового відгуку та/або рейтингу на завдання/подію.
    """
    # task_id: uuid.UUID # З URL
    # user_id: uuid.UUID # З поточного користувача

    rating: Optional[conint(ge=1, le=5)] = Field(None, description="Рейтинг (від 1 до 5, опціонально)")
    comment: Optional[str] = Field(None, description="Текстовий коментар (опціонально, але хоча б одне з rating/comment має бути)")

    # status_id: Optional[uuid.UUID] # Встановлюється сервісом (наприклад, "опубліковано" або "на модерації")

    @model_validator(mode='after')
    def check_rating_or_comment_present(cls, data: 'TaskReviewCreateSchema') -> 'TaskReviewCreateSchema':
        if data.rating is None and (data.comment is None or not data.comment.strip()):
            raise ValueError("Має бути наданий або рейтинг, або не порожній коментар.")
        return data

# --- Схема для оновлення існуючого відгуку (якщо дозволено) ---
class TaskReviewUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючого відгуку/рейтингу.
    Дозволяє оновлювати рейтинг та/або коментар.
    """
    rating: Optional[conint(ge=1, le=5)] = Field(None, description="Новий рейтинг (від 1 до 5, опціонально)")
    comment: Optional[str] = Field(None, description="Новий текстовий коментар (опціонально)")

    # status_id: Optional[uuid.UUID] # Якщо адмін змінює статус модерації

    @model_validator(mode='after')
    def check_at_least_one_field_present_for_update(cls, data: 'TaskReviewUpdateSchema') -> 'TaskReviewUpdateSchema':
        # Якщо це PATCH, то хоча б одне поле має бути.
        # Якщо це PUT, то всі поля (або ті, що можна змінювати) мають бути.
        # Для PATCH:
        if all(value is None for value in data.model_dump(exclude_unset=True).values()):
             raise ValueError("Для оновлення потрібно надати хоча б одне поле (rating або comment).")
        # Додатково, якщо оновлюється, то не можна зробити так, щоб і рейтинг, і коментар стали None.
        # Цю логіку краще обробляти на сервісному рівні, маючи доступ до поточного стану об'єкта.
        return data


# TaskReviewSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `TaskReviewModel`.
# `TaskReviewModel` успадковує від `BaseModel`.
# `TaskReviewSchema` успадковує від `AuditDatesSchema` і додає `task_id, user_id, rating, comment`.
# Розгорнуті зв'язки додані з `ForwardRef`.
#
# `TaskReviewCreateSchema`:
#   - `task_id` та `user_id` очікуються з контексту/сервісу.
#   - `rating` та `comment` опціональні, але валідатор перевіряє, що хоча б одне з них надано.
#   - `conint(ge=1, le=5)` для валідації діапазону рейтингу.
#
# `TaskReviewUpdateSchema` дозволяє оновлювати `rating` та `comment`.
# Валідатор перевіряє, що хоча б одне поле надано для оновлення (для PATCH).
#
# Поле `status_id` (для модерації відгуків) закоментоване, оскільки воно
# не було в `TaskReviewModel`. Якщо буде додано, схеми потрібно оновити.
#
# Все виглядає узгоджено.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` - час створення відгуку.
# `updated_at` - якщо відгук редагується (якщо це дозволено).
#
# Можливість редагування/видалення власних відгуків - це питання бізнес-логіки,
# яке буде реалізовано на сервісному рівні та в API ендпоінтах.
# Схеми готові для підтримки цих операцій.
#
# Все виглядає добре.

TaskReviewSchema.model_rebuild()
TaskReviewCreateSchema.model_rebuild()
TaskReviewUpdateSchema.model_rebuild()
