# backend/app/src/services/tasks/task.py
# backend/app/src/services/tasks/task.py
# import logging # Замінено на централізований логер
from typing import List, Optional, Any
# UUID видалено
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # sqlalchemy.future тепер select
from sqlalchemy.orm import selectinload, noload # joinedload видалено
from sqlalchemy.exc import IntegrityError

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.tasks.task import Task
from backend.app.src.repositories.tasks.task_repository import TaskRepository # Імпорт репозиторію
from backend.app.src.models.auth.user import User
from backend.app.src.models.groups.group import Group
from backend.app.src.models.dictionaries.task_types import TaskType
from backend.app.src.models.dictionaries.statuses import Status

from backend.app.src.models.tasks.assignment import TaskAssignment
from backend.app.src.models.tasks.completion import TaskCompletion
from backend.app.src.models.tasks.review import TaskReview

from backend.app.src.schemas.tasks.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskDetailedResponse
)
from backend.app.src.config.logging import logger
from backend.app.src.config import settings as global_settings

DEFAULT_TASK_STATUS_CODE = "OPEN" # TODO: Перенести в конфігурацію


class TaskService(BaseService):
    """
    Сервіс для управління завданнями, включаючи CRUD-операції та обробку
    специфічної для завдань логіки, такої як повторення (хоча фактичне створення
    екземплярів для повторюваних завдань може бути делеговано сервісу планування).
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.task_repo = TaskRepository() # Ініціалізація репозиторію
        logger.info("TaskService ініціалізовано.")

    async def get_task_by_id(self, task_id: int, include_details: bool = False) -> Optional[ # Змінено UUID на int
        TaskResponse]:
        """
        Отримує завдання за його ID.
        Опціонально може включати більше деталей.
        """
        logger.debug(f"Спроба отримання завдання за ID: {task_id}, include_details: {include_details}")

        if include_details:
            task_db = await self.task_repo.get_task_with_all_details(session=self.db_session, task_id=task_id)
        else:
            # task_repo.get() не завантажує зв'язки за замовчуванням.
            # Для TaskResponse потрібні як мінімум group, task_type, status, created_by_user.
            # Залишаємо прямий запит для простого TaskResponse, якщо get() з repo не достатній.
            query = select(Task).where(Task.id == task_id).options(
                selectinload(Task.group).options(noload("*")),
                selectinload(Task.task_type),
                selectinload(Task.status),
                selectinload(Task.created_by_user).options(noload("*"))
            )
            task_db = (await self.db_session.execute(query)).scalar_one_or_none()

        if task_db:
            logger.info(f"Завдання з ID '{task_id}' знайдено.")
            response_model = TaskDetailedResponse if include_details else TaskResponse
            return response_model.model_validate(task_db)

        logger.info(f"Завдання з ID '{task_id}' не знайдено.")
        return None

    async def create_task(self, task_create_data: TaskCreate, creator_user_id: int) -> TaskDetailedResponse: # Змінено UUID на int
        """
        Створює нове завдання.
        """
        logger.debug(f"Спроба створення нового завдання '{task_create_data.title}' користувачем ID: {creator_user_id}")

        # Перевірки існування залишаються в сервісі
        if not await self.db_session.get(Group, task_create_data.group_id):
            raise ValueError(f"Групу з ID '{task_create_data.group_id}' не знайдено.")
        if not await self.db_session.get(TaskType, task_create_data.task_type_id):
            raise ValueError(f"Тип завдання з ID '{task_create_data.task_type_id}' не знайдено.")

        status_id_to_set = task_create_data.status_id
        if not status_id_to_set:
            default_status_db = (await self.db_session.execute( # Прямий запит для статусу
                select(Status).where(Status.code == DEFAULT_TASK_STATUS_CODE))
                                 ).scalar_one_or_none()
            if not default_status_db:
                logger.error(
                    f"Статус за замовчуванням '{DEFAULT_TASK_STATUS_CODE}' не знайдено. Створення завдання не вдалося.")
                raise ValueError(
                    f"Статус завдання є обов'язковим, але статус за замовчуванням '{DEFAULT_TASK_STATUS_CODE}' не знайдено.")
            status_id_to_set = default_status_db.id
            logger.info(
                f"Для нового завдання не надано ID статусу, використано статус за замовчуванням ID: {status_id_to_set}")
        elif not await self.db_session.get(Status, status_id_to_set):
            raise ValueError(f"Статус з ID '{status_id_to_set}' не знайдено.")

        # Підготовка даних для репозиторію
        # TaskCreateSchema (який очікує repo.create) має включати всі необхідні поля.
        # Якщо task_create_data (TaskCreate) вже містить status_id, то добре.
        # Якщо ні, потрібно створити TaskCreateSchema з status_id_to_set.

        # Припускаємо, що TaskCreate (вхідний) може мати status_id=None,
        # а TaskCreateSchema (для репо) вимагає status_id.
        # Або task_create_data вже містить правильний status_id.
        # Для простоти, модифікуємо вхідні дані або створюємо новий об'єкт схеми.

        create_dict = task_create_data.model_dump(exclude_unset=True)
        create_dict['status_id'] = status_id_to_set # Переконуємося, що status_id встановлено

        # Якщо TaskCreateSchema відрізняється від TaskCreate, потрібно створити екземпляр TaskCreateSchema
        # Наразі TaskRepository використовує TaskCreateSchema, який є аліасом TaskCreate.
        # Тому передаємо TaskCreate з оновленим status_id.
        final_task_create_data = TaskCreate(**create_dict)


        try:
            new_task_db = await self.task_repo.create(
                session=self.db_session,
                obj_in=final_task_create_data,
                created_by_user_id=creator_user_id,
                updated_by_user_id=creator_user_id
            )
            await self.commit()
            created_task_detailed = await self.get_task_by_id(new_task_db.id, include_details=True)
            if not created_task_detailed:
                raise RuntimeError(
                    f"Критична помилка: не вдалося отримати створене завдання ID {new_task_db.id} після коміту.")

            logger.info(
                f"Завдання '{new_task_db.title}' (ID: {new_task_db.id}) успішно створено користувачем ID '{creator_user_id}'.")
            return created_task_detailed
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при створенні завдання '{task_create_data.title}': {e}",
                         exc_info=global_settings.DEBUG)
            raise ValueError(f"Не вдалося створити завдання через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при створенні завдання '{task_create_data.title}': {e}",
                         exc_info=global_settings.DEBUG)
            raise

    async def update_task(self, task_id: int, task_update_data: TaskUpdate, current_user_id: int) -> Optional[ # Змінено UUID на int
        TaskDetailedResponse]:
        """Оновлює деталі завдання."""
        logger.debug(f"Спроба оновлення завдання ID: {task_id} користувачем ID: {current_user_id}")

        task_db = await self.task_repo.get(session=self.db_session, id=task_id) # Використання репозиторію
        if not task_db:
            logger.warning(f"Завдання ID '{task_id}' не знайдено для оновлення.")
            return None

        update_data_dict = task_update_data.model_dump(exclude_unset=True)

        # Перевірки існування FK залишаються в сервісі
        if 'task_type_id' in update_data_dict and task_db.task_type_id != update_data_dict['task_type_id']:
            if not await self.db_session.get(TaskType, update_data_dict['task_type_id']):
                raise ValueError(f"Новий тип завдання ID '{update_data_dict['task_type_id']}' не знайдено.")
        if 'status_id' in update_data_dict and task_db.status_id != update_data_dict['status_id']:
            if not await self.db_session.get(Status, update_data_dict['status_id']):
                raise ValueError(f"Новий статус ID '{update_data_dict['status_id']}' не знайдено.")

        # updated_at оновлюється автоматично через TimestampedMixin в BaseRepository.update
        try:
            updated_task_db = await self.task_repo.update(
                session=self.db_session,
                db_obj=task_db,
                obj_in=task_update_data, # Передаємо Pydantic схему TaskUpdate
                updated_by_user_id=current_user_id # Передаємо як kwarg
            )
            await self.commit()

            updated_task_detailed = await self.get_task_by_id(updated_task_db.id, include_details=True)
            if not updated_task_detailed:
                raise RuntimeError(
                    f"Критична помилка: не вдалося отримати оновлене завдання ID {updated_task_db.id} після коміту.")
            logger.info(f"Завдання ID '{task_id}' успішно оновлено користувачем ID '{current_user_id}'.")
            return updated_task_detailed
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при оновленні завдання ID '{task_id}': {e}",
                         exc_info=global_settings.DEBUG)
            raise ValueError(f"Не вдалося оновити завдання через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка при оновленні завдання ID '{task_id}': {e}", exc_info=global_settings.DEBUG)
            raise

    async def delete_task(self, task_id: int, current_user_id: int) -> bool: # Змінено UUID на int
        """Видаляє завдання."""
        logger.debug(f"Спроба видалення завдання ID: {task_id} користувачем ID: {current_user_id}")

        task_to_delete = await self.task_repo.get(session=self.db_session, id=task_id) # Використання репозиторію
        if not task_to_delete:
            logger.warning(f"Завдання ID '{task_id}' не знайдено для видалення.")
            return False

        task_title_for_log = task_to_delete.title

        try:
            await self.task_repo.remove(session=self.db_session, id=task_id) # Використання репозиторію
            await self.commit()
            logger.info(
                f"Завдання ID '{task_id}' (Назва: '{task_title_for_log}') успішно видалено користувачем ID '{current_user_id}'.")
            return True
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при видаленні завдання ID '{task_id}' ({task_title_for_log}): {e}. Можливо, завдання використовується.",
                         exc_info=global_settings.DEBUG)
            raise ValueError(f"Завдання '{task_title_for_log}' використовується і не може бути видалене.")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при видаленні завдання ID '{task_id}' ({task_title_for_log}): {e}", exc_info=global_settings.DEBUG)
            raise

    async def list_tasks_for_group(
            self, group_id: int, skip: int = 0, limit: int = 100, # Змінено UUID на int
            status_code: Optional[str] = None, task_type_code: Optional[str] = None,
            assignee_user_id: Optional[int] = None,  # Змінено UUID на int
            is_recurring_filter: Optional[bool] = None,
            due_date_before: Optional[datetime] = None,
            due_date_after: Optional[datetime] = None,
            include_details: bool = False
    ) -> List[TaskResponse]:
        """Перелічує завдання для групи з розширеними фільтрами та пагінацією."""
        logger.debug(
            f"Перелік завдань для групи ID: {group_id}, статус: {status_code}, тип: {task_type_code}, деталі: {include_details}")

        query = select(Task).where(Task.group_id == group_id)

        # Налаштування завантаження зв'язків
        if include_details:
            query = query.options(
                selectinload(Task.task_type), selectinload(Task.status),
                selectinload(Task.created_by_user).options(selectinload(User.user_type)),
                selectinload(Task.updated_by_user).options(selectinload(User.user_type)),
                selectinload(Task.assignments).options(
                    selectinload(TaskAssignment.user).options(selectinload(User.user_type))
                ),
                selectinload(Task.completions), selectinload(Task.reviews)
            )
        else:  # Мінімум для TaskResponse
            query = query.options(
                selectinload(Task.task_type),
                selectinload(Task.status),
                selectinload(Task.created_by_user).options(noload("*"))
                # Тільки ID, якщо UserResponse не потрібен повністю
            )

        # Застосування фільтрів
        if status_code:
            query = query.join(Status, Task.status_id == Status.id).where(Status.code == status_code)
        if task_type_code:
            query = query.join(TaskType, Task.task_type_id == TaskType.id).where(TaskType.code == task_type_code)
        if assignee_user_id:
            # Потрібен join з TaskAssignment
            query = query.join(TaskAssignment, Task.id == TaskAssignment.task_id).where(
                TaskAssignment.user_id == assignee_user_id,
                TaskAssignment.is_active == True  # Тільки активні призначення
            )
        if is_recurring_filter is not None:
            query = query.where(Task.is_recurring == is_recurring_filter)
        if due_date_before:
            query = query.where(Task.due_date <= due_date_before)
        if due_date_after:
            query = query.where(Task.due_date >= due_date_after)

        # TODO: Додати можливість передачі параметрів сортування (sort_by, sort_order)
        query = query.order_by(Task.due_date.asc().nulls_last(), Task.created_at.desc()).offset(skip).limit(limit)

        tasks_db = (await self.db_session.execute(query)).scalars().unique().all()

        response_model = TaskDetailedResponse if include_details else TaskResponse
        response_list = [response_model.model_validate(t) for t in tasks_db]  # Pydantic v2

        logger.info(f"Отримано {len(response_list)} завдань для групи ID '{group_id}'.")
        return response_list


logger.debug(f"{TaskService.__name__} (сервіс завдань) успішно визначено.")
