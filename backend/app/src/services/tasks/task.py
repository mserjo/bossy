# backend/app/src/services/tasks/task.py
# import logging # Замінено на централізований логер
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload, noload
from sqlalchemy.exc import IntegrityError

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.tasks.task import Task  # Модель SQLAlchemy Task
from backend.app.src.models.auth.user import User
from backend.app.src.models.groups.group import Group
from backend.app.src.models.dictionaries.task_types import TaskType
from backend.app.src.models.dictionaries.statuses import Status  # Для статусу завдання

from backend.app.src.models.tasks.assignment import TaskAssignment
from backend.app.src.models.tasks.completion import TaskCompletion
from backend.app.src.models.tasks.review import TaskReview

from backend.app.src.schemas.tasks.task import (  # Схеми Pydantic Task
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskDetailedResponse  # Розширена схема відповіді
)
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings  # Для доступу до конфігурацій (наприклад, DEBUG)

# TODO: Винести коди статусів за замовчуванням (наприклад, "OPEN") в конфігурацію або константи.
DEFAULT_TASK_STATUS_CODE = "OPEN"


class TaskService(BaseService):
    """
    Сервіс для управління завданнями, включаючи CRUD-операції та обробку
    специфічної для завдань логіки, такої як повторення (хоча фактичне створення
    екземплярів для повторюваних завдань може бути делеговано сервісу планування).
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("TaskService ініціалізовано.")

    async def get_task_by_id(self, task_id: UUID, include_details: bool = False) -> Optional[
        TaskResponse]:  # Або TaskDetailedResponse
        """
        Отримує завдання за його ID.
        Опціонально може включати більше деталей, таких як виконавці, завершення, тип, статус тощо.

        :param task_id: ID завдання.
        :param include_details: Якщо True, завантажує розширену інформацію про завдання.
        :return: Pydantic схема TaskResponse або TaskDetailedResponse, або None, якщо не знайдено.
        """
        logger.debug(f"Спроба отримання завдання за ID: {task_id}, include_details: {include_details}")

        query = select(Task).where(Task.id == task_id)
        if include_details:
            query = query.options(
                selectinload(Task.group),  # Завжди завантажуємо групу, якщо є
                selectinload(Task.task_type),
                selectinload(Task.status),
                selectinload(Task.created_by_user).options(selectinload(User.user_type)),
                selectinload(Task.updated_by_user).options(selectinload(User.user_type)),
                selectinload(Task.assignments).options(
                    selectinload(TaskAssignment.user).options(selectinload(User.user_type))
                ),
                selectinload(Task.completions).options(
                    selectinload(TaskCompletion.user).options(selectinload(User.user_type))
                ),
                selectinload(Task.reviews).options(
                    selectinload(TaskReview.reviewer_user).options(selectinload(User.user_type))
                )
                # TODO: selectinload(Task.bonus_rules), якщо є прямий зв'язок
            )
        else:  # Для звичайного TaskResponse
            query = query.options(
                selectinload(Task.group).options(noload("*")),  # Тільки ID, якщо GroupResponse не потрібен повністю
                selectinload(Task.task_type),
                selectinload(Task.status),
                selectinload(Task.created_by_user).options(noload("*"))
            )

        task_db = (await self.db_session.execute(query)).scalar_one_or_none()

        if task_db:
            logger.info(f"Завдання з ID '{task_id}' знайдено.")
            response_model = TaskDetailedResponse if include_details else TaskResponse
            return response_model.model_validate(task_db)  # Pydantic v2

        logger.info(f"Завдання з ID '{task_id}' не знайдено.")
        return None

    async def create_task(self, task_create_data: TaskCreate, creator_user_id: UUID) -> TaskDetailedResponse:
        """
        Створює нове завдання.

        :param task_create_data: Дані для нового завдання.
        :param creator_user_id: ID користувача, що створює завдання.
        :return: Pydantic схема TaskDetailedResponse створеного завдання.
        :raises ValueError: Якщо пов'язані сутності (група, тип завдання, статус) не знайдено,
                            або виникає конфлікт даних. # i18n
        """
        logger.debug(f"Спроба створення нового завдання '{task_create_data.title}' користувачем ID: {creator_user_id}")

        # Перевірка існування пов'язаних сутностей
        if not await self.db_session.get(Group, task_create_data.group_id):
            # i18n
            raise ValueError(f"Групу з ID '{task_create_data.group_id}' не знайдено.")
        if not await self.db_session.get(TaskType, task_create_data.task_type_id):
            # i18n
            raise ValueError(f"Тип завдання з ID '{task_create_data.task_type_id}' не знайдено.")

        status_id_to_set = task_create_data.status_id
        if not status_id_to_set:  # Якщо статус не надано, встановлюємо за замовчуванням
            default_status_id = (await self.db_session.execute(
                select(Status.id).where(Status.code == DEFAULT_TASK_STATUS_CODE))
                                 ).scalar_one_or_none()
            if not default_status_id:
                logger.error(
                    f"Статус за замовчуванням '{DEFAULT_TASK_STATUS_CODE}' не знайдено. Створення завдання не вдалося.")
                # i18n
                raise ValueError(
                    f"Статус завдання є обов'язковим, але статус за замовчуванням '{DEFAULT_TASK_STATUS_CODE}' не знайдено.")
            status_id_to_set = default_status_id
            logger.info(
                f"Для нового завдання не надано ID статусу, використано статус за замовчуванням ID: {status_id_to_set}")
        elif not await self.db_session.get(Status, status_id_to_set):  # Якщо ID статусу надано, перевіряємо його
            # i18n
            raise ValueError(f"Статус з ID '{status_id_to_set}' не знайдено.")

        # Створення завдання
        # `created_at`, `updated_at` встановлюються автоматично моделлю
        new_task_db = Task(
            **task_create_data.model_dump(exclude={'status_id'}),  # Виключаємо status_id, бо він встановлюється окремо
            status_id=status_id_to_set,  # Встановлюємо перевірений/дефолтний status_id
            created_by_user_id=creator_user_id,
            updated_by_user_id=creator_user_id  # При створенні
        )
        self.db_session.add(new_task_db)
        try:
            await self.commit()
            # Отримуємо завдання з усіма деталями для відповіді
            created_task_detailed = await self.get_task_by_id(new_task_db.id, include_details=True)
            if not created_task_detailed:  # Малоймовірно
                # i18n
                raise RuntimeError(
                    f"Критична помилка: не вдалося отримати створене завдання ID {new_task_db.id} після коміту.")

            logger.info(
                f"Завдання '{new_task_db.title}' (ID: {new_task_db.id}) успішно створено користувачем ID '{creator_user_id}'.")
            return created_task_detailed
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при створенні завдання '{task_create_data.title}': {e}",
                         exc_info=global_settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося створити завдання через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при створенні завдання '{task_create_data.title}': {e}",
                         exc_info=global_settings.DEBUG)
            raise

    async def update_task(self, task_id: UUID, task_update_data: TaskUpdate, current_user_id: UUID) -> Optional[
        TaskDetailedResponse]:
        """Оновлює деталі завдання."""
        # Перевірка прав (наприклад, чи є користувач адміном групи або творцем завдання) - на рівні API.
        logger.debug(f"Спроба оновлення завдання ID: {task_id} користувачем ID: {current_user_id}")

        task_db = await self.db_session.get(Task, task_id)
        if not task_db:
            logger.warning(f"Завдання ID '{task_id}' не знайдено для оновлення.")
            return None

        update_data = task_update_data.model_dump(exclude_unset=True)  # Pydantic v2

        # Перевірка існування пов'язаних сутностей, якщо вони змінюються
        if 'task_type_id' in update_data and task_db.task_type_id != update_data['task_type_id']:
            if not await self.db_session.get(TaskType, update_data['task_type_id']):
                # i18n
                raise ValueError(f"Новий тип завдання ID '{update_data['task_type_id']}' не знайдено.")
        if 'status_id' in update_data and task_db.status_id != update_data['status_id']:
            if not await self.db_session.get(Status, update_data['status_id']):
                # i18n
                raise ValueError(f"Новий статус ID '{update_data['status_id']}' не знайдено.")
        # TODO: Додати перевірку group_id, якщо його дозволено змінювати (зазвичай ні).

        for field, value in update_data.items():
            setattr(task_db, field, value)

        task_db.updated_by_user_id = current_user_id
        task_db.updated_at = datetime.now(timezone.utc)  # Явне оновлення

        self.db_session.add(task_db)
        try:
            await self.commit()
            updated_task_detailed = await self.get_task_by_id(task_id, include_details=True)
            if not updated_task_detailed:  # Малоймовірно
                # i18n
                raise RuntimeError(
                    f"Критична помилка: не вдалося отримати оновлене завдання ID {task_id} після коміту.")
            logger.info(f"Завдання ID '{task_id}' успішно оновлено користувачем ID '{current_user_id}'.")
            return updated_task_detailed
        except IntegrityError as e:  # Наприклад, якщо назва завдання має бути унікальною в групі (не реалізовано)
            await self.rollback()
            logger.error(f"Помилка цілісності при оновленні завдання ID '{task_id}': {e}",
                         exc_info=global_settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося оновити завдання через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка при оновленні завдання ID '{task_id}': {e}", exc_info=global_settings.DEBUG)
            raise

    async def delete_task(self, task_id: UUID, current_user_id: UUID) -> bool:
        """Видаляє завдання."""
        # TODO: Уточнити політику видалення: що відбувається з пов'язаними TaskAssignment, TaskCompletion, TaskReview?
        #  Чи потрібне каскадне видалення, чи м'яке видалення, чи заборона видалення, якщо є залежності?
        logger.debug(f"Спроба видалення завдання ID: {task_id} користувачем ID: {current_user_id}")

        task_db = await self.db_session.get(Task, task_id)
        if not task_db:
            logger.warning(f"Завдання ID '{task_id}' не знайдено для видалення.")
            return False

        # Перевірка прав (адмін групи, творець завдання, суперюзер) - на рівні API.

        try:
            await self.db_session.delete(task_db)
            await self.commit()
            logger.info(
                f"Завдання ID '{task_id}' (Назва: '{task_db.title}') успішно видалено користувачем ID '{current_user_id}'.")
            return True
        except IntegrityError as e:  # Якщо є залежності, що блокують видалення (FK constraints)
            await self.rollback()
            logger.error(f"Помилка цілісності '{task_id}': {e}. Можливо, завдання використовується.",
                         exc_info=global_settings.DEBUG)
            # i18n
            raise ValueError(f"Завдання '{task_db.title}' використовується і не може бути видалене.")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка '{task_id}': {e}", exc_info=global_settings.DEBUG)
            raise

    async def list_tasks_for_group(
            self, group_id: UUID, skip: int = 0, limit: int = 100,
            status_code: Optional[str] = None, task_type_code: Optional[str] = None,
            assignee_user_id: Optional[UUID] = None,  # Фільтр за призначеним користувачем
            is_recurring_filter: Optional[bool] = None,  # Фільтр за повторюваністю
            due_date_before: Optional[datetime] = None,  # Фільтр за терміном виконання (до)
            due_date_after: Optional[datetime] = None,  # Фільтр за терміном виконання (після)
            include_details: bool = False
    ) -> List[TaskResponse]:  # Або List[TaskDetailedResponse]
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
