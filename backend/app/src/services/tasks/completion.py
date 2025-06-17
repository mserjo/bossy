# backend/app/src/services/tasks/completion.py
# -*- coding: utf-8 -*-
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, noload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.tasks.completion import TaskCompletion  # Модель SQLAlchemy TaskCompletion
from backend.app.src.models.tasks.task import Task  # Для контексту завдання
from backend.app.src.models.auth.user import User  # Для контексту користувача
from backend.app.src.models.tasks.assignment import TaskAssignment  # Для перевірки, чи користувач призначений
from backend.app.src.models.dictionaries.task_types import TaskType  # Для перевірки `requires_approval`

from backend.app.src.schemas.tasks.completion import (  # Схеми Pydantic
    TaskCompletionCreateRequest,  # Користувач позначає завдання як виконане
    TaskCompletionAdminUpdateRequest,  # Адмін ухвалює/відхиляє
    TaskCompletionResponse
)
from backend.app.src.config import settings as global_settings  # Для доступу до конфігурацій (наприклад, DEBUG)
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# TODO: Винести статуси завершення до спільного файлу констант або Enum,
#  наприклад, backend/app/src/core/enums.py
COMPLETION_STATUS_PENDING_APPROVAL = "PENDING_APPROVAL"  # Очікує на ухвалення
COMPLETION_STATUS_APPROVED = "APPROVED"  # Ухвалено
COMPLETION_STATUS_REJECTED = "REJECTED"  # Відхилено
COMPLETION_STATUS_COMPLETED = "COMPLETED"  # Завершено (для завдань, що не потребують ухвалення)


