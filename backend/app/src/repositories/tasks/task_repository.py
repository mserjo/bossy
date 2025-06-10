# backend/app/src/repositories/tasks/task_repository.py
"""
Репозиторій для моделі "Завдання" (Task).

Цей модуль визначає клас `TaskRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи із завданнями/подіями, такі як
отримання завдань за ID групи, завдань, призначених користувачеві,
та підзавдань.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func, join
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделей та схем
from backend.app.src.models.tasks.task import Task
from backend.app.src.models.tasks.assignment import TaskAssignment  # Для join в get_tasks_assigned_to_user
from backend.app.src.models.dictionaries.task_types import TaskType  # Для фільтрації за task_type_code
from backend.app.src.models.dictionaries.statuses import Status  # Для фільтрації за status_code
from backend.app.src.schemas.tasks.task import TaskCreateSchema, TaskUpdateSchema
from backend.app.src.core.dicts import TaskStatus as TaskStatusEnum  # Для active_only


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class TaskRepository(BaseRepository[Task, TaskCreateSchema, TaskUpdateSchema]):
    """
    Репозиторій для управління записами завдань/подій (`Task`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для специфічного пошуку та отримання завдань.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `Task`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=Task)

    async def get_tasks_by_group_id(
            self,
            group_id: int,
            skip: int = 0,
            limit: int = 100,
            *,
            active_only: bool = False,  # Отримувати лише завдання, які не в фінальному/архівному статусі
            task_type_code: Optional[str] = None,
            status_code: Optional[str] = None  # Код статусу з довідника dict_statuses
            # TODO: Узгодити з Task.state, яке може використовувати TaskStatusEnum
    ) -> Tuple[List[Task], int]:
        """
        Отримує список завдань для вказаної групи з пагінацією та фільтрами.

        Args:
            group_id (int): ID групи.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.
            active_only (bool): Якщо True, повертає лише завдання, які не є завершеними або скасованими.
                                Потребує узгодження з тим, як зберігається статус (Task.state чи Task.status_id).
            task_type_code (Optional[str]): Код типу завдання для фільтрації.
            status_code (Optional[str]): Код статусу завдання для фільтрації.

        Returns:
            Tuple[List[Task], int]: Кортеж зі списком завдань та їх загальною кількістю.
        """
        filters = [self.model.group_id == group_id]
        # Використовуємо Task.state, яке успадковане від BaseMainModel -> StateMixin
        if active_only:
            # Припускаємо, що "активні" - це ті, що не COMPLETED, CANCELLED, REJECTED, EXPIRED
            # Це потрібно узгодити з фактичними значеннями TaskStatusEnum, які позначають неактивність.
            inactive_statuses = [
                TaskStatusEnum.COMPLETED.value,
                TaskStatusEnum.CANCELLED.value,
                TaskStatusEnum.REJECTED.value,
                TaskStatusEnum.EXPIRED.value
            ]
            filters.append(self.model.state.notin_(inactive_statuses))

        # Формуємо запити для stmt та count_stmt
        stmt = select(self.model)
        count_stmt = select(func.count(self.model.id)).select_from(self.model)

        if task_type_code:
            # Приєднуємо таблицю типів завдань і фільтруємо за кодом
            stmt = stmt.join(TaskType, self.model.task_type_id == TaskType.id)
            count_stmt = count_stmt.join(TaskType, self.model.task_type_id == TaskType.id)
            filters.append(TaskType.code == task_type_code)

        if status_code:
            # TODO: Якщо Task.status_id використовується для зв'язку з dict_statuses
            if hasattr(self.model, 'status_id') and self.model.status_id is not None:
                stmt = stmt.join(Status, self.model.status_id == Status.id)
                count_stmt = count_stmt.join(Status, self.model.status_id == Status.id)
                filters.append(Status.code == status_code)
            # Або якщо Task.state напряму містить коди статусів (менш ймовірно для узгодженості)
            # elif hasattr(self.model, 'state'):
            #     filters.append(self.model.state == status_code)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = (await self.db_session.execute(count_stmt)).scalar_one()

        stmt = stmt.offset(skip).limit(limit).order_by(self.model.created_at.desc())
        # .options(selectinload(self.model.task_type), selectinload(self.model.status)) # Приклад жадібного завантаження

        items_result = await self.db_session.execute(stmt)
        items = list(items_result.scalars().all())

        return items, total

    async def get_tasks_assigned_to_user(
            self,
            user_id: int,
            group_id: Optional[int] = None,
            skip: int = 0,
            limit: int = 100,
            active_only: bool = False  # Чи повертати лише "активні" завдання
    ) -> Tuple[List[Task], int]:
        """
        Отримує список завдань, призначених вказаному користувачеві, з пагінацією.

        Args:
            user_id (int): ID користувача.
            group_id (Optional[int]): ID групи для фільтрації (якщо потрібно).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.
            active_only (bool): Якщо True, повертає лише завдання, які не є завершеними або скасованими.

        Returns:
            Tuple[List[Task], int]: Кортеж зі списком завдань та їх загальною кількістю.
        """
        base_join = self.model.join(TaskAssignment, self.model.id == TaskAssignment.task_id)

        filters = [TaskAssignment.user_id == user_id]
        if group_id is not None:
            filters.append(self.model.group_id == group_id)

        if active_only:
            inactive_statuses = [
                TaskStatusEnum.COMPLETED.value, TaskStatusEnum.CANCELLED.value,
                TaskStatusEnum.REJECTED.value, TaskStatusEnum.EXPIRED.value
            ]
            filters.append(self.model.state.notin_(inactive_statuses))

        count_stmt = select(func.count(self.model.id)).select_from(base_join).where(*filters)
        total = (await self.db_session.execute(count_stmt)).scalar_one()

        stmt = (
            select(self.model)
            .select_from(base_join)
            .where(*filters)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.due_date.asc().nulls_last(), self.model.created_at.desc())
        # Пріоритет за терміном виконання
            # .options(selectinload(self.model.task_type), selectinload(self.model.status))
        )

        items_result = await self.db_session.execute(stmt)
        items = list(items_result.scalars().all())

        return items, total

    async def get_sub_tasks(self, parent_task_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[Task], int]:
        """
        Отримує список підзавдань для вказаного батьківського завдання з пагінацією.

        Args:
            parent_task_id (int): ID батьківського завдання.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Task], int]: Кортеж зі списком підзавдань та їх загальною кількістю.
        """
        filters = [self.model.parent_task_id == parent_task_id]
        order_by = [self.model.created_at.asc()]  # Або інше сортування, наприклад, за порядковим номером, якщо є
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)


if __name__ == "__main__":
    # Демонстраційний блок для TaskRepository.
    print("--- Репозиторій Завдань/Подій (TaskRepository) ---")

    print("Для тестування TaskRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {Task.__name__}.")
    print(f"  Очікує схему створення: {TaskCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {TaskUpdateSchema.__name__}")

    print("\nСпецифічні методи:")
    print("  - get_tasks_by_group_id(group_id, skip, limit, active_only, task_type_code, status_code)")
    print("  - get_tasks_assigned_to_user(user_id, group_id, skip, limit, active_only)")
    print("  - get_sub_tasks(parent_task_id, skip, limit)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    print("TODO: Узгодити логіку фільтрації за статусом (Task.state vs Task.status_id) в get_tasks_by_group_id.")
