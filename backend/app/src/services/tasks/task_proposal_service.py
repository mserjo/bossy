# backend/app/src/services/tasks/task_proposal_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `TaskProposalService` для управління пропозиціями завдань від користувачів.
"""
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.tasks.proposal import TaskProposalModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.tasks.proposal import TaskProposalCreateSchema, TaskProposalUpdateSchema, TaskProposalSchema
from backend.app.src.repositories.tasks.proposal import TaskProposalRepository, task_proposal_repository
from backend.app.src.repositories.groups.group import group_repository
from backend.app.src.repositories.dictionaries.status import status_repository
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import (
    USER_TYPE_SUPERADMIN,
    TASK_PROPOSAL_STATUS_PENDING_CODE, # Потрібна константа
    TASK_PROPOSAL_STATUS_APPROVED_CODE, # Потрібна константа
    TASK_PROPOSAL_STATUS_REJECTED_CODE, # Потрібна константа
    TRANSACTION_TYPE_PROPOSAL_BONUS # Для нарахування бонусу
)
# from backend.app.src.services.groups.group_membership_service import group_membership_service
# from backend.app.src.services.tasks.task_service import task_service # Для створення завдання
# from backend.app.src.services.bonuses.transaction_service import transaction_service # Для нарахування бонусу

class TaskProposalService(BaseService[TaskProposalRepository]):
    """
    Сервіс для управління пропозиціями завдань.
    """

    async def get_proposal_by_id(self, db: AsyncSession, proposal_id: uuid.UUID) -> TaskProposalModel:
        proposal = await self.repository.get(db, id=proposal_id) # Репозиторій має завантажувати зв'язки за потреби
        if not proposal:
            raise NotFoundException(f"Пропозицію завдання з ID {proposal_id} не знайдено.")
        return proposal

    async def submit_proposal(
        self, db: AsyncSession, *, obj_in: TaskProposalCreateSchema, group_id: uuid.UUID, current_user: UserModel
    ) -> TaskProposalModel:
        """
        Створює (подає) нову пропозицію завдання.
        """
        # Перевірка, чи користувач є членом групи
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Відкладений імпорт
        membership = await group_membership_service.get_membership_by_user_and_group(db, user_id=current_user.id, group_id=group_id)
        if not membership: # Або якщо членство неактивне
            raise ForbiddenException("Лише члени групи можуть подавати пропозиції завдань.")

        # Перевірка існування групи (хоча членство вже мало б це перевірити)
        group = await group_repository.get(db, id=group_id)
        if not group:
            raise NotFoundException(f"Групу з ID {group_id} не знайдено.")

        # TODO: Перевірити, чи ввімкнено пропозиції завдань в налаштуваннях групи
        # (GroupSettingsModel.task_proposals_enabled)
        # group_settings = await group_settings_service.get_settings_for_group(db, group_id=group_id)
        # if not group_settings.task_proposals_enabled:
        #     raise ForbiddenException("Пропозиції завдань вимкнені для цієї групи.")

        pending_status = await status_repository.get_by_code(db, code=TASK_PROPOSAL_STATUS_PENDING_CODE)
        if not pending_status:
            raise BadRequestException(f"Статус '{TASK_PROPOSAL_STATUS_PENDING_CODE}' для пропозицій не знайдено.")

        # Використовуємо кастомний метод репозиторію для встановлення group_id, proposer_id, status_id
        return await self.repository.create_proposal(
            db, obj_in=obj_in, group_id=group_id, proposer_id=current_user.id, initial_status_id=pending_status.id
        )

    async def review_proposal(
        self, db: AsyncSession, *,
        proposal_id: uuid.UUID,
        obj_in: TaskProposalUpdateSchema, # Має містити новий status_id, admin_review_notes
        current_user: UserModel # Адмін групи або superuser
    ) -> TaskProposalModel:
        """
        Розглядає пропозицію завдання (приймає або відхиляє).
        Якщо прийнято, може автоматично створити завдання.
        Якщо нараховується бонус, створює транзакцію.
        """
        db_proposal = await self.get_proposal_by_id(db, proposal_id=proposal_id)

        # Перевірка прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=db_proposal.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи може розглядати пропозиції завдань.")

        if db_proposal.status.code != TASK_PROPOSAL_STATUS_PENDING_CODE:
            raise BadRequestException(f"Пропозиція не знаходиться в статусі '{TASK_PROPOSAL_STATUS_PENDING_CODE}' для розгляду.")

        new_status = await status_repository.get(db, id=obj_in.status_id)
        if not new_status:
            raise BadRequestException(f"Новий статус з ID {obj_in.status_id} не знайдено.")

        if new_status.code not in [TASK_PROPOSAL_STATUS_APPROVED_CODE, TASK_PROPOSAL_STATUS_REJECTED_CODE]:
            raise BadRequestException(f"Недопустимий статус для результату розгляду пропозиції: {new_status.code}.")

        if new_status.code == TASK_PROPOSAL_STATUS_REJECTED_CODE and not obj_in.admin_review_notes:
            raise BadRequestException("Коментар (admin_review_notes) є обов'язковим при відхиленні пропозиції.")

        update_data = obj_in.model_dump(exclude_unset=True)
        update_data["reviewed_by_user_id"] = current_user.id
        update_data["reviewed_at"] = datetime.utcnow()

        created_task_id_from_schema = update_data.pop("created_task_id", None) # Обробляємо окремо

        updated_proposal = await self.repository.update(db, db_obj=db_proposal, obj_in=update_data)

        if new_status.code == TASK_PROPOSAL_STATUS_APPROVED_CODE:
            # Логіка створення завдання на основі пропозиції
            if created_task_id_from_schema: # Якщо адмін вручну вказав ID створеного завдання
                task_exists = await task_repository.get(db, id=created_task_id_from_schema)
                if not task_exists:
                     raise BadRequestException(f"Вказане створене завдання з ID {created_task_id_from_schema} не знайдено.")
                updated_proposal.created_task_id = created_task_id_from_schema
            # else:
                # TODO: Автоматичне створення завдання, якщо `created_task_id` не передано.
                # from backend.app.src.services.tasks.task_service import task_service
                # task_create_schema = ... # Сформувати з db_proposal.title, description, proposed_task_details
                # created_task = await task_service.create_task(db, obj_in=task_create_schema, group_id=db_proposal.group_id, current_user=current_user)
                # updated_proposal.created_task_id = created_task.id
                pass # Залишаю для реалізації логіки авто-створення

            # Нарахування бонусу за пропозицію, якщо вказано
            if obj_in.bonus_for_proposal_awarded and not updated_proposal.bonus_for_proposal_awarded: # Якщо встановлено в True і ще не було нараховано
                # TODO: Визначити суму бонусу (з налаштувань групи або фіксована).
                # bonus_amount = Decimal("5.00") # Приклад
                # proposer_account = await account_repository.get_by_user_and_group(...)
                # await transaction_service.create_transaction(db, account_id=proposer_account.id, amount=bonus_amount,
                #                                           type_code=TRANSACTION_TYPE_PROPOSAL_BONUS,
                #                                           description=f"Бонус за пропозицію завдання: {updated_proposal.title}",
                #                                           source_entity_type="task_proposal", source_entity_id=updated_proposal.id)
                updated_proposal.bonus_for_proposal_awarded = True # Позначаємо, що бонус нараховано (або буде нараховано)
                self.logger.info(f"Бонус за пропозицію {updated_proposal.id} буде нараховано користувачу {updated_proposal.proposed_by_user_id}.")

        db.add(updated_proposal) # Додаємо для збереження змін created_task_id або bonus_for_proposal_awarded
        await db.commit()
        await db.refresh(updated_proposal)
        return updated_proposal

    # `delete` успадкований (якщо пропозиції можна видаляти).

task_proposal_service = TaskProposalService(task_proposal_repository)

# TODO: Додати константи для TASK_PROPOSAL_STATUS_* в `constants.py` та відповідний Enum в `dicts.py`.
# TODO: Реалізувати логіку перевірки `GroupSettingsModel.task_proposals_enabled`.
# TODO: Реалізувати логіку автоматичного створення завдання з пропозиції.
# TODO: Реалізувати логіку нарахування бонусу за пропозицію (інтеграція з TransactionService).
# TODO: Переконатися, що `TaskProposalCreateSchema` та `TaskProposalUpdateSchema` коректні.
#       `TaskProposalCreateSchema` не має містити `group_id`, `proposed_by_user_id`, `status_id`.
#       `TaskProposalUpdateSchema` має дозволяти оновлення `status_id` та інших полів розгляду.
#
# Все виглядає як хороший початок для сервісу пропозицій завдань.
# Охоплено створення, розгляд (прийняття/відхилення).
# Важливою є інтеграція з TaskService та TransactionService.
