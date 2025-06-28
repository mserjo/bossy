# backend/app/src/services/system/cron_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `CronTaskService` для управління системними cron-задачами.
"""
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from croniter import croniter
except ImportError:
    croniter = None # type: ignore

from backend.app.src.models.system.cron import CronTaskModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.system.cron_task import CronTaskCreateSchema, CronTaskUpdateSchema, CronTaskSchema
from backend.app.src.repositories.system.cron_repository import CronTaskRepository # Змінено імпорт
from backend.app.src.repositories.dictionaries.status_repository import StatusRepository # Змінено імпорт
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN, STATUS_ACTIVE_CODE
from backend.app.src.config.logging import logger

class CronTaskService(BaseService[CronTaskRepository]):
    """
    Сервіс для управління системними cron-задачами.
    """
    def __init__(self, db_session: AsyncSession):
        super().__init__(CronTaskRepository(db_session))
        self.db_session = db_session # Зберігаємо сесію для використання в цьому сервісі
        self.status_repo = StatusRepository(db_session)


    async def get_task_by_id(self, task_id: uuid.UUID) -> CronTaskModel:
        task = await self.repository.get(id=task_id)
        if not task:
            raise NotFoundException(f"Cron-задача з ID {task_id} не знайдена.")
        return task

    async def get_task_by_identifier(self, task_identifier: str) -> Optional[CronTaskModel]:
        # Дозволяємо повернути None, якщо задача не обов'язково має існувати
        return await self.repository.get_by_task_identifier(task_identifier=task_identifier)

    async def get_all_cron_tasks(self, skip: int = 0, limit: int = 100) -> List[CronTaskModel]:
        return await self.repository.get_multi(skip=skip, limit=limit)

    async def create_cron_task(
        self, *, obj_in: CronTaskCreateSchema, current_user: UserModel
    ) -> CronTaskModel:
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може створювати cron-задачі.")

        existing_task = await self.repository.get_by_task_identifier(task_identifier=obj_in.task_identifier)
        if existing_task:
            raise BadRequestException(f"Cron-задача з ідентифікатором '{obj_in.task_identifier}' вже існує.")

        if obj_in.cron_expression:
            if croniter is None:
                logger.warning("Бібліотека 'croniter' не встановлена. Пропускається валідація cron-виразу.")
            elif not croniter.is_valid(obj_in.cron_expression):
                raise BadRequestException(f"Некоректний формат cron-виразу: {obj_in.cron_expression}")

        create_data = obj_in.model_dump(exclude_unset=True)
        if 'state_id' not in create_data or create_data['state_id'] is None: # Встановлюємо статус за замовчуванням, якщо не передано
            active_status = await self.status_repo.get_by_code(code=STATUS_ACTIVE_CODE)
            if active_status:
                create_data['state_id'] = active_status.id
            else: # Малоймовірно, але обробимо
                logger.error(f"Не вдалося знайти активний статус з кодом {STATUS_ACTIVE_CODE} для cron-задачі.")
                # Можна кинути помилку або залишити state_id=None, залежно від логіки БД

        create_data["created_by_user_id"] = current_user.id

        new_task = await self.repository.create_cron_task(obj_in_data=create_data)
        logger.info(f"Супер-адміністратор {current_user.email} створив cron-задачу '{new_task.name}'.")
        return new_task


    async def update_cron_task(
        self, *, task_id: uuid.UUID, obj_in: CronTaskUpdateSchema, current_user: UserModel
    ) -> CronTaskModel:
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може оновлювати cron-задачі.")

        db_task = await self.get_task_by_id(task_id=task_id)
        update_data = obj_in.model_dump(exclude_unset=True)

        if "task_identifier" in update_data and update_data["task_identifier"] != db_task.task_identifier:
            existing_task = await self.repository.get_by_task_identifier(task_identifier=update_data["task_identifier"])
            if existing_task and existing_task.id != task_id:
                raise BadRequestException(f"Cron-задача з ідентифікатором '{update_data['task_identifier']}' вже існує.")

        if "cron_expression" in update_data and update_data["cron_expression"]:
            if croniter is None:
                logger.warning("Бібліотека 'croniter' не встановлена. Пропускається валідація cron-виразу при оновленні.")
            elif not croniter.is_valid(update_data["cron_expression"]):
                raise BadRequestException(f"Некоректний формат cron-виразу: {update_data['cron_expression']}")

        update_data["updated_by_user_id"] = current_user.id

        updated_task = await self.repository.update_cron_task(db_obj=db_task, obj_in_data=update_data)
        logger.info(f"Супер-адміністратор {current_user.email} оновив cron-задачу ID {task_id}.")
        return updated_task

    async def delete_cron_task(self, *, task_id: uuid.UUID, current_user: UserModel) -> CronTaskModel:
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може видаляти cron-задачі.")
        # М'яке видалення реалізовано в репозиторії
        deleted_task = await self.repository.soft_delete_by_id(id=task_id)
        if not deleted_task:
            raise NotFoundException(f"Cron-задача з ID {task_id} не знайдена для видалення.")
        logger.info(f"Супер-адміністратор {current_user.email} видалив (м'яко) cron-задачу ID {task_id}.")
        return deleted_task

    async def calculate_next_run_time(self, task: CronTaskModel, current_time_utc: Optional[datetime] = None) -> Optional[datetime]:
        if not task.is_enabled or task.is_deleted:
            return None

        if current_time_utc is None:
            current_time_utc = datetime.now(timezone.utc)
        elif current_time_utc.tzinfo is None: # Переконуємося, що час є aware
            current_time_utc = current_time_utc.replace(tzinfo=timezone.utc)


        next_run: Optional[datetime] = None
        if task.cron_expression:
            if croniter is None:
                logger.error("Бібліотека 'croniter' не встановлена. Неможливо розрахувати next_run_time для cron-виразу.")
                return None
            try:
                # croniter працює з naive datetime в UTC, якщо base є aware UTC
                base_for_croniter = current_time_utc # Вже є aware UTC
                itr = croniter(task.cron_expression, base_for_croniter)
                next_run = itr.get_next(datetime) # Поверне aware datetime в UTC
            except Exception as e:
                logger.error(f"Помилка розрахунку next_run_time для cron '{task.cron_expression}' задачі '{task.name}': {e}")
                return None
        elif task.interval_schedule:
            last_event_time = task.last_run_at or task.created_at
            if last_event_time.tzinfo is None: # Робимо aware, якщо naive
                last_event_time = last_event_time.replace(tzinfo=timezone.utc)

            potential_next_run = last_event_time + task.interval_schedule
            # Якщо розрахований час вже минув, наступний запуск - це зараз (щоб наздогнати)
            # Або, якщо потрібно строго дотримуватися інтервалу від останнього запуску, то potential_next_run.
            # Для простоти, якщо вже минув, то наступний запуск буде "незабаром" (наприклад, при наступній перевірці планувальника).
            # Щоб уникнути миттєвого повторного запуску, якщо завдання виконується довго:
            if potential_next_run <= current_time_utc:
                 # Наступний запуск буде від поточного часу + інтервал, щоб уникнути зациклення, якщо завдання довге
                 next_run = current_time_utc + task.interval_schedule
            else:
                 next_run = potential_next_run

        elif task.run_once_at:
            run_once_at_aware = task.run_once_at
            if run_once_at_aware.tzinfo is None:
                run_once_at_aware = run_once_at_aware.replace(tzinfo=timezone.utc)

            if task.last_run_at is None and run_once_at_aware > current_time_utc:
                next_run = run_once_at_aware
            else:
                next_run = None # Вже виконано або час минув

        return next_run

    async def update_task_after_run(
        self, *, task_id: uuid.UUID,
        run_succeeded: bool, log_message: Optional[str] = None
    ):
        task = await self.get_task_by_id(task_id=task_id)

        current_time = datetime.now(timezone.utc)
        next_run_time = await self.calculate_next_run_time(task, current_time_utc=current_time)

        if task.run_once_at and run_succeeded:
            # Для одноразових завдань, які успішно виконані, вимикаємо їх
            task.is_enabled = False
            logger.info(f"Одноразова задача '{task.name}' (ID: {task.id}) виконана та деактивована.")
            # next_run_time також буде None

        await self.repository.update_task_run_info(
            task_obj=task,
            last_run_at=current_time,
            next_run_at=next_run_time, # Може бути None
            last_run_status="success" if run_succeeded else "failure",
            last_run_log=log_message
        )
        logger.debug(f"Оновлено інформацію про запуск для задачі ID {task_id}. Наступний запуск: {next_run_time}")

    async def get_active_and_due_tasks(self) -> List[CronTaskModel]:
        """
        Отримує список активних cron-задач, час виконання яких настав або минув.
        """
        # Цей метод буде викликатися періодично (наприклад, кожну хвилину)
        # завданням `execute_due_cron_tasks` з `cron_task_executor.py`.
        now_utc = datetime.now(timezone.utc)
        due_tasks = await self.repository.get_due_tasks(current_time_utc=now_utc)
        logger.info(f"Знайдено {len(due_tasks)} активних cron-задач для виконання станом на {now_utc}.")
        return due_tasks

# Екземпляр сервісу не створюємо тут глобально. Він буде створюватися там, де потрібен, з передачею сесії.
