# backend/app/src/services/tasks/assignment.py
# import logging # Замінено на централізований логер
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload, noload
from sqlalchemy.exc import IntegrityError

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.tasks.assignment import TaskAssignment  # Модель SQLAlchemy TaskAssignment
from backend.app.src.models.tasks.task import Task  # Для контексту завдання
# from backend.app.src.models.tasks.event import Event # Для контексту події (якщо призначення можливі і для подій)
from backend.app.src.models.auth.user import User  # Для контексту користувача
from backend.app.src.models.dictionaries.task_types import TaskType  # Для завантаження типу завдання
from backend.app.src.models.dictionaries.statuses import Status  # Для завантаження статусу завдання
from backend.app.src.models.groups.group import Group  # Для завантаження групи завдання

from backend.app.src.schemas.tasks.assignment import (  # Схеми Pydantic
    # TaskAssignmentCreate, # Не використовується прямо як тип параметра, але для узгодженості
    # TaskAssignmentUpdate, # Призначення зазвичай незмінні; зміни = нове призначення або скасування/перепризначення
    TaskAssignmentResponse
)
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings  # Для доступу до конфігурацій (наприклад, DEBUG)


class TaskAssignmentService(BaseService):
    """
    Сервіс для управління призначеннями завдань (або подій) користувачам.
    Обробляє створення, отримання та видалення (деактивацію) призначень.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("TaskAssignmentService ініціалізовано.")

    async def _get_orm_assignment_with_relations(self, assignment_id: UUID) -> Optional[TaskAssignment]:
        """Внутрішній метод для отримання ORM моделі TaskAssignment з усіма зв'язками."""
        stmt = select(TaskAssignment).options(
            selectinload(TaskAssignment.user).options(selectinload(User.user_type)),
            selectinload(TaskAssignment.task).options(
                selectinload(Task.task_type),
                selectinload(Task.status),
                selectinload(Task.group),
                selectinload(Task.created_by_user).options(noload("*"))  # Тільки ID, якщо не потрібен повний User
            ),
            selectinload(TaskAssignment.assigned_by).options(selectinload(User.user_type))
        ).where(TaskAssignment.id == assignment_id)
        return (await self.db_session.execute(stmt)).scalar_one_or_none()

    async def assign_task_to_user(
            self,
            task_id: UUID,
            user_id: UUID,
            assigned_by_user_id: Optional[UUID] = None
            # TODO: Якщо сервіс має обробляти призначення і для Event, додати параметр item_type: str ('task'/'event')
            #  та відповідно event_id: Optional[UUID]. Модель TaskAssignment також має це підтримувати.
    ) -> TaskAssignmentResponse:
        """
        Призначає завдання користувачеві.
        Запобігає дублюванню активних призначень. Реактивує неактивні призначення.

        :param task_id: ID завдання.
        :param user_id: ID користувача, якому призначається завдання.
        :param assigned_by_user_id: ID користувача, який виконав призначення (для аудиту).
        :return: Pydantic схема TaskAssignmentResponse створеного або оновленого призначення.
        :raises ValueError: Якщо завдання або користувача не знайдено, або виникає конфлікт даних. # i18n
        """
        logger.debug(f"Спроба призначення завдання ID '{task_id}' користувачу ID '{user_id}'.")

        # Перевірка існування завдання та користувача
        task = await self.db_session.get(Task, task_id)
        if not task: raise ValueError(f"Завдання з ID '{task_id}' не знайдено.")  # i18n

        user = await self.db_session.get(User, user_id)
        if not user: raise ValueError(f"Користувача з ID '{user_id}' не знайдено.")  # i18n

        # Пошук існуючого призначення (активного або неактивного)
        existing_assignment_stmt = select(TaskAssignment).where(
            TaskAssignment.task_id == task_id,
            TaskAssignment.user_id == user_id
        )
        assignment_db = (await self.db_session.execute(existing_assignment_stmt)).scalar_one_or_none()

        current_time = datetime.now(timezone.utc)
        if assignment_db:  # Якщо запис призначення існує
            if assignment_db.is_active:
                logger.info(
                    f"Користувач ID '{user_id}' вже активно призначений на завдання ID '{task_id}'. Повернення існуючого призначення.")
                # Завантажуємо зв'язки для повної відповіді
                full_assignment_db = await self._get_orm_assignment_with_relations(assignment_db.id)
                return TaskAssignmentResponse.model_validate(full_assignment_db or assignment_db)  # Pydantic v2
            else:  # Неактивне, реактивуємо
                logger.info(
                    f"Реактивація існуючого неактивного призначення для користувача ID '{user_id}' на завдання ID '{task_id}'.")
                assignment_db.is_active = True
                assignment_db.assigned_at = current_time  # Оновлюємо час "призначення" / реактивації
                if hasattr(assignment_db, 'assigned_by_user_id'):  # Перевірка наявності поля
                    assignment_db.assigned_by_user_id = assigned_by_user_id
                # `updated_at` оновлюється автоматично моделлю
        else:  # Немає існуючого призначення, створюємо нове
            logger.info(f"Створення нового призначення завдання ID '{task_id}' користувачу ID '{user_id}'.")
            create_data = {
                "task_id": task_id,
                "user_id": user_id,
                "is_active": True,
                "assigned_at": current_time
            }
            if hasattr(TaskAssignment, 'assigned_by_user_id'):
                create_data['assigned_by_user_id'] = assigned_by_user_id

            assignment_db = TaskAssignment(**create_data)
            self.db_session.add(assignment_db)

        try:
            await self.commit()
            # Оновлюємо для завантаження всіх зв'язків для відповіді
            refreshed_assignment = await self._get_orm_assignment_with_relations(assignment_db.id)
            if not refreshed_assignment:  # Малоймовірно
                # i18n
                raise RuntimeError("Критична помилка: не вдалося отримати запис призначення після збереження.")
        except IntegrityError as e:  # На випадок унікальних обмежень (task_id, user_id), якщо логіка вище дала збій
            await self.rollback()
            logger.error(f"Помилка цілісності '{task_id}' для '{user_id}': {e}", exc_info=global_settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося призначити завдання через конфлікт даних: {e}")

        logger.info(
            f"Успішно призначено завдання ID '{task_id}' користувачу ID '{user_id}'. ID Призначення: {refreshed_assignment.id}")
        return TaskAssignmentResponse.model_validate(refreshed_assignment)  # Pydantic v2

    async def unassign_task_from_user(
            self, task_id: UUID, user_id: UUID, unassigned_by_user_id: Optional[UUID] = None
    ) -> bool:
        """
        Скасовує призначення завдання користувачеві (деактивує запис призначення).

        :param task_id: ID завдання.
        :param user_id: ID користувача.
        :param unassigned_by_user_id: ID користувача, який виконав скасування (для аудиту).
        :return: True, якщо скасування успішне, False - якщо активне призначення не знайдено.
        """
        logger.debug(f"Спроба скасування призначення завдання ID '{task_id}' для користувача ID '{user_id}'.")

        assignment_db = (await self.db_session.execute(
            select(TaskAssignment).where(
                TaskAssignment.task_id == task_id,
                TaskAssignment.user_id == user_id,
                TaskAssignment.is_active == True  # Шукаємо тільки активне призначення
            )
        )).scalar_one_or_none()

        if not assignment_db:
            logger.warning(
                f"Активне призначення для користувача ID '{user_id}' на завдання ID '{task_id}' не знайдено. Скасування неможливе.")
            return False

        assignment_db.is_active = False
        # TODO: Перевірити, чи модель TaskAssignment має поля `unassigned_at`, `unassigned_by_user_id`
        #  та встановити їх, якщо є. Поки що припускаємо, що `updated_at` оновлюється автоматично.
        if hasattr(assignment_db, 'unassigned_at'):
            setattr(assignment_db, 'unassigned_at', datetime.now(timezone.utc))
        if hasattr(assignment_db, 'unassigned_by_user_id') and unassigned_by_user_id:
            setattr(assignment_db, 'unassigned_by_user_id', unassigned_by_user_id)

        self.db_session.add(assignment_db)
        await self.commit()

        logger.info(f"Користувача ID '{user_id}' успішно відкріплено (деактивовано) від завдання ID '{task_id}'.")
        return True

    async def list_assignments_for_task(
            self, task_id: UUID, skip: int = 0, limit: int = 100, is_active: Optional[bool] = True
    ) -> List[TaskAssignmentResponse]:
        """Перелічує призначення для конкретного завдання."""
        logger.debug(
            f"Перелік призначень для завдання ID '{task_id}', активні: {is_active}, пропустити={skip}, ліміт={limit}")

        stmt = select(TaskAssignment).options(
            selectinload(TaskAssignment.user).options(selectinload(User.user_type)),
            selectinload(TaskAssignment.task).options(noload("*")),  # Завдання вже відоме (task_id)
            selectinload(TaskAssignment.assigned_by).options(noload("*"))  # Тільки ID, якщо не потрібен повний User
        ).where(TaskAssignment.task_id == task_id)

        if is_active is not None:
            stmt = stmt.where(TaskAssignment.is_active == is_active)

        # Приєднуємо User для сортування за ім'ям користувача
        stmt = stmt.join(User, TaskAssignment.user_id == User.id).order_by(User.username).offset(skip).limit(limit)
        assignments_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [TaskAssignmentResponse.model_validate(a) for a in assignments_db]  # Pydantic v2
        logger.info(f"Отримано {len(response_list)} призначень для завдання ID '{task_id}'.")
        return response_list

    async def list_tasks_for_user(
            self, user_id: UUID, skip: int = 0, limit: int = 100,
            is_active_assignment: Optional[bool] = True,
            # TODO: Додати фільтри за статусом завдання, типом завдання тощо, якщо потрібно
    ) -> List[TaskAssignmentResponse]:  # Повертає список призначень, що містять деталі завдання
        """Перелічує завдання, призначені вказаному користувачеві."""
        logger.debug(
            f"Перелік завдань, призначених користувачу ID: {user_id}, активне призначення: {is_active_assignment}, пропустити={skip}, ліміт={limit}")

        stmt = select(TaskAssignment).options(
            selectinload(TaskAssignment.user).options(noload("*")),  # Користувач вже відомий (user_id)
            selectinload(TaskAssignment.task).options(  # Завантажуємо деталі завдання
                selectinload(Task.task_type),
                selectinload(Task.status),
                selectinload(Task.group).options(noload("*")),  # Група завдання (тільки ID)
                selectinload(Task.created_by_user).options(noload("*"))  # Творець завдання (тільки ID)
            ),
            selectinload(TaskAssignment.assigned_by).options(noload("*"))
        ).where(TaskAssignment.user_id == user_id)

        if is_active_assignment is not None:
            stmt = stmt.where(TaskAssignment.is_active == is_active_assignment)

        # Сортування за терміном виконання завдання (спочатку ті, що найближче), потім за датою створення завдання
        # isouter=True не потрібен, якщо FK гарантує існування Task
        stmt = stmt.join(Task, TaskAssignment.task_id == Task.id).order_by(
            Task.due_date.asc().nulls_last(), Task.created_at.desc()
        ).offset(skip).limit(limit)

        assignments_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [TaskAssignmentResponse.model_validate(a) for a in assignments_db]  # Pydantic v2
        logger.info(f"Отримано {len(response_list)} призначених завдань для користувача ID '{user_id}'.")
        return response_list

    async def get_assignment_details(self, assignment_id: UUID) -> Optional[TaskAssignmentResponse]:
        """Отримує деталі конкретного призначення за його ID."""
        logger.debug(f"Отримання деталей для призначення ID {assignment_id}")

        assignment_db = await self._get_orm_assignment_with_relations(assignment_id)
        if not assignment_db:
            logger.info(f"Призначення з ID {assignment_id} не знайдено.")
            return None

        return TaskAssignmentResponse.model_validate(assignment_db)  # Pydantic v2


logger.debug(f"{TaskAssignmentService.__name__} (сервіс призначень завдань) успішно визначено.")
