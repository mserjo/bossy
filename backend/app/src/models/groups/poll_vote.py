# backend/app/src/models/groups/poll_vote.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `PollVoteModel` для зберігання голосів користувачів
в опитуваннях. Кожен запис представляє голос одного користувача за один або декілька
(якщо дозволено) варіантів відповіді в конкретному опитуванні.
"""

from sqlalchemy import Column, ForeignKey, DateTime, UniqueConstraint # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

class PollVoteModel(BaseModel):
    """
    Модель для зберігання голосів користувачів в опитуваннях.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор голосу (успадковано).
        poll_id (uuid.UUID): Ідентифікатор опитування, до якого належить цей голос.
        option_id (uuid.UUID): Ідентифікатор обраного варіанту відповіді.
        user_id (uuid.UUID | None): Ідентифікатор користувача, який проголосував.
                                    Може бути NULL, якщо голосування анонімне (`PollModel.is_anonymous` = True).
        voted_at (datetime): Час, коли був поданий голос (може бути `created_at`).

        created_at (datetime): Дата та час створення запису (успадковано, відповідає `voted_at`).
        updated_at (datetime): Дата та час останнього оновлення (успадковано, зазвичай не оновлюється).

    Зв'язки:
        poll (relationship): Зв'язок з PollModel.
        option (relationship): Зв'язок з PollOptionModel.
        user (relationship): Зв'язок з UserModel (якщо голосування не анонімне).
    """
    __tablename__ = "poll_votes"

    poll_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("polls.id", ondelete="CASCADE"), nullable=False, index=True)
    option_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("poll_options.id", ondelete="CASCADE"), nullable=False, index=True)

    # Користувач, який проголосував.
    # `nullable=True`, оскільки голосування може бути анонімним (визначається в PollModel.is_anonymous).
    # Якщо анонімне, user_id не зберігається.
    # TODO: Замінити "users.id" на константу або імпорт моделі UserModel.
    user_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_poll_votes_user_id", ondelete="SET NULL"), nullable=True, index=True)
    # `ondelete="SET NULL"` для user_id: якщо користувач видаляється, його голос стає анонімним,
    # але сам голос залишається (якщо це бажана поведінка). Або "CASCADE", якщо голоси видалених користувачів не потрібні.
    # Поки що SET NULL, щоб зберегти цілісність кількості голосів.

    # `created_at` з BaseModel може слугувати як `voted_at`.

    # --- Зв'язки (Relationships) ---
    poll = relationship("PollModel", back_populates="votes")
    option = relationship("PollOptionModel", back_populates="votes")
    user = relationship("UserModel", foreign_keys=[user_id]) # back_populates="poll_votes" буде в UserModel

    # Обмеження унікальності:
    # 1. Якщо голосування не анонімне і дозволено лише один вибір: (poll_id, user_id) має бути унікальним.
    #    Це означає, що користувач може проголосувати в одному опитуванні лише один раз.
    # 2. Якщо голосування не анонімне і дозволено декілька виборів: (poll_id, user_id, option_id) має бути унікальним.
    #    Це означає, що користувач не може проголосувати за один і той же варіант двічі.
    # 3. Якщо голосування анонімне: обмежень на user_id немає.
    #
    # Поки що додамо обмеження для найпоширенішого випадку: один користувач - один голос за один варіант в опитуванні.
    # Якщо опитування дозволяє кілька варіантів, то один користувач може мати кілька записів у PollVoteModel
    # для одного poll_id, але з різними option_id.
    # Якщо опитування не дозволяє кілька варіантів, то один користувач може мати лише один запис для одного poll_id.
    # Це контролюється логікою на сервісному рівні.
    # Обмеження (poll_id, user_id, option_id) гарантує, що користувач не голосує за той самий варіант двічі.
    # Якщо `user_id` є NULL (анонімне голосування), це обмеження не застосовується до `user_id`.
    # PostgreSQL підтримує NULL в унікальних індексах (NULL не дорівнює іншому NULL).
    __table_args__ = (
        UniqueConstraint('poll_id', 'user_id', 'option_id', name='uq_poll_user_option_vote'),
        # TODO: Розглянути можливість створення часткового індексу/обмеження,
        # якщо `user_id` не NULL: UniqueConstraint('poll_id', 'user_id', name='uq_poll_user_vote', where=(user_id != None)),
        # якщо користувач може голосувати лише один раз в опитуванні (незалежно від варіанту),
        # коли `allow_multiple_choices` = False.
        # Поточне обмеження `uq_poll_user_option_vote` є більш загальним і правильним.
    )

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі PollVoteModel.
        """
        user_info = f"user_id='{self.user_id}'" if self.user_id else "anonymous"
        return f"<{self.__class__.__name__}(poll_id='{self.poll_id}', option_id='{self.option_id}', {user_info})>"

# TODO: Перевірити відповідність `technical-task.md` та `structure-claude-v3.md`.
# `structure-claude-v3.md` вказує `poll_vote.py`.
# Назва таблиці `poll_votes` є логічною.
# Ключові поля: `poll_id`, `option_id`, `user_id`.
# `ondelete="CASCADE"` для `poll_id` та `option_id` забезпечує видалення голосів при видаленні опитування або варіанту.
# `ondelete="SET NULL"` для `user_id` для збереження анонімності голосу при видаленні користувача.
# Зв'язки визначені.
# `UniqueConstraint` для `(poll_id, user_id, option_id)` запобігає дублюванню голосів.
# Все виглядає узгоджено.
# `created_at` використовується як час голосування.
# Анонімність контролюється через `user_id = NULL` та перевірку `PollModel.is_anonymous` на сервісному рівні.
# Логіка для `allow_multiple_choices` (чи може один user_id мати кілька записів для одного poll_id з різними option_id)
# також реалізується на сервісному рівні. Обмеження `uq_poll_user_option_vote` це дозволяє.
# Якщо ж `allow_multiple_choices` = False, то сервіс повинен перевіряти, що для пари (poll_id, user_id)
# ще немає записів перед створенням нового голосу.
# Або ж, якщо `allow_multiple_choices` = False, то можна додати `UniqueConstraint('poll_id', 'user_id')`
# (з урахуванням анонімності). Але це ускладнить модель. Простіше контролювати в логіці.
# Поточне `UniqueConstraint` є достатнім для базової функціональності.
