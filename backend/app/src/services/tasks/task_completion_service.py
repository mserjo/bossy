# backend/app/src/services/tasks/task_completion_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `TaskCompletionService` для управління процесом виконання завдань.
"""
from typing import List, Optional, Union, Dict, Any
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.tasks.completion import TaskCompletionModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.models.tasks.task import TaskModel # Для отримання деталей завдання
from backend.app.src.schemas.tasks.completion import (
    TaskCompletionCreateSchema, TaskCompletionUpdateSchema, TaskCompletionSchema,
    TaskCompletionStartSchema, TaskCompletionSubmitSchema, TaskCompletionReviewSchema
)
from backend.app.src.repositories.tasks.completion import TaskCompletionRepository, task_completion_repository
from backend.app.src.repositories.tasks.task import task_repository
from backend.app.src.repositories.dictionaries.status import status_repository
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import (
    TASK_STATUS_IN_PROGRESS_CODE, TASK_STATUS_PENDING_REVIEW_CODE,
    TASK_STATUS_COMPLETED_CODE, TASK_STATUS_REJECTED_CODE, TASK_STATUS_CANCELLED_CODE,
    USER_TYPE_SUPERADMIN, TRANSACTION_TYPE_TASK_REWARD, TRANSACTION_TYPE_TASK_PENALTY
)
# from backend.app.src.services.groups.group_membership_service import group_membership_service
# from backend.app.src.services.bonuses.transaction_service import transaction_service # Для нарахування бонусів

class TaskCompletionService(BaseService[TaskCompletionRepository]):
    """
    Сервіс для управління виконанням завдань.
    """

    async def get_completion_by_id(self, db: AsyncSession, completion_id: uuid.UUID) -> TaskCompletionModel:
        completion = await self.repository.get(db, id=completion_id)
        if not completion:
            raise NotFoundException(f"Запис про виконання з ID {completion_id} не знайдено.")
        return completion

    async def start_task_completion(
        self, db: AsyncSession, *, task_id: uuid.UUID, current_user: UserModel,
        start_data: Optional[TaskCompletionStartSchema] = None # Може містити `started_at`
    ) -> TaskCompletionModel:
        """
        Починає виконання завдання користувачем (або командою, якщо завдання командне).
        Створює запис TaskCompletion зі статусом "в роботі".
        """
        task = await task_repository.get_task_with_details(db, task_id=task_id)
        if not task:
            raise NotFoundException(f"Завдання з ID {task_id} не знайдено.")

        # TODO: Перевірка, чи може користувач взяти це завдання в роботу:
        # - Чи є він членом групи завдання?
        # - Чи призначене завдання йому/його команді (якщо не відкрите для всіх)?
        # - Чи не виконує він його вже?
        # - Чи дозволяє завдання кілька виконавців, якщо воно вже кимось виконується?
        # - Чи активне завдання (статус, is_deleted)?

        existing_completion = await self.repository.get_by_task_and_user(db, task_id=task_id, user_id=current_user.id)
        if existing_completion and existing_completion.status.code in [TASK_STATUS_IN_PROGRESS_CODE, TASK_STATUS_PENDING_REVIEW_CODE]:
            raise BadRequestException("Ви вже виконуєте це завдання або воно очікує перевірки.")

        # TODO: Логіка для командних завдань (визначення team_id)

        status_in_progress = await status_repository.get_by_code(db, code=TASK_STATUS_IN_PROGRESS_CODE)
        if not status_in_progress:
            raise BadRequestException(f"Статус '{TASK_STATUS_IN_PROGRESS_CODE}' не знайдено.")

        return await self.repository.create_completion_entry(
            db, task_id=task_id, user_id=current_user.id, status_id=status_in_progress.id, start_data=start_data
        )

    async def submit_task_for_review(
        self, db: AsyncSession, *, completion_id: uuid.UUID, obj_in: TaskCompletionSubmitSchema, current_user: UserModel
    ) -> TaskCompletionModel:
        """
        Подає виконане завдання на перевірку.
        Оновлює запис TaskCompletion: статус на "на перевірці", додає нотатки, файли.
        """
        db_completion = await self.get_completion_by_id(db, completion_id=completion_id)

        if db_completion.user_id != current_user.id: # Або якщо це командне завдання, перевірка членства в команді
            raise ForbiddenException("Ви не можете подати на перевірку завдання, яке виконує інший користувач.")
        if db_completion.status.code != TASK_STATUS_IN_PROGRESS_CODE:
            raise BadRequestException(f"Завдання не знаходиться в статусі '{TASK_STATUS_IN_PROGRESS_CODE}'. Поточний статус: {db_completion.status.code}")

        status_pending_review = await status_repository.get_by_code(db, code=TASK_STATUS_PENDING_REVIEW_CODE)
        if not status_pending_review:
            raise BadRequestException(f"Статус '{TASK_STATUS_PENDING_REVIEW_CODE}' не знайдено.")

        update_data = obj_in.model_dump(exclude_unset=True)
        update_data["status_id"] = status_pending_review.id
        # `submitted_for_review_at` встановлюється в схемі або тут
        if "submitted_for_review_at" not in update_data:
            update_data["submitted_for_review_at"] = datetime.utcnow()

        # TODO: Обробка `attachments` - збереження файлів, отримання їх ID.
        # Поки що просто зберігаємо передані метадані.

        return await self.repository.update(db, db_obj=db_completion, obj_in=update_data)

    async def review_task_completion(
        self, db: AsyncSession, *, completion_id: uuid.UUID, obj_in: TaskCompletionReviewSchema, current_user: UserModel # Адмін
    ) -> TaskCompletionModel:
        """
        Перевіряє виконання завдання адміністратором.
        Оновлює статус ("підтверджено", "відхилено"), додає коментарі, нараховує/списує бонуси.
        """
        db_completion = await self.get_completion_by_id(db, completion_id=completion_id)
        task = await task_repository.get_task_with_details(db, task_id=db_completion.task_id) # Потрібні деталі завдання для бонусів
        if not task: # Малоймовірно, якщо є completion
            raise NotFoundException("Пов'язане завдання не знайдено.")

        # Перевірка прав (адмін групи завдання або superuser)
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=task.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи може перевіряти виконання завдань.")

        if db_completion.status.code != TASK_STATUS_PENDING_REVIEW_CODE:
            raise BadRequestException(f"Завдання не знаходиться в статусі '{TASK_STATUS_PENDING_REVIEW_CODE}' для перевірки.")

        new_status = await status_repository.get(db, id=obj_in.new_status_id)
        if not new_status:
            raise BadRequestException(f"Новий статус з ID {obj_in.new_status_id} не знайдено.")

        if new_status.code not in [TASK_STATUS_COMPLETED_CODE, TASK_STATUS_REJECTED_CODE, TASK_STATUS_CANCELLED_CODE]: # TODO: TASK_STATUS_BLOCKED_CODE?
            raise BadRequestException(f"Недопустимий статус для результату перевірки: {new_status.code}.")

        if new_status.code == TASK_STATUS_REJECTED_CODE and not obj_in.review_notes:
            raise BadRequestException("Коментар (review_notes) є обов'язковим при відхиленні завдання.")

        update_data = obj_in.model_dump(exclude_unset=True)
        update_data["status_id"] = new_status.id
        update_data["reviewed_by_user_id"] = current_user.id
        if "reviewed_at" not in update_data: # reviewed_at з схеми, якщо передано
            update_data["reviewed_at"] = datetime.utcnow()

        if new_status.code == TASK_STATUS_COMPLETED_CODE:
            update_data["completed_at"] = datetime.utcnow()
            # Нарахування бонусів / списання штрафів
            bonus_to_award = obj_in.bonus_points_awarded if obj_in.bonus_points_awarded is not None else task.bonus_points
            penalty_to_apply = obj_in.penalty_points_applied if obj_in.penalty_points_applied is not None else task.penalty_points # Зазвичай штраф за невиконання, а не за відхилене виконання

            if bonus_to_award is not None and bonus_to_award > 0:
                update_data["bonus_points_awarded"] = bonus_to_award
                # TODO: Створити транзакцію для нарахування бонусів
                # await transaction_service.create_task_reward_transaction(db, user_id=db_completion.user_id, task_id=task.id, amount=bonus_to_award, group_id=task.group_id)
                self.logger.info(f"Нараховано {bonus_to_award} бонусів користувачу {db_completion.user_id} за завдання {task.id}")

            # Якщо завдання було обов'язковим і не виконано вчасно, а потім відхилено - чи є штраф?
            # Поточна логіка: штраф (penalty_points в TaskModel) - за невиконання.
            # Тут ми розглядаємо підтвердження або відхилення поданого виконання.
            # Якщо відхилено, бонуси не нараховуються. Чи є штраф за погане виконання - залежить від логіки.
            # Поки що `penalty_points_applied` тут не використовується для створення транзакції.

        updated_completion = await self.repository.update(db, db_obj=db_completion, obj_in=update_data)

        # TODO: Відправити сповіщення користувачу про результат перевірки.
        return updated_completion

    async def cancel_task_completion(
        self, db: AsyncSession, *, completion_id: uuid.UUID, current_user: UserModel
    ) -> TaskCompletionModel:
        """Скасовує виконання завдання (або користувачем, або адміном)."""
        db_completion = await self.get_completion_by_id(db, completion_id=completion_id)
        task = await task_repository.get(db, id=db_completion.task_id)
        if not task: raise NotFoundException("Пов'язане завдання не знайдено.")

        # Перевірка прав (виконавець, адмін групи, superuser)
        is_admin = await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=task.group_id) # type: ignore
        if not (db_completion.user_id == current_user.id or is_admin or current_user.user_type_code == USER_TYPE_SUPERADMIN):
            raise ForbiddenException("Ви не можете скасувати це виконання завдання.")

        if db_completion.status.code in [TASK_STATUS_COMPLETED_CODE, TASK_STATUS_REJECTED_CODE, TASK_STATUS_CANCELLED_CODE]:
            raise BadRequestException(f"Неможливо скасувати завдання зі статусом '{db_completion.status.code}'.")

        status_cancelled = await status_repository.get_by_code(db, code=TASK_STATUS_CANCELLED_CODE)
        if not status_cancelled:
            raise BadRequestException(f"Статус '{TASK_STATUS_CANCELLED_CODE}' не знайдено.")

        update_data = {"status_id": status_cancelled.id}
        if db_completion.status.code == TASK_STATUS_PENDING_REVIEW_CODE and current_user.id != db_completion.user_id: # Якщо адмін скасовує подане на перевірку
            update_data["reviewed_by_user_id"] = current_user.id
            update_data["reviewed_at"] = datetime.utcnow()
            update_data["review_notes"] = "Скасовано адміністратором." # Приклад

        return await self.repository.update(db, db_obj=db_completion, obj_in=update_data)


task_completion_service = TaskCompletionService(task_completion_repository)

# TODO: Реалізувати логіку для командних завдань (хто бере в роботу, як розподіляються бонуси).
# TODO: Інтегрувати з `TransactionService` для нарахування/списання бонусів.
# TODO: Інтегрувати з `NotificationService` для відправки сповіщень.
# TODO: Деталізувати перевірку прав та умов для кожної дії (наприклад, чи можна взяти завдання в роботу).
# TODO: Обробка `attachments` в `submit_task_for_review` - збереження файлів та зв'язування.
#
# Все виглядає як хороший початок для сервісу управління виконанням завдань.
# Охоплено основні етапи: початок, подання на перевірку, перевірка, скасування.
# Використовуються відповідні статуси та схеми.
