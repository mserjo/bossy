# backend/app/src/services/system/cron_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `CronTaskService` для управління системними cron-задачами.
"""
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
# import croniter # Для валідації та розрахунку next_run_at з cron_expression

from backend.app.src.models.system.cron import CronTaskModel
from backend.app.src.models.auth.user import UserModel # Для перевірки прав (superuser)
from backend.app.src.schemas.system.cron_task import CronTaskCreateSchema, CronTaskUpdateSchema, CronTaskSchema
from backend.app.src.repositories.system.cron import CronTaskRepository, cron_task_repository
from backend.app.src.repositories.dictionaries.status import status_repository # Для статусу
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN, STATUS_ACTIVE_CODE # Для дефолтного статусу

class CronTaskService(BaseService[CronTaskRepository]):
    """
    Сервіс для управління системними cron-задачами.
    """

    async def get_task_by_id(self, db: AsyncSession, task_id: uuid.UUID) -> CronTaskModel:
        task = await self.repository.get(db, id=task_id)
        if not task:
            raise NotFoundException(f"Cron-задача з ID {task_id} не знайдена.")
        return task

    async def get_task_by_identifier(self, db: AsyncSession, task_identifier: str) -> CronTaskModel:
        task = await self.repository.get_by_task_identifier(db, task_identifier=task_identifier)
        if not task:
            raise NotFoundException(f"Cron-задача з ідентифікатором '{task_identifier}' не знайдена.")
        return task

    async def create_cron_task(
        self, db: AsyncSession, *, obj_in: CronTaskCreateSchema, current_user: UserModel
    ) -> CronTaskModel:
        """Створює нову cron-задачу. Доступно лише супер-адміністратору."""
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може створювати cron-задачі.")

        # Перевірка унікальності task_identifier (вже є в моделі, але можна і тут)
        existing_task = await self.repository.get_by_task_identifier(db, task_identifier=obj_in.task_identifier)
        if existing_task:
            raise BadRequestException(f"Cron-задача з ідентифікатором '{obj_in.task_identifier}' вже існує.")

        # Валідація cron_expression (якщо передано)
        if obj_in.cron_expression:
            # from croniter import croniter # Відкладений імпорт
            # if not croniter.is_valid(obj_in.cron_expression):
            #     raise BadRequestException("Некоректний формат cron-виразу.")
            pass # TODO: Додати реальну валідацію cron-виразу

        # Встановлення початкового статусу, якщо не передано
        create_data = obj_in.model_dump(exclude_unset=True)
        if not obj_in.state_id:
            active_status = await status_repository.get_by_code(db, code=STATUS_ACTIVE_CODE)
            if active_status:
                create_data['state_id'] = active_status.id

        # `created_by_user_id`
        # create_data["created_by_user_id"] = current_user.id

        # `interval_seconds` з схеми конвертується в `interval_schedule` в репозиторії
        return await self.repository.create_cron_task(db, obj_in_data=create_data) # type: ignore # Репозиторій приймає obj_in: CronTaskCreateSchema

    async def update_cron_task(
        self, db: AsyncSession, *, task_id: uuid.UUID, obj_in: CronTaskUpdateSchema, current_user: UserModel
    ) -> CronTaskModel:
        """Оновлює існуючу cron-задачу. Доступно лише супер-адміністратору."""
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може оновлювати cron-задачі.")

        db_task = await self.get_task_by_id(db, task_id=task_id)

        update_data = obj_in.model_dump(exclude_unset=True)
        if "task_identifier" in update_data and update_data["task_identifier"] != db_task.task_identifier:
            existing_task = await self.repository.get_by_task_identifier(db, task_identifier=update_data["task_identifier"])
            if existing_task and existing_task.id != task_id:
                raise BadRequestException(f"Cron-задача з ідентифікатором '{update_data['task_identifier']}' вже існує.")

        if "cron_expression" in update_data and update_data["cron_expression"]:
            # Валідація нового cron_expression
            pass # TODO: Додати валідацію

        # `updated_by_user_id`
        # update_data["updated_by_user_id"] = current_user.id

        # `interval_seconds` з схеми конвертується в `interval_schedule` в репозиторії
        return await self.repository.update_cron_task(db, db_obj=db_task, obj_in_data=update_data) # type: ignore

    async def delete_cron_task(self, db: AsyncSession, *, task_id: uuid.UUID, current_user: UserModel) -> CronTaskModel:
        """Видаляє cron-задачу (м'яке видалення). Доступно лише супер-адміністратору."""
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може видаляти cron-задачі.")

        db_task = await self.get_task_by_id(db, task_id=task_id)
        # TODO: Перевірити, чи задача не виконується зараз, перед видаленням.

        deleted_task = await self.repository.soft_delete(db, db_obj=db_task) # type: ignore
        if not deleted_task:
             raise NotImplementedError("М'яке видалення не підтримується або не вдалося для cron-задач.")
        return deleted_task

    async def calculate_next_run_time(self, task: CronTaskModel, current_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        Розраховує наступний час виконання для задачі на основі її розкладу.
        """
        if not task.is_enabled or task.is_deleted:
            return None

        if current_time is None:
            current_time = datetime.utcnow() # Важливо UTC

        next_run: Optional[datetime] = None
        if task.cron_expression:
            # from croniter import croniter # Відкладений імпорт
            # try:
            #     # Переконуємося, що croniter працює з UTC, якщо current_time є UTC
            #     # Або передаємо naive datetime, якщо croniter очікує такий
            #     iter = croniter(task.cron_expression, current_time)
            #     next_run = iter.get_next(datetime)
            # except Exception as e:
            #     self.logger.error(f"Помилка розрахунку next_run_time для cron '{task.cron_expression}': {e}")
            #     return None
            pass # TODO: Реалізувати з croniter
        elif task.interval_schedule:
            # Для інтервальних, наступний запуск - це last_run_at + interval, або current_time + interval, якщо ще не запускалася
            last_run = task.last_run_at or task.created_at # Якщо не запускалася, беремо час створення
            if last_run:
                 # Переконуємося, що last_run є aware, якщо current_time aware
                if current_time.tzinfo is not None and last_run.tzinfo is None:
                    last_run = last_run.replace(tzinfo=current_time.tzinfo) # Припускаємо ту саму зону

                potential_next_run = last_run + task.interval_schedule
                # Якщо наступний розрахований час вже минув (наприклад, сервер був вимкнений),
                # то наступний запуск - це зараз + короткий інтервал, або просто зараз.
                # Або ж, якщо задача "наздоганяюча", то potential_next_run.
                # Поки що просто:
                next_run = potential_next_run
        elif task.run_once_at:
            if task.last_run_at is None and task.run_once_at > current_time: # Ще не запускалася і час не настав
                next_run = task.run_once_at
            else: # Вже запускалася або час минув
                next_run = None

        return next_run

    async def update_task_after_run(
        self, db: AsyncSession, *, task_id: uuid.UUID,
        run_succeeded: bool, log_message: Optional[str] = None
    ):
        """Оновлює задачу після її виконання."""
        task = await self.get_task_by_id(db, task_id=task_id)

        last_run_status = "success" if run_succeeded else "failure"
        next_run_time = await self.calculate_next_run_time(task, current_time=datetime.utcnow())

        # Якщо це була разова задача і вона виконана, її можна деактивувати
        if task.run_once_at and run_succeeded:
            task.is_enabled = False # Або змінити state_id на "завершено"

        return await self.repository.update_task_run_info(
            db, task_obj=task,
            last_run_at=datetime.utcnow(), # Час завершення (приблизно)
            next_run_at=next_run_time,
            last_run_status=last_run_status,
            last_run_log=log_message
        )

cron_task_service = CronTaskService(cron_task_repository)

# TODO: Інтегрувати бібліотеку `croniter` для валідації та розрахунку `next_run_at` з `cron_expression`.
# TODO: Узгодити встановлення `created_by_user_id` / `updated_by_user_id`.
#       (Передається `creator_id` в `create_cron_task` репозиторію).
# TODO: Узгодити логіку `is_enabled` та `state_id` для визначення активності задачі.
#
# Все виглядає як хороший початок для CronTaskService.
# Основні методи для CRUD, отримання задач для виконання, оновлення після виконання.
# Валідація прав супер-адміністратора.
# Розрахунок `next_run_at` є ключовою частиною.
