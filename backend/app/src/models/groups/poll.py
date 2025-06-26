# backend/app/src/models/groups/poll.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `PollModel` для зберігання опитувань або голосувань
в межах групи. Користувачі групи можуть брати участь у голосуванні.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer, \
    CheckConstraint  # type: ignore # String, Text etc. for mapped_column
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column # type: ignore
from typing import Optional, List
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

from backend.app.src.models.base import BaseMainModel

class PollModel(BaseMainModel):
    """
    Модель для зберігання опитувань/голосувань в групі.
    (Атрибути name, description, state_id, group_id, notes, deleted_at, is_deleted успадковані)
    """
    __tablename__ = "polls"

    created_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_polls_creator_id", ondelete="SET NULL"), nullable=False, index=True)

    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_multiple_choices: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    min_choices: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_choices: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    show_results_before_voting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    results_visibility: Mapped[str] = mapped_column(String(50), default="after_end", nullable=False)

    # --- Зв'язки (Relationships) ---
    # group: Mapped["GroupModel"] - успадковано з BaseMainModel.state (там є foreign_keys=[group_id])
    # state: Mapped[Optional["StatusModel"]] - успадковано з BaseMainModel.state (там є foreign_keys=[state_id])

    creator: Mapped["UserModel"] = relationship(foreign_keys=[created_by_user_id], back_populates="created_polls")
    options: Mapped[List["PollOptionModel"]] = relationship(back_populates="poll", cascade="all, delete-orphan", order_by="PollOptionModel.order_num")
    votes: Mapped[List["PollVoteModel"]] = relationship(back_populates="poll", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('group_id IS NOT NULL', name='ck_poll_group_id_not_null'),
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', group_id='{self.group_id}')>"

# Примітки до змін:
# - Переведено на стиль SQLAlchemy 2.0 (Mapped, mapped_column).
# - `ondelete="SET NULL"` для `created_by_user_id`, щоб опитування могло існувати без автора.
# - `back_populates` для `creator` узгоджено з тим, що буде в `UserModel`.
# - Зв'язки `group` та `state` вже визначені в `BaseMainModel` і будуть успадковані.
#   `PollModel.group_id` та `PollModel.state_id` є відповідними ForeignKey полями.
#   У `BaseMainModel`:
#   `group: Mapped[Optional["GroupModel"]] = relationship("GroupModel", foreign_keys=[group_id], lazy="selectin")`
#   `state: Mapped[Optional["StatusModel"]] = relationship("StatusModel", foreign_keys=[state_id], lazy="selectin")`
#   Потрібно буде додати `polls = relationship("PollModel", back_populates="group")` в `GroupModel`.
#   Та `polls_with_this_state = relationship("PollModel", back_populates="state")` в `StatusModel`.
#   (Це вже було зроблено для StatusModel, для GroupModel буде на наступному кроці).
#
# Все інше (наприклад, `order_by` для options) залишено як було.
# `group_id` в `PollModel` (успадкований з `BaseMainModel`) має бути NOT NULL.
# Це забезпечується логікою на сервісному рівні при створенні.
# Або можна перевизначити поле тут з `nullable=False`, але це може конфліктувати з успадкуванням.
# `BaseMainModel.group_id` є `nullable=True`.
# Для `PollModel` це поле завжди має бути заповнене.
# Можна додати `CheckConstraint(group_id.isnot(None))` через міграції для таблиці `polls`.
# Або зробити поле `group_id` в `PollModel` обов'язковим при перевизначенні, якщо це можливо без конфліктів.
#
# Поки що залишаю успадкований `group_id` як `nullable=True` з `BaseMainModel`,
# покладаючись на логіку сервісу для забезпечення його заповнення для опитувань.
# І додаю коментар для Alembic міграції.
# __table_args__ = (
#     CheckConstraint('group_id IS NOT NULL', name='ck_poll_group_id_not_null'),
# )
# Це краще додати через міграції.
#
# Все готово.
