# backend/app/src/schemas/tasks/event.py

"""
Pydantic схеми для Подій.
"""

from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import Field

# Абсолютний імпорт базових схем та Enum
from backend.app.src.config.logging import get_logger
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
    id: int = Field(..., example=1, description="Ідентифікатор групи.")
    name: str = Field(..., example="Відділ маркетингу", description="Назва групи.")

# class EventTypeBasicInfoSchema(BaseSchema): # Приклад, якщо події мають власний довідник типів
#     id: int = Field(..., example=2, description="Ідентифікатор типу події.")
#     code: str = Field(..., example="WEBINAR", description="Код типу події.")
#     name: str = Field(..., example="Вебінар", description="Назва типу події.")
# --- Кінець локальних базових інформаційних схем ---


# --- Схеми Подій ---

class EventBaseSchema(BaseSchema):
    """Базова схема для даних події, спільна для операцій створення та оновлення."""
    name: str = Field(..., min_length=3, max_length=255, description="Назва або заголовок події.", example="Щоквартальна зустріч-огляд")
    description: Optional[str] = Field(None, description="Детальний опис події.", example="Огляд результатів 3-го кварталу та планування на 4-й квартал.")
    # event_type_id: Optional[int] = Field(None, description="ID типу події (наприклад, з dict_event_types або dict_task_types).", example=1)
    start_time: datetime = Field(..., description="Дата та час початку події (UTC).", example=datetime.now(timezone.utc)) # Removed timedelta for simplicity here
    end_time: Optional[datetime] = Field(None, description="Необов'язкові дата та час закінчення події (UTC).", example=datetime.now(timezone.utc)) # Removed timedelta
    location: Optional[str] = Field(None, max_length=512, description="Фізичне або віртуальне місцезнаходження події.", example="Кімната переговорів / Zoom")
    state: Optional[str] = Field("upcoming", max_length=50, description="Стан події (наприклад, 'upcoming', 'ongoing', 'past', 'cancelled').", example="upcoming") # З BaseMainModel
    notes: Optional[str] = Field(None, description="Внутрішні нотатки для події.") # З BaseMainModel
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
    group_id: int = Field(..., description="Ідентифікатор групи, до якої належить ця подія.")
    # name та start_time є обов'язковими з EventBaseSchema.

class EventUpdateSchema(BaseSchema): # Не успадковує EventBaseSchema, щоб зробити всі поля справді опціональними
    """
    Схема для оновлення існуючої події. Всі поля є опціональними для часткових оновлень.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=255, description="Нова назва або заголовок події.")
    description: Optional[str] = Field(None, description="Новий детальний опис події.")
    # event_type_id: Optional[int] = Field(None, description="Новий ID типу події.")
    start_time: Optional[datetime] = Field(None, description="Нові дата та час початку події (UTC).")
    end_time: Optional[datetime] = Field(None, description="Нові дата та час закінчення події (UTC).")
    location: Optional[str] = Field(None, max_length=512, description="Нове фізичне або віртуальне місцезнаходження події.")
    state: Optional[str] = Field(None, max_length=50, description="Новий стан події.")
    notes: Optional[str] = Field(None, description="Оновлені внутрішні нотатки для події.")
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

    # TODO: Замінити локальну GroupBasicInfoSchema на імпортовану з backend.app.src.schemas.groups.group
    group: Optional[GroupBasicInfoSchema] = Field(None, description="Базова інформація про групу, до якої належить ця подія.") # Заповнюється сервісом

    # event_type: Optional[EventTypeBasicInfoSchema] = Field(None, description="Інформація про тип події.") # Заповнюється сервісом

    start_time: datetime = Field(..., description="Дата та час початку події.")
    end_time: Optional[datetime] = Field(None, description="Дата та час закінчення події.")
    location: Optional[str] = Field(None, description="Місцезнаходження події.", example="Головна конференц-зала")

    created_by_user_id: Optional[int] = Field(None, description="ID користувача, який створив подію.")
    created_by: Optional[UserPublicProfileSchema] = Field(None, description="Профіль користувача, який створив подію.")

    assignments: List[TaskAssignmentSchema] = Field(default_factory=list, description="Список призначень, пов'язаних з подією.")
    completions: List[TaskCompletionSchema] = Field(default_factory=list, description="Список виконань, пов'язаних з подією.")

    # Додайте поля повторюваності, якщо застосовно
    # is_recurring: bool = Field(..., description="Чи є подія повторюваною.")
    # recurrence_frequency: Optional[EventFrequency] = Field(None, description="Частота повторення.")
    # recurrence_interval: Optional[int] = Field(None, description="Інтервал повторення.")

    class Config:
        from_attributes = True # Дозволяє мапити з моделі SQLAlchemy
        populate_by_name = True # Дозволяє використовувати аліаси полів
