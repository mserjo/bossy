# backend/app/src/repositories/tasks/task_repository.py
"""
Репозиторій для моделі "Завдання" (Task).

Цей модуль визначає клас `TaskRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи із завданнями/подіями, такі як
отримання завдань за ID групи, завдань, призначених користувачеві,
та підзавдань.
"""

from typing import List, Optional, Tuple, Any, Sequence, Dict, TYPE_CHECKING # Added Sequence, Dict, TYPE_CHECKING
from datetime import datetime # For type hints, removed 'import datetime as dt'
from sqlalchemy.sql.expression import false, true  # For boolean comparisons

from sqlalchemy import select, func, and_, or_, not_ # join видалено
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделей та схем
from backend.app.src.models.tasks.task import Task
from backend.app.src.models.tasks.assignment import TaskAssignment
from backend.app.src.models.tasks.completion import TaskCompletion # Для get_task_with_all_details
from backend.app.src.models.tasks.review import TaskReview # Для get_task_with_all_details
from backend.app.src.models.dictionaries.task_types import TaskType
from backend.app.src.models.dictionaries.statuses import Status
from backend.app.src.schemas.tasks.task import TaskCreateSchema, TaskUpdateSchema
from backend.app.src.core.dicts import TaskStatus as TaskStatusEnum
from backend.app.src.config.logging import get_logger  # Стандартизований імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


# Необхідно імпортувати UserModel для type hints в selectinload, якщо він використовується.
# Припускаючи, що UserModel знаходиться в backend.app.src.models.auth.user
if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User as UserModel


