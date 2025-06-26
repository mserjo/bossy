# backend/app/src/repositories/tasks/proposal.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `TaskProposalModel`.
Надає методи для управління пропозиціями завдань від користувачів.
"""

from typing import Optional, List, Any, Dict
import uuid
from sqlalchemy import select # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.tasks.proposal import TaskProposalModel
from backend.app.src.schemas.tasks.proposal import TaskProposalCreateSchema, TaskProposalUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class TaskProposalRepository(BaseRepository[TaskProposalModel, TaskProposalCreateSchema, TaskProposalUpdateSchema]):
    """
    Репозиторій для роботи з моделлю пропозицій завдань (`TaskProposalModel`).
    """

    async def get_proposals_for_group(
        self, db: AsyncSession, *, group_id: uuid.UUID,
        status_code: Optional[str] = None, # Код статусу пропозиції
        skip: int = 0, limit: int = 100
    ) -> List[TaskProposalModel]:
        """
        Отримує список пропозицій завдань для вказаної групи,
        опціонально фільтруючи за статусом.
        """
        from backend.app.src.models.dictionaries.status import StatusModel # Для фільтрації за статусом

        statement = select(self.model).where(self.model.group_id == group_id)
        if status_code:
            statement = statement.join(StatusModel, self.model.status_id == StatusModel.id).where(StatusModel.code == status_code)

        statement = statement.order_by(self.model.created_at.desc()).options( # type: ignore
            selectinload(self.model.proposer),
            selectinload(self.model.status),
            selectinload(self.model.reviewer),
            selectinload(self.model.created_task)
        ).offset(skip).limit(limit)

        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_proposals_by_user(
        self, db: AsyncSession, *, user_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[TaskProposalModel]:
        """
        Отримує список пропозицій, зроблених вказаним користувачем.
        """
        statement = select(self.model).where(self.model.proposed_by_user_id == user_id)
        statement = statement.order_by(self.model.created_at.desc()).options( # type: ignore
            selectinload(self.model.group),
            selectinload(self.model.status)
        ).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    # `create` успадкований. `TaskProposalCreateSchema` використовується для вхідних даних.
    # `group_id` та `proposed_by_user_id` мають бути встановлені сервісом.
    # Потрібен кастомний метод `create_proposal`.
    async def create_proposal(
        self, db: AsyncSession, *, obj_in: TaskProposalCreateSchema,
        group_id: uuid.UUID, proposer_id: uuid.UUID, initial_status_id: uuid.UUID
    ) -> TaskProposalModel:
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(
            group_id=group_id,
            proposed_by_user_id=proposer_id,
            status_id=initial_status_id,
            **obj_in_data
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # `update` успадкований. `TaskProposalUpdateSchema` використовується для оновлення,
    # наприклад, статусу, коментарів адміна, пов'язаного завдання.
    # `reviewed_by_user_id` та `reviewed_at` встановлюються сервісом.

task_proposal_repository = TaskProposalRepository(TaskProposalModel)

# TODO: Переконатися, що `TaskProposalCreateSchema` та `TaskProposalUpdateSchema`
#       коректно визначені.
#       `TaskProposalCreateSchema` не має містити `group_id`, `proposed_by_user_id`, `status_id`.
#       `TaskProposalUpdateSchema` може оновлювати `status_id`, `admin_review_notes`,
#       `reviewed_by_user_id`, `reviewed_at`, `created_task_id`, `bonus_for_proposal_awarded`.
#
# Все виглядає добре. Надано методи для отримання та створення пропозицій.
# Фільтрація за статусом в `get_proposals_for_group` корисна.
