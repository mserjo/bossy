# backend/app/src/api/v1/system/cron_task.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління системними завданнями (cron).

Цей модуль надає API для перегляду, створення, редагування та видалення
системних завдань, які виконуються за розкладом (cron).
Доступ до цих ендпоінтів зазвичай має лише суперкористувач.

Системні завдання можуть включати:
- Регулярне очищення логів.
- Створення резервних копій.
- Розсилку періодичних звітів.
- Інші фонові задачі.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response # Додано Response
from typing import List

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.system.cron_task import CronTaskSchema, CronTaskCreateSchema, CronTaskUpdateSchema
from backend.app.src.services.system.cron_service import CronService # Назва сервісу може бути CronService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser
from backend.app.src.models.auth.user import UserModel # Для type hint current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/cron-tasks",
    response_model=List[CronTaskSchema],
    tags=["System", "Cron Tasks"],
    summary="Отримати список всіх системних cron завдань",
)
async def list_cron_tasks(
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    """
    Повертає список всіх налаштованих системних cron завдань.
    Доступно лише суперкористувачам.
    """
    logger.info(f"Користувач {current_user.email} запитує список cron завдань.")
    cron_service = CronService(db_session)
    tasks = await cron_service.get_all_cron_tasks()
    return tasks

@router.post(
    "/cron-tasks",
    response_model=CronTaskSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["System", "Cron Tasks"],
    summary="Створити нове системне cron завдання",
)
async def create_new_cron_task(
    task_data: CronTaskCreateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    """
    Створює нове системне cron завдання.
    Доступно лише суперкористувачам.
    """
    logger.info(f"Користувач {current_user.email} створює нове cron завдання: {task_data.name}.")
    cron_service = CronService(db_session)
    # TODO: Додати обробку можливих помилок з сервісу (наприклад, невалідний cron_expression)
    new_task = await cron_service.create_cron_task(task_data=task_data)
    return new_task

@router.get(
    "/cron-tasks/{task_id}",
    response_model=CronTaskSchema,
    tags=["System", "Cron Tasks"],
    summary="Отримати деталі конкретного cron завдання",
)
async def get_cron_task_details(
    task_id: int,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    """
    Повертає детальну інформацію про вказане cron завдання.
    Доступно лише суперкористувачам.
    """
    logger.info(f"Користувач {current_user.email} запитує деталі cron завдання ID: {task_id}.")
    cron_service = CronService(db_session)
    task = await cron_service.get_cron_task_by_id(task_id=task_id)
    if not task:
        logger.warning(f"Cron завдання з ID {task_id} не знайдено (запит від {current_user.email}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cron завдання не знайдено")
    return task

@router.put(
    "/cron-tasks/{task_id}",
    response_model=CronTaskSchema,
    tags=["System", "Cron Tasks"],
    summary="Оновити існуюче cron завдання",
)
async def update_existing_cron_task(
    task_id: int,
    task_data: CronTaskUpdateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    """
    Оновлює параметри існуючого cron завдання.
    Доступно лише суперкористувачам.
    """
    logger.info(f"Користувач {current_user.email} оновлює cron завдання ID: {task_id}.")
    cron_service = CronService(db_session)
    updated_task = await cron_service.update_cron_task(task_id=task_id, task_data=task_data)
    if not updated_task:
        logger.warning(f"Cron завдання з ID {task_id} не знайдено для оновлення (запит від {current_user.email}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cron завдання не знайдено для оновлення")
    return updated_task

@router.delete(
    "/cron-tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["System", "Cron Tasks"],
    summary="Видалити cron завдання",
)
async def delete_existing_cron_task(
    task_id: int,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    """
    Видаляє існуюче cron завдання.
    Доступно лише суперкористувачам.
    """
    logger.info(f"Користувач {current_user.email} видаляє cron завдання ID: {task_id}.")
    cron_service = CronService(db_session)
    success = await cron_service.delete_cron_task(task_id=task_id)
    if not success: # Припускаємо, що сервіс повертає boolean або кидає виняток
        logger.warning(f"Cron завдання з ID {task_id} не знайдено для видалення (запит від {current_user.email}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cron завдання не знайдено для видалення")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Роутер буде підключений в backend/app/src/api/v1/system/__init__.py
# або безпосередньо в backend/app/src/api/v1/router.py
