# backend/app/src/models/groups/poll.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `PollModel` для зберігання опитувань або голосувань
в межах групи. Користувачі групи можуть брати участь у голосуванні.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

# Використовуємо BaseMainModel, оскільки опитування має назву (питання), опис, статус.
# group_id буде вказувати на групу, до якої належить опитування.
from backend.app.src.models.base import BaseMainModel

class PollModel(BaseMainModel):
    """
    Модель для зберігання опитувань/голосувань в групі.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор опитування (успадковано).
        name (str): Питання або назва опитування (успадковано).
        description (str | None): Детальний опис або контекст опитування (успадковано).
        state_id (uuid.UUID | None): Статус опитування (наприклад, "активне", "завершене", "скасоване", "чернетка").
                                     Посилається на StatusModel. (успадковано)
        group_id (uuid.UUID): Ідентифікатор групи, в якій проводиться опитування. (успадковано, тут буде NOT NULL)

        created_by_user_id (uuid.UUID): Ідентифікатор користувача (адміна групи), який створив опитування.
        is_anonymous (bool): Чи є голосування анонімним.
        allow_multiple_choices (bool): Чи дозволено обирати декілька варіантів відповіді.
        starts_at (datetime | None): Дата та час початку опитування (якщо відкладений старт).
        ends_at (datetime | None): Дата та час закінчення опитування. NULL означає безстрокове (доки не закриють вручну).

        # Додаткові поля
        min_choices (int): Мінімальна кількість варіантів, яку потрібно обрати (якщо allow_multiple_choices=True).
        max_choices (int | None): Максимальна кількість варіантів (якщо allow_multiple_choices=True).
        show_results_before_voting (bool): Чи показувати результати тим, хто ще не проголосував.
        results_visibility (str): Хто може бачити результати ('all', 'voted_only', 'admins_only', 'after_end').

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення (успадковано).
        is_deleted (bool): Прапорець "м'якого" видалення (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Зв'язки:
        group (relationship): Зв'язок з GroupModel.
        creator (relationship): Зв'язок з UserModel (хто створив).
        options (relationship): Список варіантів відповідей для цього опитування (PollOptionModel).
        votes (relationship): Список голосів, поданих в цьому опитуванні (PollVoteModel).
        status (relationship): Зв'язок зі статусом опитування (вже є через state_id з BaseMainModel).
    """
    __tablename__ = "polls"

    # group_id успадковано і має бути NOT NULL для опитувань.
    # Це буде забезпечено на рівні логіки створення або валідації.
    # ForeignKey("groups.id", name="fk_polls_group_id") вже є в BaseMainModel, якщо group_id там визначено як ForeignKey.
    # Потрібно переконатися, що group_id в BaseMainModel є ForeignKey.
    # В BaseMainModel: group_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=True, index=True)
    # Тут ми очікуємо, що для PollModel group_id буде завжди заповненим.

    # Ідентифікатор користувача (адміна групи), який створив опитування.
    # TODO: Замінити "users.id" на константу або імпорт моделі UserModel.
    created_by_user_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_polls_creator_id"), nullable=False, index=True)

    is_anonymous: Column[bool] = Column(Boolean, default=False, nullable=False)
    allow_multiple_choices: Column[bool] = Column(Boolean, default=False, nullable=False)

    starts_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True)
    ends_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True, index=True)

    min_choices: Column[int] = Column(Integer, default=1, nullable=False)
    max_choices: Column[int | None] = Column(Integer, nullable=True) # NULL означає без обмеження (якщо allow_multiple_choices)

    show_results_before_voting: Column[bool] = Column(Boolean, default=False, nullable=False)
    # TODO: Визначити можливі значення для results_visibility (можливо, Enum або довідник)
    results_visibility: Column[str] = Column(String(50), default="after_end", nullable=False) # 'all', 'voted_only', 'admins_only', 'after_end'

    # --- Зв'язки (Relationships) ---
    # Зв'язок з групою (успадкований з BaseMainModel, якщо там визначено relationship `group`)
    # group = relationship("GroupModel", foreign_keys=[group_id], back_populates="polls") # group_id вже є в BaseMainModel
    # Потрібно переконатися, що back_populates="polls" є в GroupModel
    group = relationship("GroupModel", foreign_keys="PollModel.group_id", back_populates="polls")


    creator = relationship("UserModel", foreign_keys=[created_by_user_id]) # back_populates="created_polls" буде в UserModel

    # Варіанти відповідей для цього опитування
    options = relationship("PollOptionModel", back_populates="poll", cascade="all, delete-orphan", order_by="PollOptionModel.order_num")

    # Голоси, подані в цьому опитуванні
    votes = relationship("PollVoteModel", back_populates="poll", cascade="all, delete-orphan")

    # Зв'язок зі статусом (успадкований з BaseMainModel, якщо там визначено relationship `state`)
    # state = relationship("StatusModel", foreign_keys=[state_id])

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі PollModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', group_id='{self.group_id}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "(адмін групи) опитування/голосування користувачів групи анонімні/відкриті"
#   - `is_anonymous` для анонімності.
#   - Створення адміном групи (`created_by_user_id`).
#   - Належність до групи (`group_id`).

# TODO: Узгодити назву таблиці `polls` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseMainModel` як основи.
# Ключові поля: `group_id` (має бути NOT NULL), `created_by_user_id`, `is_anonymous`, `allow_multiple_choices`, `ends_at`.
# Додаткові поля для налаштувань голосування: `min_choices`, `max_choices`, `show_results_before_voting`, `results_visibility`.
# Зв'язки з `GroupModel`, `UserModel`, `PollOptionModel`, `PollVoteModel`.
# `cascade="all, delete-orphan"` для `options` та `votes` означає, що при видаленні опитування
# також видаляються всі його варіанти відповідей та голоси. Це логічно.
# `order_by` для `options` дозволяє отримувати варіанти відповідей у визначеному порядку.
# Все виглядає узгоджено.
# Поле `name` з `BaseMainModel` використовується як питання/назва опитування.
# `description` для деталей. `state_id` для статусу опитування.
# `deleted_at`, `is_deleted`, `notes` успадковані.
# `group_id` в `PollModel` має бути обов'язковим, хоча в `BaseMainModel` він `nullable`.
# Це потрібно буде контролювати на рівні валідації даних або сервісу.
# Або ж можна перевизначити `group_id` в `PollModel` як `nullable=False`.
# Поки що залишаю як є, покладаючись на логіку сервісу.
# Зв'язок `group` уточнено з `foreign_keys="PollModel.group_id"` для уникнення неоднозначності,
# якщо `BaseMainModel` має інші поля `ForeignKey` до `groups.id`.
# (Хоча в `BaseMainModel` `group_id` вже є `ForeignKey("groups.id")`).
# Краще явно вказувати `foreign_keys` в `relationship`, якщо є сумніви.
# `PollOptionModel.order_num` - поле для сортування варіантів, буде додано в `PollOptionModel`.
