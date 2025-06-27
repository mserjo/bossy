# backend/app/src/api/v1/tasks/assignments.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління призначеннями завдань API v1.

Цей модуль надає API для:
- Призначення завдання конкретному користувачу або команді (адміністратором групи).
- Перегляду, хто призначений на завдання.
- Можливо, для користувача - взяти завдання у роботу (якщо це реалізовано через призначення).
"""

from fastapi import APIRouter, Depends, status
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати схеми, сервіси, залежності.

logger = get_logger(__name__)
router = APIRouter()

# Шляхи будуть відносно /groups/{group_id}/tasks/{task_id}/assignments

@router.post(
    "", # Тобто /groups/{group_id}/tasks/{task_id}/assignments
    # response_model=TaskAssignmentSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks", "Task Assignments"],
    summary="Призначити завдання користувачу/команді (заглушка)"
    # dependencies=[Depends(group_admin_permission_for_task)]
)
async def assign_task(
    group_id: int,
    task_id: int,
    # assignment_data: TaskAssignmentCreateSchema
    # (має містити user_id або team_id, можливо, due_date)
):
    logger.info(f"Призначення завдання {task_id} (група {group_id}) (заглушка).")
    # TODO: Реалізувати логіку призначення завдання
    return {"message": "Завдання призначено", "task_id": task_id, "assigned_to": "user_or_team_id"}

@router.get(
    "",
    # response_model=List[TaskAssignmentSchema],
    tags=["Tasks", "Task Assignments"],
    summary="Отримати список призначень для завдання (заглушка)"
    # dependencies=[Depends(group_member_permission_for_task)]
)
async def get_task_assignments(
    group_id: int,
    task_id: int,
):
    logger.info(f"Запит списку призначень для завдання {task_id} (група {group_id}) (заглушка).")
    # TODO: Реалізувати логіку отримання списку призначень
    return [{"assignment_id": 1, "user_id": 123, "assigned_at": "datetime"}]

@router.delete(
    "/{assignment_id}", # Або /{user_or_team_id}
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tasks", "Task Assignments"],
    summary="Скасувати призначення завдання (заглушка)"
    # dependencies=[Depends(group_admin_permission_for_task)]
)
async def unassign_task(
    group_id: int,
    task_id: int,
    assignment_id: int, # Або user_or_team_id
):
    logger.info(f"Скасування призначення {assignment_id} для завдання {task_id} (група {group_id}) (заглушка).")
    # TODO: Реалізувати логіку скасування призначення
    return

# Роутер буде підключений в backend/app/src/api/v1/tasks/__init__.py
