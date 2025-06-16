# backend/app/src/repositories/tasks/event_repository.py

"""
Репозиторій для сутностей "Подія" (Event).
Надає CRUD операції та специфічні методи для управління подіями.
"""

from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload # Імпорт для "жадібного" завантаження

from backend.app.src.models.tasks.event import Event
from backend.app.src.schemas.tasks.event import EventCreateSchema, EventUpdateSchema
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.config.logging import get_logger # Стандартизований імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class EventRepository(BaseRepository[Event, EventCreateSchema, EventUpdateSchema]):
    """
    Репозиторій для управління записами Подій (Event).
    """

    def __init__(self):
        """
        Ініціалізує репозиторій з моделлю Event.
        """
        super().__init__(model=Event)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_events_for_group(
        self,
        session: AsyncSession,
        *,
        group_id: int,
        start_after: Optional[datetime] = None,
        end_before: Optional[datetime] = None,   # Події, що закінчуються до цього часу
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        """
        Отримує події для конкретної групи, опціонально фільтровані за часом початку/закінчення.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            group_id (int): Ідентифікатор групи.
            start_after (Optional[datetime]): Фільтр для подій, що починаються після цієї дати/часу.
            end_before (Optional[datetime]): Фільтр для подій, що закінчуються до цієї дати/часу (або починаються раніше, якщо немає часу закінчення).
            include_deleted (bool): Якщо True, включає "м'яко" видалені події.
            skip (int): Кількість записів, яку потрібно пропустити.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            List[Event]: Список об'єктів Event.
        """
        # self.model тут посилається на Event
        conditions = [self.model.group_id == group_id]
        if start_after:
            conditions.append(self.model.start_time > start_after)
        if end_before:
            conditions.append(
                or_(
                    self.model.end_time < end_before,
                    and_(self.model.end_time.is_(None), self.model.start_time < end_before)
                )
            )

        if not include_deleted and hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None))

        statement = (
            select(self.model)
            .where(*conditions)
            .options(
                selectinload(self.model.created_by),
                selectinload(self.model.assignments),
                selectinload(self.model.completions)
            ) # "Жадібне" завантаження пов'язаних об'єктів
            .order_by(self.model.start_time.asc())
            .offset(skip)
            .limit(limit)
        )
        try:
            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(
                f"Помилка при отриманні подій для групи {group_id}: {e}",
                exc_info=True
            )
            return []

    async def get_events_in_date_range(
        self,
        session: AsyncSession,
        *,
        range_start: datetime,
        range_end: datetime,
        group_id: Optional[int] = None,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        """
        Отримує події, які активні (start_time < range_end ТА (end_time > range_start АБО end_time IS NULL))
        в межах заданого діапазону дат [range_start, range_end].
        Опціонально фільтрує за group_id.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            range_start (datetime): Початок діапазону дат.
            range_end (datetime): Кінець діапазону дат.
            group_id (Optional[int]): Опціональний фільтр за ID групи.
            include_deleted (bool): Якщо True, включає "м'яко" видалені події.
            skip (int): Кількість записів, яку потрібно пропустити.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            List[Event]: Список об'єктів Event, активних в межах діапазону.
        """
        conditions = [
            self.model.start_time < range_end,
            or_(
                self.model.end_time > range_start,
                self.model.end_time.is_(None)
            )
        ]
        if group_id is not None:
            conditions.append(self.model.group_id == group_id)

        if not include_deleted and hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None))

        statement = (
            select(self.model)
            .where(*conditions)
            .options(
                selectinload(self.model.created_by),
                selectinload(self.model.assignments),
                selectinload(self.model.completions)
            ) # "Жадібне" завантаження
            .order_by(self.model.start_time.asc())
            .offset(skip)
            .limit(limit)
        )
        try:
            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(
                f"Помилка при отриманні подій в діапазоні дат ({range_start} - {range_end}): {e}",
                exc_info=True
            )
            return []

    # Методи BaseRepository: create, get, update, delete успадковуються.
    # Створення подій потребуватиме group_id, start_time тощо, що обробляється сервісом.
    # Оновлення подій використовуватиме схему EventUpdateSchema.
    # Для get() та get_by_id() з BaseRepository, "жадібне" завантаження зв'язків
    # (created_by, assignments, completions) буде залежати від конфігурації lazy='selectin' у моделі Event.
    # Якщо потрібно гарантоване "жадібне" завантаження для окремих запитів get,
    # можна перевизначити get() або додати новий метод get_with_details(session: AsyncSession, record_id: int).
    # Наприклад:
    # async def get_with_details(self, session: AsyncSession, record_id: int) -> Optional[Event]:
    #     logger.debug(f"Отримання деталей для Event ID: {record_id}")
    #     statement = select(self.model).where(self.model.id == record_id).options(
    #         selectinload(self.model.created_by),
    #         selectinload(self.model.assignments),
    #         selectinload(self.model.completions)
    #     )
    #     try:
    #         result = await session.execute(statement)
    #         return result.scalar_one_or_none()
    #     except Exception as e:
    #         logger.error(f"Помилка при отриманні деталей для Event ID {record_id}: {e}", exc_info=True)
    #         return None
