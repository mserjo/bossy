# backend/app/src/schemas/tasks/event.py

"""
Pydantic схеми для Подій.
"""

from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import Field

# Абсолютний імпорт базових схем та Enum
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)

from backend.app.src.schemas.base import BaseSchema, BaseMainSchema # BaseMainSchema for response
from backend.app.src.schemas.auth.user import UserPublicProfileSchema
from backend.app.src.schemas.tasks.assignment import TaskAssignmentSchema
from backend.app.src.schemas.tasks.completion import TaskCompletionSchema
# from backend.app.src.core.dicts import EventFrequency # Якщо події мають повторюваність

# --- Локально визначені базові інформаційні схеми для демонстрації ---
# TODO: Замінити на імпорти з відповідних файлів схем, коли вони будуть повністю визначені.
class GroupBasicInfoSchema(BaseSchema):
    """Мінімальна інформація про групу для вкладення в інші схеми."""
    # Assuming these descriptions are for developer reference or very generic UI,
    # otherwise they might need more specific keys if used in diverse contexts.
    # For now, using a generic 'id' and 'name' key if available, or leaving as is if not critical for user display.
    # Let's assume they are for dev/generic for now and don't have specific i18n keys in messages.json for this sub-schema.
    # If they were to be translated, keys like "group.fields.id.description" and "group.fields.name.description" would be used.
    id: int = Field(..., example=1, description="Ідентифікатор групи.") # Not changing for now, as it's a sub-schema.
    name: str = Field(..., example="Відділ маркетингу", description="Назва групи.") # Not changing for now.

# class EventTypeBasicInfoSchema(BaseSchema): # Приклад, якщо події мають власний довідник типів
#     id: int = Field(..., example=2, description="Ідентифікатор типу події.")
#     code: str = Field(..., example="WEBINAR", description="Код типу події.")
#     name: str = Field(..., example="Вебінар", description="Назва типу події.")
# --- Кінець локальних базових інформаційних схем ---


# --- Схеми Подій ---

class EventBaseSchema(BaseSchema):
    """Базова схема для даних події, спільна для операцій створення та оновлення."""
    name: str = Field(..., min_length=3, max_length=255, description=_("event.fields.name.description"), example="Щоквартальна зустріч-огляд")
    description: Optional[str] = Field(None, description=_("event.fields.description.description"), example="Огляд результатів 3-го кварталу та планування на 4-й квартал.")
    # event_type_id: Optional[int] = Field(None, description="ID типу події (наприклад, з dict_event_types або dict_task_types).", example=1)
    start_time: datetime = Field(..., description=_("event.fields.start_time.description"), example=datetime.now(timezone.utc))
    end_time: Optional[datetime] = Field(None, description=_("event.fields.end_time.description"), example=datetime.now(timezone.utc))
    location: Optional[str] = Field(None, max_length=512, description=_("event.fields.location.description"), example="Кімната переговорів / Zoom")
    state: Optional[str] = Field("upcoming", max_length=50, description=_("event.fields.state.description"), example="upcoming")
    notes: Optional[str] = Field(None, description=_("event.fields.notes.description"))
    # Додайте сюди поля повторюваності, якщо події можуть бути повторюваними, аналогічно до TaskBase
    # is_recurring: Optional[bool] = Field(False, description="Чи є подія повторюваною.")
    # recurrence_frequency: Optional[EventFrequency] = Field(None, description="Частота повторення.")
    # recurrence_interval: Optional[int] = Field(None, ge=1, description="Інтервал повторення.")

class EventCreateSchema(EventBaseSchema):
    """
    Схема для створення нової події.
    `group_id` повинен бути наданий, оскільки подія належить групі.
    `created_by_user_id` зазвичай встановлюється сервісом.
    """
    group_id: int = Field(..., description=_("event.create.fields.group_id.description"))
    # name та start_time є обов'язковими з EventBaseSchema.

class EventUpdateSchema(BaseSchema): # Не успадковує EventBaseSchema, щоб зробити всі поля справді опціональними
    """
    Схема для оновлення існуючої події. Всі поля є опціональними для часткових оновлень.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=255, description=_("event.fields.name.description")) # Reusing base
    description: Optional[str] = Field(None, description=_("event.fields.description.description")) # Reusing base
    # event_type_id: Optional[int] = Field(None, description="Новий ID типу події.")
    start_time: Optional[datetime] = Field(None, description=_("event.fields.start_time.description")) # Reusing base
    end_time: Optional[datetime] = Field(None, description=_("event.fields.end_time.description")) # Reusing base
    location: Optional[str] = Field(None, max_length=512, description=_("event.fields.location.description")) # Reusing base
    state: Optional[str] = Field(None, max_length=50, description=_("event.fields.state.description")) # Reusing base
    notes: Optional[str] = Field(None, description=_("event.fields.notes.description")) # Reusing base
    # Оновлення полів повторюваності, якщо вони існують

class EventResponseSchema(BaseMainSchema): # Успадковує id, created_at, updated_at, deleted_at, name, description, state, notes, group_id
    """
    Схема для представлення події у відповідях API.
    Успадковує спільні поля з BaseMainSchema.
    """
    # name, description, state, notes, group_id, id, created_at, updated_at, deleted_at - з BaseMainSchema.
    # Потрібно переконатись, що поля BaseMainSchema відповідають потребам Event.
    # name: str = Field(..., description="Назва події.", example="Вебінар з запуску продукту") # Вже є в BaseMainSchema
    # description: Optional[str] = Field(None, description="Детальний опис події.") # Вже є в BaseMainSchema
    # state: Optional[str] = Field(None, description="Життєвий цикл події (наприклад, 'upcoming', 'past').", example="upcoming") # Вже є в BaseMainSchema

    group: Optional[GroupBasicInfoSchema] = Field(None, description=_("event.response.fields.group.description"))

    # event_type: Optional[EventTypeBasicInfoSchema] = Field(None, description="Інформація про тип події.")

    start_time: datetime = Field(..., description=_("event.fields.start_time.description")) # Reuse
    end_time: Optional[datetime] = Field(None, description=_("event.fields.end_time.description")) # Reuse
    location: Optional[str] = Field(None, description=_("event.fields.location.description"), example="Головна конференц-зала") # Reuse

    created_by_user_id: Optional[int] = Field(None, description=_("event.response.fields.created_by_user_id.description"))
    created_by: Optional[UserPublicProfileSchema] = Field(None, description=_("event.response.fields.created_by.description"))

    assignments: List[TaskAssignmentSchema] = Field(default_factory=list, description=_("event.response.fields.assignments.description"))
    completions: List[TaskCompletionSchema] = Field(default_factory=list, description=_("event.response.fields.completions.description"))

    # Додайте поля повторюваності, якщо застосовно
    # is_recurring: bool = Field(..., description="Чи є подія повторюваною.")
    # recurrence_frequency: Optional[EventFrequency] = Field(None, description="Частота повторення.")
    # recurrence_interval: Optional[int] = Field(None, description="Інтервал повторення.")

    class Config:
        from_attributes = True # Дозволяє мапити з моделі SQLAlchemy
        populate_by_name = True # Дозволяє використовувати аліаси полів