class TaskCompletionService(BaseService):
    """
    Сервіс для управління життєвим циклом завершень завдань (або подій).
    Обробляє позначення завдань користувачами як виконаних, ухвалення/відхилення адміністраторами
    та потенційно ініціює нарахування балів.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        # TODO: Ініціалізувати NotificationService та BonusCalculationService (або UserAccountService)
        # self.notification_service = NotificationService(db_session)
        # self.bonus_service = BonusCalculationService(db_session)
        logger.info("TaskCompletionService ініціалізовано.")

    async def _get_orm_completion_with_relations(self, completion_id: UUID) -> Optional[TaskCompletion]:
        """Внутрішній метод для отримання ORM моделі TaskCompletion з усіма зв'язками."""
        stmt = select(TaskCompletion).options(
            selectinload(TaskCompletion.user).options(selectinload(User.user_type)),
            selectinload(TaskCompletion.task).options(
                selectinload(Task.task_type),
                selectinload(Task.status),  # Статус самого завдання
                selectinload(Task.group)
            ),
            selectinload(TaskCompletion.reviewed_by_user).options(selectinload(User.user_type))
        ).where(TaskCompletion.id == completion_id)
        return (await self.db_session.execute(stmt)).scalar_one_or_none()

    async def mark_task_as_completed_by_user(
            self,
            task_id: UUID,
            user_id: UUID,
            completion_data: TaskCompletionCreateRequest  # Містить, наприклад, user_notes, submitted_file_id
    ) -> TaskCompletionResponse:
        """
        Позначає завдання як виконане користувачем.
        Статус може бути 'PENDING_APPROVAL' або 'COMPLETED' залежно від налаштувань типу завдання.

        :param task_id: ID завдання.
        :param user_id: ID користувача, що виконав завдання.
        :param completion_data: Дані від користувача про виконання.
        :return: Pydantic схема TaskCompletionResponse.
        :raises ValueError: Якщо завдання/користувача не знайдено, або завдання вже виконано (якщо не повторюване). # i18n
        """
        logger.debug(f"Користувач ID '{user_id}' намагається позначити завдання ID '{task_id}' як виконане.")

        task = await self.db_session.get(Task, task_id, options=[selectinload(Task.task_type)])
        if not task: raise ValueError(f"Завдання з ID '{task_id}' не знайдено.")  # i18n

        if not await self.db_session.get(User, user_id):
            raise ValueError(f"Користувача з ID '{user_id}' не знайдено.")  # i18n

        # TODO: Узгодити з `technical_task.txt`: чи обов'язково бути призначеним на завдання для його виконання?
        #  Якщо так, додати перевірку активного TaskAssignment.
        # assignment = (await self.db_session.execute(
        #     select(TaskAssignment.id).where(
        #         TaskAssignment.task_id == task_id, TaskAssignment.user_id == user_id, TaskAssignment.is_active == True
        #     )
        # )).scalar_one_or_none()
        # if not assignment:
        #     raise ValueError(f"Користувач ID '{user_id}' не призначений на завдання ID '{task_id}'.") # i18n

        # Перевірка, чи завдання вже було виконано цим користувачем (і не є повторюваним)
        # Дозволяємо нове виконання, якщо попереднє було відхилено (REJECTED).
        if not getattr(task, 'is_repeatable', False):  # Припускаємо, що модель Task має поле is_repeatable
            existing_completion = (await self.db_session.execute(
                select(TaskCompletion.id).where(
                    TaskCompletion.task_id == task_id,
                    TaskCompletion.user_id == user_id,
                    TaskCompletion.status != COMPLETION_STATUS_REJECTED  # Дозволяє повторно подати після відхилення
                )
            )).scalar_one_or_none()
            if existing_completion:
                msg = f"Завдання ID '{task_id}' вже було виконано Вами і не є повторюваним."  # i18n
                logger.warning(f"{msg} (Користувач ID: {user_id})")
                raise ValueError(msg)

        # Визначення початкового статусу на основі типу завдання
        # Припускаємо, що модель TaskType має поле requires_approval: bool
        requires_approval = getattr(task.task_type, 'requires_approval', True) if task.task_type else True
        initial_status = COMPLETION_STATUS_PENDING_APPROVAL if requires_approval else COMPLETION_STATUS_COMPLETED

        # `completed_at` - час, коли користувач позначив завдання як виконане
        # `created_at`, `updated_at` для TaskCompletion встановлюються автоматично
        new_completion_db = TaskCompletion(
            task_id=task_id,
            user_id=user_id,
            status=initial_status,
            completed_at=datetime.now(timezone.utc),
            user_notes=completion_data.user_notes,
            submitted_file_id=completion_data.submitted_file_id
        )
        self.db_session.add(new_completion_db)
        try:
            await self.commit()
            refreshed_completion = await self._get_orm_completion_with_relations(new_completion_db.id)
            if not refreshed_completion: raise RuntimeError("Не вдалося отримати створене виконання завдання.")  # i18n
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності '{task_id}' для '{user_id}': {e}", exc_info=global_settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося позначити завдання як виконане через конфлікт даних: {e}")

        logger.info(
            f"Завдання ID '{task_id}' позначено як '{initial_status}' користувачем ID '{user_id}'. ID Завершення: {refreshed_completion.id}")

        # TODO: Ініціювати сповіщення та нарахування бонусів (якщо статус COMPLETED)
        # if initial_status == COMPLETION_STATUS_COMPLETED and task.points_reward > 0:
        #     # await self.bonus_service.award_points_for_task_completion(refreshed_completion)
        #     logger.info(f"[ЗАГЛУШКА] Нарахування {task.points_reward} балів за завдання ID {task_id} для {user_id}.")
        # if initial_status == COMPLETION_STATUS_PENDING_APPROVAL:
        #     # await self.notification_service.notify_group_admins_task_pending_approval(task.group_id, task_id, user_id)
        #     logger.info(f"[ЗАГЛУШКА] Сповіщення адмінів групи {task.group_id} про завдання {task_id}, що очікує на ухвалення.")

        return TaskCompletionResponse.model_validate(refreshed_completion)  # Pydantic v2

    async def update_task_completion_status(
            self, completion_id: UUID, admin_update_data: TaskCompletionAdminUpdateRequest, admin_user_id: UUID
    ) -> TaskCompletionResponse:
        """
        Оновлює статус завершення завдання (зазвичай адміністратором).

        :param completion_id: ID запису завершення завдання.
        :param admin_update_data: Дані оновлення від адміністратора (новий статус, коментарі).
        :param admin_user_id: ID адміністратора, що виконує дію.
        :return: Pydantic схема оновленого TaskCompletionResponse.
        :raises ValueError: Якщо запис не знайдено, або статус не дозволяє оновлення. # i18n
        """
        logger.debug(
            f"Адмін ID '{admin_user_id}' намагається оновити статус завершення ID '{completion_id}' на '{admin_update_data.status}'.")

        completion_db = await self._get_orm_completion_with_relations(completion_id)
        if not completion_db:
            raise ValueError(f"Запис завершення завдання з ID '{completion_id}' не знайдено.")  # i18n

        if completion_db.status != COMPLETION_STATUS_PENDING_APPROVAL:
            msg = f"Завершення ID '{completion_id}' не очікує на ухвалення (поточний статус: {completion_db.status})."  # i18n
            logger.warning(msg)
            raise ValueError(msg)

        # Перевірка, чи новий статус є допустимим (APPROVED або REJECTED)
        valid_new_statuses = {COMPLETION_STATUS_APPROVED, COMPLETION_STATUS_REJECTED}
        if admin_update_data.status not in valid_new_statuses:
            # i18n
            raise ValueError(
                f"Неприпустимий новий статус '{admin_update_data.status}'. Дозволені: {valid_new_statuses}.")

        original_status = completion_db.status
        completion_db.status = admin_update_data.status
        completion_db.admin_notes = admin_update_data.admin_notes
        completion_db.reviewed_by_user_id = admin_user_id
        completion_db.reviewed_at = datetime.now(timezone.utc)
        # `updated_at` оновлюється автоматично

        self.db_session.add(completion_db)
        await self.commit()
        # Оновлюємо для відповіді, оскільки зв'язки вже були завантажені _get_orm_completion_with_relations
        await self.db_session.refresh(completion_db)

        logger.info(
            f"Статус завершення ID '{completion_id}' оновлено з '{original_status}' на '{completion_db.status}' адміном ID '{admin_user_id}'.")

        # TODO: Ініціювати сповіщення користувачу про результат перевірки.
        # await self.notification_service.notify_user_task_completion_reviewed(completion_db)

        # TODO: Якщо статус APPROVED, ініціювати нарахування бонусів.
        # if completion_db.status == COMPLETION_STATUS_APPROVED and completion_db.task and completion_db.task.points_reward > 0:
        #     # await self.bonus_service.award_points_for_task_completion(completion_db)
        #     logger.info(f"[ЗАГЛУШКА] Нарахування {completion_db.task.points_reward} балів за завдання ID {completion_db.task_id} для {completion_db.user_id}.")

        # TODO: Якщо тип завдання 'EXECUTE_ONCE_CLOSE' і статус APPROVED, оновити статус основного завдання Task.
        # if completion_db.status == COMPLETION_STATUS_APPROVED and \
        #    getattr(completion_db.task.task_type, 'execution_logic', None) == 'EXECUTE_ONCE_CLOSE':
        #    # task_service = TaskService(self.db_session)
        #    # await task_service.update_task_status(completion_db.task_id, "COMPLETED", admin_user_id)
        #    logger.info(f"[ЗАГЛУШКА] Завдання ID {completion_db.task_id} має бути закрито, оскільки воно типу 'EXECUTE_ONCE_CLOSE'.")

        return TaskCompletionResponse.model_validate(completion_db)  # Pydantic v2

    async def list_completions_for_task(
            self, task_id: UUID, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[TaskCompletionResponse]:
        """Перелічує всі завершення для конкретного завдання."""
        logger.debug(
            f"Перелік завершень для завдання ID: {task_id}, статус: {status}, пропустити={skip}, ліміт={limit}")

        stmt = select(TaskCompletion).options(
            selectinload(TaskCompletion.user).options(selectinload(User.user_type)),
            selectinload(TaskCompletion.task).options(noload("*")),  # Завдання вже відоме
            selectinload(TaskCompletion.reviewed_by_user).options(selectinload(User.user_type))
        ).where(TaskCompletion.task_id == task_id)

        if status:
            stmt = stmt.where(TaskCompletion.status == status)

        stmt = stmt.order_by(TaskCompletion.completed_at.desc()).offset(skip).limit(limit)
        completions_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [TaskCompletionResponse.model_validate(c) for c in completions_db]  # Pydantic v2
        logger.info(f"Отримано {len(response_list)} завершень для завдання ID '{task_id}'.")
        return response_list

    async def list_completions_by_user(
            self, user_id: UUID, skip: int = 0, limit: int = 100,
            status: Optional[str] = None, group_id: Optional[UUID] = None
    ) -> List[TaskCompletionResponse]:
        """Перелічує всі завершення, зроблені конкретним користувачем."""
        logger.debug(
            f"Перелік завершень користувачем ID: {user_id}, статус: {status}, група: {group_id}, пропустити={skip}, ліміт={limit}")

        stmt = select(TaskCompletion).options(
            selectinload(TaskCompletion.user).options(noload("*")),  # Користувач вже відомий
            selectinload(TaskCompletion.task).options(
                selectinload(Task.task_type), selectinload(Task.status), selectinload(Task.group)
            ),
            selectinload(TaskCompletion.reviewed_by_user).options(selectinload(User.user_type))
        ).where(TaskCompletion.user_id == user_id)

        if status:
            stmt = stmt.where(TaskCompletion.status == status)
        if group_id:  # Фільтр за групою завдання
            stmt = stmt.join(Task, TaskCompletion.task_id == Task.id).where(Task.group_id == group_id)

        stmt = stmt.order_by(TaskCompletion.completed_at.desc()).offset(skip).limit(limit)
        completions_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [TaskCompletionResponse.model_validate(c) for c in completions_db]  # Pydantic v2
        logger.info(f"Отримано {len(response_list)} завершень користувачем ID '{user_id}'.")
        return response_list

    async def get_completion_details(self, completion_id: UUID, user_id_check: Optional[UUID] = None) -> Optional[
        TaskCompletionResponse]:
        """
        Отримує деталі конкретного завершення завдання за його ID.
        Якщо надано `user_id_check`, перевіряє, чи належить запис цьому користувачеві.
        """
        logger.debug(f"Отримання деталей для завершення ID {completion_id}" + (
            f" для користувача {user_id_check}" if user_id_check else ""))

        completion_db = await self._get_orm_completion_with_relations(completion_id)
        if not completion_db:
            logger.info(f"Завершення завдання з ID {completion_id} не знайдено.")
            return None

        if user_id_check and completion_db.user_id != user_id_check:
            logger.warning(
                f"Спроба доступу до завершення ID {completion_id} користувачем {user_id_check}, але воно належить {completion_db.user_id}.")
            # i18n
            raise PermissionError("Ви не маєте дозволу на перегляд цього запису про виконання.")

        return TaskCompletionResponse.model_validate(completion_db)  # Pydantic v2


logger.debug(f"{TaskCompletionService.__name__} (сервіс завершення завдань) успішно визначено.")
