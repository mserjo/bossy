# backend/app/src/api/v1/tasks/proposals.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління пропозиціями завдань від користувачів API v1.

Цей модуль надає API для:
- Створення користувачем пропозиції нового завдання/події.
- Перегляду списку пропозицій (адміністратором групи, можливо, автором).
- Розгляду пропозиції адміністратором (прийняття/відхилення).
  Прийняття може автоматично створювати нове завдання на основі пропозиції.
"""

from fastapi import APIRouter, Depends, status
from typing import List
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати схеми, сервіси, залежності.

logger = get_logger(__name__)
router = APIRouter()

# Шляхи можуть бути відносно /groups/{group_id}/task-proposals

@router.post(
    "", # Тобто /groups/{group_id}/task-proposals
    # response_model=TaskProposalSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks", "Task Proposals"],
    summary="Створити пропозицію завдання/події (заглушка)"
    # dependencies=[Depends(group_member_permission)]
)
async def create_task_proposal(
    group_id: int,
    # proposal_data: TaskProposalCreateSchema,
    # current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач (ID TODO) створює пропозицію завдання для групи {group_id} (заглушка).")
    # TODO: Реалізувати логіку створення пропозиції
    return {"proposal_id": "prop_abc", "group_id": group_id, "title": "Запропоноване завдання", "status": "pending"}

@router.get(
    "",
    # response_model=List[TaskProposalSchema],
    tags=["Tasks", "Task Proposals"],
    summary="Отримати список пропозицій завдань для групи (адміністратор) (заглушка)"
    # dependencies=[Depends(group_admin_permission)]
)
async def list_task_proposals(
    group_id: int,
    # status_filter: Optional[str] = Query(None, description="Фільтр за статусом пропозиції")
):
    logger.info(f"Запит списку пропозицій завдань для групи {group_id} (заглушка).")
    # TODO: Реалізувати логіку отримання списку пропозицій
    return [{"proposal_id": "prop_abc", "title": "Запропоноване завдання", "status": "pending", "proposer_id": 123}]

@router.get(
    "/{proposal_id}",
    # response_model=TaskProposalSchema,
    tags=["Tasks", "Task Proposals"],
    summary="Отримати деталі пропозиції завдання (заглушка)"
    # dependencies=[Depends(group_admin_or_proposal_author_permission)]
)
async def get_task_proposal_details(
    group_id: int,
    proposal_id: str # Або int
):
    logger.info(f"Запит деталей пропозиції {proposal_id} для групи {group_id} (заглушка).")
    # TODO: Реалізувати логіку
    return {"proposal_id": proposal_id, "title": "Деталі запропонованого завдання", "description": "...", "status": "pending"}

@router.post(
    "/{proposal_id}/approve",
    # response_model=TaskSchema, # Повертає створене завдання
    tags=["Tasks", "Task Proposals"],
    summary="Прийняти пропозицію та створити завдання (адміністратор) (заглушка)"
    # dependencies=[Depends(group_admin_permission)]
)
async def approve_task_proposal(
    group_id: int,
    proposal_id: str, # Або int
    # Optional: admin_can_modify_task_details_on_approval = Body(None)
):
    logger.info(f"Адміністратор (ID TODO) приймає пропозицію {proposal_id} для групи {group_id} (заглушка).")
    # TODO: Реалізувати логіку:
    # 1. Змінити статус пропозиції на "approved".
    # 2. Створити нове завдання на основі даних пропозиції (можливо, з модифікаціями).
    # 3. Опціонально: нарахувати бонус автору пропозиції.
    return {"task_id": "task_789", "name": "Нове завдання з пропозиції", "message": "Пропозицію прийнято, завдання створено."}

@router.post(
    "/{proposal_id}/reject",
    # response_model=TaskProposalSchema, # Повертає оновлену пропозицію
    tags=["Tasks", "Task Proposals"],
    summary="Відхилити пропозицію завдання (адміністратор) (заглушка)"
    # dependencies=[Depends(group_admin_permission)]
)
async def reject_task_proposal(
    group_id: int,
    proposal_id: str, # Або int
    # rejection_reason: Optional[str] = Body(None)
):
    logger.info(f"Адміністратор (ID TODO) відхиляє пропозицію {proposal_id} для групи {group_id} (заглушка).")
    # TODO: Реалізувати логіку зміни статусу пропозиції на "rejected"
    return {"proposal_id": proposal_id, "status": "rejected", "message": "Пропозицію відхилено."}


# Роутер буде підключений в backend/app/src/api/v1/tasks/__init__.py