class TaskRepository(BaseRepository[Task, TaskCreateSchema, TaskUpdateSchema]):
    """
    Репозиторій для управління записами завдань (`Task`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для специфічного пошуку та отримання завдань.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `Task`.
        """
        super().__init__(model=Task)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_tasks_by_group_id(
            self,
            session: AsyncSession,
            group_id: int,
            skip: int = 0,
            limit: int = 100,
            *,
            active_only: bool = False,
            task_type_code: Optional[str] = None,
            status_code: Optional[str] = None
            # TODO: [Статус Завдання] Узгодити з Task.state (успадковане) vs Task.status_id (FK до dict_statuses)
            #       для фільтрації `active_only` та `status_code`.
    ) -> Tuple[List[Task], int]:
        """
        Отримує список завдань для вказаної групи з пагінацією та фільтрами.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            group_id (int): ID групи.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.
            active_only (bool): Якщо True, повертає лише завдання, які не є завершеними або скасованими.
            task_type_code (Optional[str]): Код типу завдання для фільтрації.
            status_code (Optional[str]): Код статусу завдання для фільтрації.

        Returns:
            Tuple[List[Task], int]: Кортеж зі списком завдань та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання завдань для group_id {group_id}, active_only={active_only}, "
            f"type_code={task_type_code}, status_code={status_code}, skip={skip}, limit={limit}"
        )

        conditions = [self.model.group_id == group_id]
        if active_only:
            inactive_statuses = [
                TaskStatusEnum.COMPLETED.value, TaskStatusEnum.CANCELLED.value,
                TaskStatusEnum.REJECTED.value, TaskStatusEnum.EXPIRED.value
            ]
            conditions.append(self.model.state.notin_(inactive_statuses))

        stmt = select(self.model)
        count_stmt = select(func.count(self.model.id)).select_from(self.model)

        if task_type_code:
            stmt = stmt.join(TaskType, self.model.task_type_id == TaskType.id)
            count_stmt = count_stmt.join(TaskType, self.model.task_type_id == TaskType.id)
            conditions.append(TaskType.code == task_type_code)

        if status_code:
            # TODO: [Фільтр Статусу] Уточнити, чи фільтрувати по Task.state чи Task.status_id -> Status.code
            #       згідно з `technical_task.txt` / `structure-claude-v2.md`.
            if hasattr(self.model, 'status_id') and self.model.status_id is not None: # type: ignore
                stmt = stmt.join(Status, self.model.status_id == Status.id) # type: ignore
                count_stmt = count_stmt.join(Status, self.model.status_id == Status.id) # type: ignore
                conditions.append(Status.code == status_code)
            elif hasattr(self.model, 'state'): # Альтернатива, якщо Task.state містить коди
                 conditions.append(self.model.state == status_code)


        stmt = stmt.where(*conditions).offset(skip).limit(limit).order_by(self.model.created_at.desc())
        stmt = stmt.options(
            selectinload(self.model.task_type),
            selectinload(self.model.status),
            selectinload(self.model.created_by_user),
            selectinload(self.model.group)
        )
        count_stmt = count_stmt.where(*conditions)

        try:
            total_result = await session.execute(count_stmt)
            total = total_result.scalar_one()

            items_result = await session.execute(stmt)
            items = list(items_result.scalars().all())

            logger.debug(f"Знайдено {total} завдань для group_id {group_id} з фільтрами.")
            return items, total
        except Exception as e:
            logger.error(f"Помилка при отриманні завдань для group_id {group_id}: {e}", exc_info=True)
            return [], 0

    async def get_task_with_all_details(self, session: AsyncSession, task_id: int) -> Optional[Task]:
        """
        Отримує одне завдання з усіма пов'язаними деталями, необхідними для TaskDetailSchema.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            task_id (int): ID завдання.

        Returns:
            Optional[Task]: Екземпляр завдання з деталями або None.
        """
        logger.debug(f"Отримання деталей для завдання ID: {task_id}")
        stmt = select(self.model).where(self.model.id == task_id).options(
            selectinload(self.model.group),
            selectinload(self.model.task_type),
            selectinload(self.model.status),
            selectinload(self.model.created_by_user),
            selectinload(self.model.parent_task),
            selectinload(self.model.sub_tasks),
            selectinload(self.model.assignments).options(
                selectinload(TaskAssignment.user)
            ),
            selectinload(self.model.completions).options( # Виправлено тут
                selectinload(TaskCompletion.user).options(selectinload(UserModel.user_type))
            ),
            selectinload(self.model.reviews).options( # Виправлено тут
                selectinload(TaskReview.user).options(selectinload(UserModel.user_type))
            ),
            selectinload(self.model.bonus_rules)
        )
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні деталей для завдання ID {task_id}: {e}", exc_info=True)
            return None

    async def get_tasks_assigned_to_user(
            self,
            session: AsyncSession,
            user_id: int,
            group_id: Optional[int] = None,
            skip: int = 0,
            limit: int = 100,
            active_only: bool = False
    ) -> Tuple[List[Task], int]:
        """
        Отримує список завдань, призначених вказаному користувачеві, з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            group_id (Optional[int]): ID групи для фільтрації (якщо потрібно).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.
            active_only (bool): Якщо True, повертає лише завдання, які не є завершеними або скасованими.

        Returns:
            Tuple[List[Task], int]: Кортеж зі списком завдань та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання призначених завдань для user_id {user_id}, group_id: {group_id}, "
            f"active_only: {active_only}, skip: {skip}, limit: {limit}"
        )

        base_join = self.model.join(TaskAssignment, self.model.id == TaskAssignment.task_id)
        conditions = [TaskAssignment.user_id == user_id]

        if group_id is not None:
            conditions.append(self.model.group_id == group_id)

        if active_only:
            inactive_statuses = [
                TaskStatusEnum.COMPLETED.value, TaskStatusEnum.CANCELLED.value,
                TaskStatusEnum.REJECTED.value, TaskStatusEnum.EXPIRED.value
            ]
            conditions.append(self.model.state.notin_(inactive_statuses))

        count_stmt = select(func.count(self.model.id)).select_from(base_join).where(*conditions)

        stmt = (
            select(self.model)
            .select_from(base_join)
            .where(*conditions)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.due_date.asc().nulls_last(), self.model.created_at.desc())
            .options(
                selectinload(self.model.task_type),
                selectinload(self.model.status),
                selectinload(self.model.group)
            )
        )
        try:
            total_result = await session.execute(count_stmt)
            total = total_result.scalar_one()

            items_result = await session.execute(stmt)
            items = list(items_result.scalars().all())

            logger.debug(f"Знайдено {total} призначених завдань для user_id {user_id} з фільтрами.")
            return items, total
        except Exception as e:
            logger.error(
                f"Помилка при отриманні призначених завдань для user_id {user_id}: {e}",
                exc_info=True
            )
            return [], 0

    async def get_sub_tasks(
            self, session: AsyncSession, parent_task_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Task], int]:
        """
        Отримує список підзавдань для вказаного батьківського завдання з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            parent_task_id (int): ID батьківського завдання.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Task], int]: Кортеж зі списком підзавдань та їх загальною кількістю.
        """
        logger.debug(f"Отримання підзавдань для parent_task_id: {parent_task_id}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"parent_task_id": parent_task_id}
        sort_by_field = "created_at"
        sort_order_str = "asc"  # Або інше сортування, наприклад, за порядковим номером, якщо є

        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict,
                sort_by=sort_by_field, sort_order=sort_order_str
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} підзавдань для parent_task_id: {parent_task_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні підзавдань для parent_task_id {parent_task_id}: {e}", exc_info=True)
            return [], 0

    async def get_recurring_task_templates_due(
            self, session: AsyncSession, current_time: datetime.datetime
    ) -> Sequence[Task]:
        """
        Отримує шаблони повторюваних завдань, для яких настав час створення нового екземпляра.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            current_time (datetime.datetime): Поточний час для перевірки.

        Returns:
            Sequence[Task]: Послідовність активних шаблонів завдань, готових до створення екземплярів.
        """
        logger.debug(f"Запит шаблонів повторюваних завдань, актуальних на {current_time}")
        stmt = (
            select(self.model)
            .where(
                self.model.is_recurring_template == true(),
                self.model.is_active == true(),
                or_(self.model.recurrence_end_date == None, self.model.recurrence_end_date >= current_time.date()),
                or_(self.model.recurrence_start_date == None, self.model.recurrence_start_date <= current_time.date()),
                self.model.next_occurrence_at <= current_time
            )
            .options(
                selectinload(self.model.created_by_user),
                selectinload(self.model.task_type),
                selectinload(self.model.group),
                selectinload(self.model.status)
            )
            .order_by(self.model.next_occurrence_at.asc())
        )
        try:
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Помилка при запиті шаблонів повторюваних завдань: {e}", exc_info=True)
            return []

    async def get_tasks_needing_reminders(
            self,
            session: AsyncSession,
            window_start: datetime.datetime,
            window_end: datetime.datetime,
            reminder_delta: datetime.timedelta
    ) -> Sequence[Task]:
        """
        Отримує завдання, для яких потрібно надіслати нагадування.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            window_start (datetime.datetime): Початок вікна для перевірки due_date.
            window_end (datetime.datetime): Кінець вікна для перевірки due_date.
            reminder_delta (datetime.timedelta): Проміжок часу, раніше якого нагадування не надсилалося.

        Returns:
            Sequence[Task]: Послідовність завдань, що потребують нагадування.
        """
        logger.debug(
            f"Запит завдань для нагадувань з {window_start} по {window_end}, дельта нагадування: {reminder_delta}"
        )
        latest_allowed_reminder_time = window_start - reminder_delta
        stmt = (
            select(self.model)
            .join(Status, Status.id == self.model.status_id) # Явне приєднання до Status
            .where(
                self.model.is_recurring_template == false(),
                self.model.is_active == true(),
                self.model.due_date.between(window_start, window_end), # type: ignore
                Status.code.notin_([TaskStatusEnum.COMPLETED.value, TaskStatusEnum.CANCELLED.value]),
                or_(
                    self.model.last_reminder_sent_at == None,
                    self.model.last_reminder_sent_at < latest_allowed_reminder_time
                )
            )
            .options(
                selectinload(self.model.assignments).options(
                    selectinload(TaskAssignment.user)
                ),
                selectinload(self.model.group)
            )
            .order_by(self.model.due_date.asc())
        )
        try:
            result = await session.execute(stmt)
            return result.scalars().unique().all()
        except Exception as e:
            logger.error(f"Помилка при запиті завдань для нагадувань: {e}", exc_info=True)
            return []

# Нижче розташований демонстраційний блок, який був поза класом.
# Його слід або видалити, або адаптувати для тестування методів класу, якщо це доречно.
# Для поточного рефакторингу він не є основним фокусом.
# if __name__ == "__main__":
    # Демонстраційний блок для TaskRepository.
    # logger.info("--- Репозиторій Завдань/Подій (TaskRepository) ---")
    # ... (решта демонстраційного коду) ...
