# backend/app/src/api/v1/tasks/completions.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління виконанням та перевіркою завдань API v1.

Цей модуль надає API для:
- Позначення завдання як "взято в роботу" користувачем.
- Позначення завдання як "виконано" користувачем (відправка на перевірку).
- Підтвердження/відхилення виконання завдання адміністратором групи.
- Скасування завдання користувачем.
"""

from fastapi import APIRouter, Depends, status
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати схеми, сервіси, залежності.

logger = get_logger(__name__)
router = APIRouter()

# Шляхи будуть відносно /groups/{group_id}/tasks/{task_id}/completions або /actions

@router.post(
    "/take", # Тобто /groups/{group_id}/tasks/{task_id}/completions/take або /actions/take
    # response_model=TaskStatusChangeResponseSchema,
    tags=["Tasks", "Task Completions"],
    summary="Взяти завдання в роботу (заглушка)"
    # dependencies=[Depends(current_user_can_take_task)]
)
async def take_task_into_progress(
    group_id: int,
    task_id: int,
    # current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач (ID TODO) бере завдання {task_id} (група {group_id}) в роботу (заглушка).")
    # TODO: Реалізувати логіку зміни статусу завдання на "в роботі"
    return {"task_id": task_id, "new_status": "in_progress", "message": "Завдання взято в роботу."}

@router.post(
    "/complete",
    # response_model=TaskStatusChangeResponseSchema,
    tags=["Tasks", "Task Completions"],
    summary="Позначити завдання як виконане (на перевірку) (заглушка)"
    # dependencies=[Depends(current_user_can_complete_task)]
)
async def mark_task_as_completed(
    group_id: int,
    task_id: int,
    # completion_notes: Optional[str] = Body(None, description="Нотатки до виконання"),
    # current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач (ID TODO) позначає завдання {task_id} (група {group_id}) як виконане (заглушка).")
    # TODO: Реалізувати логіку зміни статусу завдання на "перевірка" та збереження нотаток
    return {"task_id": task_id, "new_status": "pending_review", "message": "Завдання відправлено на перевірку."}

@router.post(
    "/approve",
    # response_model=TaskStatusChangeResponseSchema,
    tags=["Tasks", "Task Completions"],
    summary="Підтвердити виконання завдання (адміністратор) (заглушка)"
    # dependencies=[Depends(group_admin_can_approve_task)]
)
async def approve_task_completion(
    group_id: int,
    task_id: int,
    # admin_notes: Optional[str] = Body(None, description="Нотатки адміністратора"),
    # admin_user: UserModel = Depends(CurrentActiveUser) # перевірка прав адміна групи
):
    logger.info(f"Адміністратор (ID TODO) підтверджує завдання {task_id} (група {group_id}) (заглушка).")
    # TODO: Реалізувати логіку зміни статусу на "підтверджено", нарахування бонусів
    return {"task_id": task_id, "new_status": "approved", "message": "Виконання завдання підтверджено."}

@router.post(
    "/reject",
    # response_model=TaskStatusChangeResponseSchema,
    tags=["Tasks", "Task Completions"],
    summary="Відхилити виконання завдання (адміністратор) (заглушка)"
    # dependencies=[Depends(group_admin_can_reject_task)]
)
async def reject_task_completion(
    group_id: int,
    task_id: int,
    # rejection_reason: str = Body(..., description="Причина відхилення"),
    # admin_user: UserModel = Depends(CurrentActiveUser) # перевірка прав адміна групи
):
    logger.info(f"Адміністратор (ID TODO) відхиляє завдання {task_id} (група {group_id}) (заглушка).")
    # TODO: Реалізувати логіку зміни статусу на "відхилено", збереження причини
    return {"task_id": task_id, "new_status": "rejected", "message": "Виконання завдання відхилено."}

@router.post(
    "/cancel",
    # response_model=TaskStatusChangeResponseSchema,
    tags=["Tasks", "Task Completions"],
    summary="Скасувати завдання (користувач, якщо взяв у роботу) (заглушка)"
    # dependencies=[Depends(current_user_can_cancel_task)]
)
async def cancel_task_progress(
    group_id: int,
    task_id: int,
    # current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач (ID TODO) скасовує завдання {task_id} (група {group_id}) (заглушка).")
    # TODO: Реалізувати логіку зміни статусу на "скасовано" або повернення до попереднього
    return {"task_id": task_id, "new_status": "cancelled", "message": "Завдання скасовано."}


# Роутер буде підключений в backend/app/src/api/v1/tasks/__init__.py
# Можливо, з префіксом /groups/{group_id}/tasks/{task_id}/actions або подібним.
