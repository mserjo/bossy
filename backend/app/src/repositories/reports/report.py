# backend/app/src/repositories/reports/report.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `ReportModel`.
Надає методи для управління записами про генерацію звітів.
"""

from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.reports.report import ReportModel
from backend.app.src.schemas.reports.report import ReportCreateSchema, ReportUpdateSchema
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.core.dicts import ReportCodeEnum # Для фільтрації за типом звіту
# from backend.app.src.models.dictionaries.status import StatusModel # Для фільтрації за статусом

class ReportRepository(BaseRepository[ReportModel, ReportCreateSchema, ReportUpdateSchema]):
    """
    Репозиторій для роботи з моделлю звітів (`ReportModel`).
    """

    async def get_reports_by_user(
        self, db: AsyncSession, *, user_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[ReportModel]:
        """
        Отримує список звітів, замовлених вказаним користувачем.
        """
        statement = select(self.model).where(self.model.requested_by_user_id == user_id)
        statement = statement.order_by(self.model.created_at.desc()).options( # type: ignore
            selectinload(self.model.status),
            selectinload(self.model.generated_file)
        ).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_reports_for_group(
        self, db: AsyncSession, *, group_id: uuid.UUID,
        report_code: Optional[ReportCodeEnum] = None,
        status_code: Optional[str] = None, # Код статусу звіту
        skip: int = 0, limit: int = 100
    ) -> List[ReportModel]:
        """
        Отримує список звітів для вказаної групи,
        опціонально фільтруючи за типом звіту та статусом.
        """
        from backend.app.src.models.dictionaries.status import StatusModel # Локальний імпорт

        statement = select(self.model).where(self.model.group_id == group_id)
        if report_code:
            statement = statement.where(self.model.report_code == report_code.value)
        if status_code:
            statement = statement.join(StatusModel, self.model.status_id == StatusModel.id).where(StatusModel.code == status_code)

        statement = statement.order_by(self.model.created_at.desc()).options( # type: ignore
            selectinload(self.model.requester),
            selectinload(self.model.status),
            selectinload(self.model.generated_file)
        ).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_pending_reports_by_code(
        self, db: AsyncSession, *, report_code: ReportCodeEnum,
        pending_status_code: str, # Код статусу "в черзі" або "генерується"
        limit: int = 10
    ) -> List[ReportModel]:
        """
        Отримує звіти певного типу, які знаходяться в стані очікування/генерації.
        Корисно для воркера, що генерує звіти.
        """
        from backend.app.src.models.dictionaries.status import StatusModel # Локальний імпорт
        statement = select(self.model).where(
            self.model.report_code == report_code.value
        ).join(
            StatusModel, self.model.status_id == StatusModel.id
        ).where(
            StatusModel.code == pending_status_code
        ).order_by(self.model.created_at.asc()).limit(limit) # type: ignore # Обробляти найстаріші спочатку

        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    # `create` успадкований. `ReportCreateSchema` використовується.
    # `requested_by_user_id`, `group_id`, `status_id` встановлюються сервісом.
    async def create_report_request(
        self, db: AsyncSession, *, obj_in: ReportCreateSchema,
        requested_by_id: Optional[uuid.UUID],
        group_id_context: Optional[uuid.UUID], # group_id може бути в obj_in.parameters
        initial_status_id: uuid.UUID
    ) -> ReportModel:
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        # group_id може бути частиною parameters, або передаватися окремо,
        # залежно від логіки сервісу та типу звіту.
        # Якщо звіт глобальний, group_id_context буде None.
        db_obj = self.model(
            requested_by_user_id=requested_by_id,
            group_id=group_id_context, # Або брати з obj_in_data.get("parameters", {}).get("group_id")
            status_id=initial_status_id,
            **obj_in_data
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # `update` успадкований. `ReportUpdateSchema` для зміни статусу, `generated_at`, `file_id`.
    # `delete` успадкований.

report_repository = ReportRepository(ReportModel)

# TODO: Переконатися, що `ReportCreateSchema` та `ReportUpdateSchema` коректно визначені.
#       `ReportCreateSchema` має містити `report_code` та `parameters`.
#       Інші поля (user_id, group_id, status_id) встановлюються сервісом.
#
# TODO: Фільтрація за статусом в `get_reports_for_group` та `get_pending_reports_by_code`
#       потребує знання кодів статусів (наприклад, з `constants.py` або Enum).
#
# Все виглядає добре. Надано методи для роботи із записами про звіти.
# Логіка самої генерації звітів буде в сервісах та, можливо, фонових задачах.
