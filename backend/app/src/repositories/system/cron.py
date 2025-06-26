# backend/app/src/repositories/system/cron.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `CronTaskModel`.
Надає методи для управління системними cron-задачами.
"""

from typing import Optional, List, Any, Dict
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.system.cron import CronTaskModel
from backend.app.src.schemas.system.cron_task import CronTaskCreateSchema, CronTaskUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class CronTaskRepository(BaseRepository[CronTaskModel, CronTaskCreateSchema, CronTaskUpdateSchema]):
    """
    Репозиторій для роботи з моделлю системних cron-задач (`CronTaskModel`).
    """

    async def get_by_task_identifier(self, db: AsyncSession, *, task_identifier: str) -> Optional[CronTaskModel]:
        """
        Отримує cron-задачу за її унікальним ідентифікатором задачі.
        """
        statement = select(self.model).where(self.model.task_identifier == task_identifier)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_active_and_due_tasks(self, db: AsyncSession, now: Optional[datetime] = None) -> List[CronTaskModel]:
        """
        Отримує список активних cron-задач, час виконання яких настав або минув.
        Використовується планувальником для визначення, які задачі запускати.
        """
        if now is None:
            now = datetime.utcnow() # Важливо використовувати UTC, якщо next_run_at в UTC

        statement = select(self.model).where(
            self.model.is_enabled == True, # type: ignore # Задача увімкнена
            # self.model.state.has(code=ACTIVE_CRON_TASK_STATUS_CODE), # Або перевірка активного статусу
            self.model.next_run_at <= now, # Час наступного запуску настав
            self.model.is_deleted == False # type: ignore
        ).order_by(self.model.next_run_at.asc()) # type: ignore # Спочатку ті, що мали запуститися раніше

        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def update_task_run_info(
        self, db: AsyncSession, *, task_obj: CronTaskModel,
        last_run_at: datetime,
        next_run_at: Optional[datetime], # Може бути None для разових задач
        last_run_status: str,
        last_run_log: Optional[str] = None
    ) -> CronTaskModel:
        """
        Оновлює інформацію про останній запуск та наступний запланований час для cron-задачі.
        """
        task_obj.last_run_at = last_run_at
        task_obj.next_run_at = next_run_at
        task_obj.last_run_status = last_run_status
        if last_run_log is not None: # Оновлюємо лог, лише якщо він переданий
            task_obj.last_run_log = last_run_log

        db.add(task_obj)
        await db.commit()
        await db.refresh(task_obj)
        return task_obj

    # `create` успадкований. `CronTaskCreateSchema` використовується.
    #   `interval_seconds` з схеми має бути конвертований в `interval_schedule: timedelta` для моделі
    #   на сервісному рівні або в кастомному методі create.
    async def create_cron_task(self, db: AsyncSession, *, obj_in: CronTaskCreateSchema) -> CronTaskModel:
        """
        Створює нову cron-задачу, конвертуючи `interval_seconds` в `interval_schedule`.
        """
        obj_in_data = obj_in.model_dump(exclude_unset=True)

        interval_seconds = obj_in_data.pop("interval_seconds", None)
        if interval_seconds is not None:
            obj_in_data["interval_schedule"] = timedelta(seconds=interval_seconds)

        # `group_id` з BaseMainModel тут буде NULL, що є правильним.
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # `update` успадкований. `CronTaskUpdateSchema` використовується.
    #   Аналогічно, якщо `interval_seconds` передається для оновлення,
    #   сервіс має конвертувати його в `interval_schedule` перед передачею в `obj_in` для `update`.
    #   Або `update` тут перевизначається.
    async def update_cron_task(self, db: AsyncSession, *, db_obj: CronTaskModel, obj_in: CronTaskUpdateSchema) -> CronTaskModel:
        """
        Оновлює cron-задачу, конвертуючи `interval_seconds` в `interval_schedule`.
        """
        update_data = obj_in.model_dump(exclude_unset=True)

        if "interval_seconds" in update_data:
            interval_seconds = update_data.pop("interval_seconds")
            if interval_seconds is not None:
                update_data["interval_schedule"] = timedelta(seconds=interval_seconds)
            else:
                update_data["interval_schedule"] = None # Дозволяємо скидання інтервалу

        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    # `delete` (та `soft_delete`) успадковані.

cron_task_repository = CronTaskRepository(CronTaskModel)

# TODO: Переконатися, що `CronTaskCreateSchema` та `CronTaskUpdateSchema`
#       коректно обробляють `interval_seconds` та/або `interval_schedule`.
#       Поточні реалізації `create_cron_task` та `update_cron_task` обробляють `interval_seconds`.
#
# TODO: Узгодити перевірку "активного" статусу в `get_active_and_due_tasks`.
#       Зараз використовується `is_enabled` та `is_deleted`. `state_id` може додавати ще один рівень.
#
# Все виглядає добре. Надано методи для отримання задач для планувальника та оновлення їх стану.
# `task_identifier` є унікальним, що важливо для ідентифікації задач.
# `UniqueConstraint('task_identifier')` в `CronTaskModel` це забезпечує.
# `group_id` в `CronTaskModel` (успадкований) буде NULL. `CheckConstraint` не потрібен.
