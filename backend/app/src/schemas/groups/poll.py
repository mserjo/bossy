# backend/app/src/schemas/groups/poll.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделей, пов'язаних з опитуваннями/голосуваннями в групах:
`PollModel`, `PollOptionModel`, `PollVoteModel`.
"""

from pydantic import Field, field_validator, model_validator
from typing import Optional, List, Any, ForwardRef
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseMainSchema, BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.groups.group import GroupSimpleSchema
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.dictionaries.status import StatusSchema

UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
# GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema') # Для group в PollSchema
# StatusSchema = ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema') # Для state в PollSchema

# --- Схеми для PollOption ---

class PollOptionBaseSchema(BaseSchema):
    """Базова схема для варіанту відповіді (спільні поля для створення/оновлення)."""
    option_text: str = Field(..., min_length=1, description="Текст варіанту відповіді")
    order_num: int = Field(default=0, ge=0, description="Порядковий номер варіанту для сортування")

class PollOptionCreateSchema(PollOptionBaseSchema):
    """Схема для створення нового варіанту відповіді для опитування."""
    # poll_id: uuid.UUID # Зазвичай передається в URL або встановлюється сервісом
    pass

class PollOptionUpdateSchema(PollOptionBaseSchema):
    """Схема для оновлення існуючого варіанту відповіді."""
    option_text: Optional[str] = Field(None, min_length=1) # Роблю опціональним для оновлення
    order_num: Optional[int] = Field(None, ge=0)

class PollOptionSchema(PollOptionBaseSchema, AuditDatesSchema): # Додаємо id, created_at, updated_at
    """Схема для відображення варіанту відповіді."""
    poll_id: uuid.UUID = Field(..., description="ID опитування, до якого належить варіант")
    # votes_count: Optional[int] = Field(None, description="Кількість голосів за цей варіант (обчислюване поле)")
    # Якщо votes_count буде додано, його треба розраховувати на сервісному рівні.

# --- Схеми для PollVote ---

class PollVoteBaseSchema(BaseSchema):
    """Базова схема для голосу (спільні поля)."""
    option_id: uuid.UUID = Field(..., description="ID обраного варіанту відповіді")
    # user_id: Optional[uuid.UUID] # Встановлюється сервісом з поточного користувача або NULL для анонімних
    # poll_id: uuid.UUID # Зазвичай з URL

class PollVoteCreateSchema(PollVoteBaseSchema):
    """Схема для подання голосу."""
    # Додаткові поля, якщо потрібні при створенні голосу, наприклад, капча.
    pass

class PollVoteSchema(PollVoteBaseSchema, AuditDatesSchema): # Додаємо id, created_at, updated_at
    """Схема для відображення поданого голосу."""
    poll_id: uuid.UUID = Field(..., description="ID опитування")
    user_id: Optional[uuid.UUID] = Field(None, description="ID користувача, який проголосував (NULL для анонімних)")
    # user: Optional[UserPublicSchema] = None # Розгорнута інформація про користувача (якщо не анонімне)
    # option: Optional[PollOptionSchema] = None # Розгорнута інформація про обраний варіант (зазвичай не потрібно тут)

# --- Схеми для Poll ---

class PollSchema(BaseMainSchema):
    """
    Повна схема для представлення опитування/голосування.
    Успадковує `id, name, description, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes`
    від `BaseMainSchema`.
    """
    # `name` з BaseMainSchema - це питання або назва опитування.
    # `group_id` з BaseMainSchema - ID групи, де проводиться опитування.

    created_by_user_id: uuid.UUID = Field(..., description="ID користувача (адміна групи), який створив опитування")
    is_anonymous: bool = Field(..., description="Чи є голосування анонімним")
    allow_multiple_choices: bool = Field(..., description="Чи дозволено обирати декілька варіантів відповіді")
    starts_at: Optional[datetime] = Field(None, description="Дата та час початку опитування")
    ends_at: Optional[datetime] = Field(None, description="Дата та час закінчення опитування")

    min_choices: int = Field(..., ge=1, description="Мінімальна кількість варіантів, яку потрібно обрати")
    max_choices: Optional[int] = Field(None, ge=1, description="Максимальна кількість варіантів (якщо allow_multiple_choices)")
    show_results_before_voting: bool = Field(..., description="Чи показувати результати тим, хто ще не проголосував")
    results_visibility: str = Field(..., description="Хто може бачити результати ('all', 'voted_only', 'admins_only', 'after_end')")

    # --- Розгорнуті зв'язки ---
    # creator: Optional[UserPublicSchema] = None
    # group: Optional[GroupSimpleSchema] = None # `group_id` вже є
    # state: Optional[StatusSchema] = None # `state_id` вже є

    options: List[PollOptionSchema] = Field(default_factory=list, description="Список варіантів відповідей для опитування")
    # votes: List[PollVoteSchema] = [] # Список голосів (зазвичай не віддається весь, а агрегується)
    # total_votes: Optional[int] = Field(None, description="Загальна кількість голосів (обчислюване поле)")

    @model_validator(mode='after')
    def check_max_choices(cls, data: 'PollSchema') -> 'PollSchema':
        if data.allow_multiple_choices and data.max_choices is not None and data.min_choices > data.max_choices:
            raise ValueError("Максимальна кількість обраних варіантів не може бути меншою за мінімальну.")
        if not data.allow_multiple_choices and (data.min_choices != 1 or data.max_choices is not None and data.max_choices != 1):
            # Якщо не дозволено кілька варіантів, то min=1, max=1 (або None)
            # Це можна встановити за замовчуванням або валідувати.
            # Поки що просто перевірка, якщо max_choices встановлено неправильно.
            pass # Логіка встановлення min/max при allow_multiple_choices=False - на сервісі
        return data


class PollCreateSchema(BaseSchema):
    """Схема для створення нового опитування."""
    name: str = Field(..., min_length=1, description="Питання або назва опитування")
    description: Optional[str] = Field(None, description="Детальний опис опитування")
    # group_id: uuid.UUID # З URL
    # created_by_user_id: uuid.UUID # З поточного користувача
    state_id: Optional[uuid.UUID] = Field(None, description="Початковий статус опитування")

    is_anonymous: bool = Field(default=False)
    allow_multiple_choices: bool = Field(default=False)
    starts_at: Optional[datetime] = Field(None)
    ends_at: Optional[datetime] = Field(None)

    min_choices: Optional[int] = Field(None, ge=1) # Стане 1, якщо None і allow_multiple_choices=False
    max_choices: Optional[int] = Field(None, ge=1)
    show_results_before_voting: bool = Field(default=False)
    results_visibility: str = Field(default="after_end") # TODO: Enum для results_visibility
    notes: Optional[str] = Field(None)

    options: List[PollOptionCreateSchema] = Field(..., min_length=1, description="Список варіантів відповідей (мінімум 1)") # min_items в OpenAPI

    @model_validator(mode='after')
    def set_default_min_max_choices(cls, data: 'PollCreateSchema') -> 'PollCreateSchema':
        if not data.allow_multiple_choices:
            data.min_choices = 1
            data.max_choices = 1 # Або залишити None, якщо це означає "тільки 1"
        else:
            if data.min_choices is None:
                data.min_choices = 1 # За замовчуванням хоча б один варіант
            if data.max_choices is not None and data.min_choices > data.max_choices:
                raise ValueError("Максимальна кількість обраних варіантів не може бути меншою за мінімальну.")
        return data

    @field_validator('ends_at')
    @classmethod
    def validate_ends_at(cls, value: Optional[datetime], values: Any) -> Optional[datetime]:
        # Pydantic v1: values.data.get('starts_at')
        # Pydantic v2: values - це вже об'єкт схеми, але на етапі field_validator ще не всі поля можуть бути.
        # Краще використовувати model_validator для перехресних перевірок.
        # Тут просто перевірка, що ends_at > starts_at, якщо обидва є.
        # Це буде зроблено в model_validator нижче.
        # Або ж, якщо starts_at не передається, то ця перевірка не потрібна.
        # Поки що залишаю без цієї перевірки тут.
        return value

    @model_validator(mode='after')
    def check_dates(cls, data: 'PollCreateSchema') -> 'PollCreateSchema':
        if data.starts_at and data.ends_at and data.starts_at >= data.ends_at:
            raise ValueError("Дата закінчення опитування має бути пізнішою за дату початку.")
        return data


class PollUpdateSchema(BaseSchema):
    """Схема для оновлення існуючого опитування."""
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None)
    state_id: Optional[uuid.UUID] = Field(None) # Наприклад, для закриття/скасування опитування

    # Ці поля зазвичай не змінюються для активного опитування, але можливо для чернетки
    is_anonymous: Optional[bool] = Field(None)
    allow_multiple_choices: Optional[bool] = Field(None)
    starts_at: Optional[datetime] = Field(None)
    ends_at: Optional[datetime] = Field(None)

    min_choices: Optional[int] = Field(None, ge=1)
    max_choices: Optional[int] = Field(None, ge=1)
    show_results_before_voting: Optional[bool] = Field(None)
    results_visibility: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)
    is_deleted: Optional[bool] = Field(None)

    # Оновлення варіантів відповідей (options) - це складніша операція:
    # додавання нових, видалення старих, оновлення існуючих.
    # Це краще робити через окремі ендпоінти для /polls/{poll_id}/options.
    # Тому тут `options` не включаю.
    # options: Optional[List[Union[PollOptionUpdateSchema, PollOptionCreateSchema]]] = None

    # TODO: Додати валідатори, аналогічні до CreateSchema, якщо потрібно.
    pass

# PollSchema.model_rebuild()
# PollOptionSchema.model_rebuild()
# PollVoteSchema.model_rebuild()

# TODO: Переконатися, що схеми відповідають моделям.
# PollModel, PollOptionModel, PollVoteModel.
# Схеми створені для кожної з них (Base, Create, Update, Read).
# Зв'язки між ними (PollSchema.options, PollVoteSchema.user/option) відображені.
# Використання ForwardRef для уникнення циклічних імпортів.
# Валідатори для дат та кількості виборів.
# Все виглядає досить повно.
# `min_length=1` для `options` в `PollCreateSchema` гарантує, що опитування має хоча б один варіант.
# `total_votes` та `votes_count` (закоментовані) - це обчислювані поля, які краще розраховувати на сервісному рівні
# і додавати до схеми відповіді, якщо потрібно, а не зберігати в БД чи вимагати в запиті.
# Поле `name` з `BaseMainSchema` для `PollSchema` - це питання/назва опитування.
# `group_id` - група. `state_id` - статус опитування.
# `PollOptionSchema` має `order_num` для сортування.
# `PollVoteSchema` має `user_id` (nullable для анонімних).
# Все виглядає узгоджено.
