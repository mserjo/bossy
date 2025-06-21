# backend/app/src/models/tasks/event.py

"""
SQLAlchemy модель для Подій.
Події можуть бути схожі на завдання, але можуть представляти зустрічі, віхи або інформаційні елементи.
"""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseMainModel
# from backend.app.src.core.dicts import EventFrequency # Якщо події також мають повторюваність
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.groups.group import Group
    from backend.app.src.models.tasks.assignment import TaskAssignment
    from backend.app.src.models.tasks.completion import TaskCompletion
    # from backend.app.src.models.dictionaries.task_types import TaskType # Якщо використовується task_types для event_type
    # Або визначити нову таблицю та модель dict_event_types


class Event(BaseMainModel):
    """
    Представляє подію в межах групи (наприклад, зустріч, призначення, віха, свято).
    Успадковує від BaseMainModel, що надає поля: id, name, description, state, group_id, notes, created_at, updated_at, deleted_at.
    Схоже на Завдання, але може мати інший акцент на полях, таких як час початку/закінчення та місцезнаходження.
    """
    __tablename__ = "events"

    # 'name', 'description', 'state', 'notes', 'group_id' успадковані.
    # 'state' може представляти 'майбутня', 'триваюча', 'минула', 'скасована'.

    # Можливо, 'event_type_id' (FK до dict_task_types або нового dict_event_types) був би корисним.
    # Наразі припускаємо, що відмінність від Завдання є переважно семантичною або через меншу кількість специфічних полів Завдання.
    # event_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("dict_event_types.id"), index=True, comment="FK до довідника типів подій")

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True, comment="Дата та час початку події (UTC)")
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True, comment="Необов'язкові дата та час закінчення події (UTC)")
    location: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="Фізичне або віртуальне місцезнаходження події")

    # Якщо події можуть бути повторюваними, знадобляться поля, схожі на модель Task:
    # is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="Чи є подія повторюваною")
    # recurrence_frequency: Mapped[Optional[EventFrequency]] = mapped_column(SQLAlchemyEnum(EventFrequency), nullable=True, comment="Частота повторення")
    # recurrence_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Інтервал повторення")

    # Зв'язки, якщо події можуть бути призначені або мати виконання/відгуки
    assignments: Mapped[List["TaskAssignment"]] = relationship(back_populates="event", cascade="all, delete-orphan", lazy="selectin")
    completions: Mapped[List["TaskCompletion"]] = relationship(back_populates="event", cascade="all, delete-orphan", lazy="selectin")

    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", name="fk_event_created_by_user_id", ondelete="SET NULL"),
        nullable=True,
        comment="Користувач, який створив подію"
    )
    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_user_id], lazy="selectin")

    # Зв'язок з групою (group_id успадковано від BaseMainModel через GroupAffiliationMixin)
    group: Mapped[Optional["Group"]] = relationship(
        foreign_keys=["Event.group_id"], # Використовуємо успадкований group_id, рядкове представлення
        lazy="selectin"
        # back_populates="events" # Потребуватиме додавання Mapped[List["Event"]] = relationship(back_populates="group") до моделі Group
    )

    # _repr_fields успадковуються та збираються з BaseMainModel (id, name, state_id, group_id, created_at тощо).
    # Додаємо специфічні для Event поля.
    _repr_fields = ("start_time", "location", "created_by_user_id")


if __name__ == "__main__":
    # from datetime import timezone, timedelta # Потрібно для __main__ прикладу, якщо він створює datetime
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Event Model --- Demonstration")

    # Example Event instance
    # Assume Group with id=1 exists
    team_meeting = Event(
        name="Weekly Team Sync",
        description="Discuss progress, blockers, and plan for the upcoming week.",
        group_id=1,
        start_time=datetime.now(timezone.utc) + timedelta(days=3, hours=10), # Starts in 3 days at 10 AM UTC
        end_time=datetime.now(timezone.utc) + timedelta(days=3, hours=11),   # Ends one hour later
        location="Virtual - Zoom Link in Description",
        state="upcoming" # Example use of inherited 'state' field
    )
    team_meeting.id = 1 # Simulate ORM-set ID
    team_meeting.created_at = datetime.now(timezone.utc)
    team_meeting.updated_at = datetime.now(timezone.utc)

    logger.info(f"Example Event: {team_meeting!r}")
    logger.info(f"  Name: {team_meeting.name}")
    logger.info(f"  Start Time: {team_meeting.start_time.isoformat() if team_meeting.start_time else 'N/A'}")
    logger.info(f"  End Time: {team_meeting.end_time.isoformat() if team_meeting.end_time else 'N/A'}")
    logger.info(f"  Location: {team_meeting.location}")
    logger.info(f"  State: {team_meeting.state}")
    logger.info(f"  Created At: {team_meeting.created_at.isoformat() if team_meeting.created_at else 'N/A'}")


    birthday_event = Event(
        name="Alice's Birthday Party",
        group_id=1,
        start_time=datetime(2024, 12, 15, 18, 0, 0, tzinfo=timezone.utc),
        location="Community Hall"
    )
    birthday_event.id = 2
    logger.info(f"Another Event: {birthday_event!r}")

    # To view relationships, a DB session and related objects would be needed.
    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"Event attributes (conceptual table columns): {[c.name for c in Event.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
