# backend/app/src/api/v1/tasks/tasks.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для основного управління завданнями/подіями в групі API v1.

Цей модуль надає API для:
- Створення нового завдання/події адміністратором групи.
- Отримання списку завдань/подій у групі.
- Отримання детальної інформації про конкретне завдання/подію.
- Оновлення інформації про завдання/подію (адміністратором групи).
- Видалення завдання/події (адміністратором групи).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Response
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.tasks.task import TaskSchema, TaskCreateSchema, TaskUpdateSchema
from backend.app.src.services.tasks.task_service import TaskService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission, group_member_permission # Для перевірки прав
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти будуть мати префікс /groups/{group_id}/tasks,
# тому group_id буде передаватися як параметр шляху.

@router.post(
    "", # Шлях буде /groups/{group_id}/tasks
    response_model=TaskSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
    summary="Створити нове завдання/подію в групі (адміністратор групи)"
)
async def create_task_in_group(
    task_in: TaskCreateSchema,
    group_id: int = Path(..., description="ID групи, в якій створюється завдання"),
    group_with_admin_rights: dict = Depends(group_admin_permission), # Перевірка, що користувач є адміном цієї групи
    db_session: DBSession = Depends()
):
    """
    Створює нове завдання або подію в зазначеній групі.
    Доступно лише адміністраторам цієї групи.
    `task_in` має містити `group_id`, який буде перевірено на відповідність `group_id` у шляху.
    """
    current_admin: UserModel = group_with_admin_rights["current_user"]

    if task_in.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID групи в тілі запиту ({task_in.group_id}) не співпадає з ID групи у шляху ({group_id})."
        )

    logger.info(
        f"Адміністратор {current_admin.email} створює нове завдання/подію '{task_in.name}' "
        f"в групі ID {group_id}."
    )
    task_service = TaskService(db_session)
    try:
        # TaskService.create_task повинен приймати TaskCreateSchema та ID користувача-творця (адміна)
        new_task = await task_service.create_task(
            task_create_data=task_in,
            creator_id=current_admin.id
        )
        logger.info(
            f"Завдання/подія '{new_task.name}' (ID: {new_task.id}) успішно створено "
            f"в групі ID {group_id} адміністратором {current_admin.email}."
        )
        return new_task
    except HTTPException as e: # Якщо сервіс кидає помилку (напр. невірний task_type_id)
        logger.warning(f"Помилка створення завдання/події '{task_in.name}' в групі {group_id}: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при створенні завдання/події '{task_in.name}' в групі {group_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при створенні завдання/події.")


@router.get(
    "", # Шлях буде /groups/{group_id}/tasks
    response_model=List[TaskSchema], # Або схема з пагінацією
    tags=["Tasks"],
    summary="Отримати список завдань/подій у групі"
)
async def list_tasks_in_group(
    group_id: int = Path(..., description="ID групи, для якої отримуються завдання"),
    access_check: dict = Depends(group_member_permission), # Учасники групи можуть бачити завдання
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
    # TODO: Додати фільтри: status_id, task_type_id, assigned_to_user_id, is_event (boolean)
    status_code: Optional[str] = Query(None, description="Фільтр за кодом статусу завдання"),
    task_type_code: Optional[str] = Query(None, description="Фільтр за кодом типу завдання"),
    # is_event: Optional[bool] = Query(None, description="Фільтр за ознакою події (true/false)")
):
    """
    Повертає список завдань/подій для зазначеної групи з пагінацією.
    Доступно учасникам групи.
    """
    current_user: UserModel = access_check["current_user"]
    logger.info(
        f"Користувач {current_user.email} запитує список завдань/подій для групи ID {group_id} "
        f"(сторінка: {page}, розмір: {page_size})."
    )
    task_service = TaskService(db_session)

    tasks_data = await task_service.get_tasks_by_group_id(
        group_id=group_id,
        skip=(page - 1) * page_size,
        limit=page_size,
        status_code=status_code,
        task_type_code=task_type_code,
        # is_event=is_event,
        # user_id_for_access_check=current_user.id # Якщо потрібна додаткова перевірка доступу на рівні сервісу
    )
    # Припускаємо, що сервіс повертає {"tasks": [], "total": 0} або просто список
    if isinstance(tasks_data, dict):
        tasks = tasks_data.get("tasks", [])
        # total_tasks = tasks_data.get("total", 0)
        # TODO: Додати заголовки пагінації
    else:
        tasks = tasks_data

    return tasks


@router.get(
    "/{task_id}", # Шлях буде /groups/{group_id}/tasks/{task_id}
    response_model=TaskSchema,
    tags=["Tasks"],
    summary="Отримати детальну інформацію про завдання/подію"
)
async def get_task_details(
    group_id: int = Path(..., description="ID групи"),
    task_id: int = Path(..., description="ID завдання/події"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends()
):
    """
    Повертає детальну інформацію про конкретне завдання/подію в групі.
    Доступно учасникам групи.
    """
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує деталі завдання/події ID {task_id} з групи ID {group_id}.")
    task_service = TaskService(db_session)

    task = await task_service.get_task_by_id_and_group_id(
        task_id=task_id,
        group_id=group_id,
        # user_id_for_access_check=current_user.id # Якщо сервіс має перевіряти доступ
    )
    if not task:
        logger.warning(
            f"Завдання/подія ID {task_id} в групі ID {group_id} не знайдено або доступ заборонено "
            f"для користувача {current_user.email}."
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Завдання/подію не знайдено або доступ заборонено.")
    return task


@router.put(
    "/{task_id}",
    response_model=TaskSchema,
    tags=["Tasks"],
    summary="Оновити інформацію про завдання/подію (адміністратор групи)"
)
async def update_existing_task(
    task_in: TaskUpdateSchema,
    group_id: int = Path(..., description="ID групи"),
    task_id: int = Path(..., description="ID завдання/події для оновлення"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    """
    Оновлює інформацію про існуюче завдання/подію в групі.
    Доступно лише адміністраторам цієї групи.
    """
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} оновлює завдання/подію ID {task_id} в групі ID {group_id}."
    )
    task_service = TaskService(db_session)
    try:
        updated_task = await task_service.update_task(
            task_id=task_id,
            task_update_data=task_in,
            group_id_context=group_id, # Для перевірки, що завдання належить цій групі
            actor_id=current_admin.id
        )
        if not updated_task:
            # Сервіс повинен кидати виняток, якщо завдання не знайдено або не належить групі
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Завдання/подія не знайдено для оновлення.")
        logger.info(f"Завдання/подія ID {task_id} в групі {group_id} успішно оновлено.")
        return updated_task
    except HTTPException as e:
        logger.warning(f"Помилка оновлення завдання/події ID {task_id} в групі {group_id}: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при оновленні завдання/події ID {task_id} в групі {group_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при оновленні завдання/події.")


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tasks"],
    summary="Видалити завдання/подію (адміністратор групи)"
)
async def delete_existing_task(
    group_id: int = Path(..., description="ID групи"),
    task_id: int = Path(..., description="ID завдання/події для видалення"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    """
    Видаляє існуюче завдання/подію з групи.
    Доступно лише адміністраторам цієї групи.
    """
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} видаляє завдання/подію ID {task_id} з групи ID {group_id}."
    )
    task_service = TaskService(db_session)
    try:
        success = await task_service.delete_task(
            task_id=task_id,
            group_id_context=group_id, # Для перевірки
            actor_id=current_admin.id
        )
        if not success: # Якщо сервіс повертає boolean
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Завдання/подію не знайдено або не вдалося видалити.")
        logger.info(f"Завдання/подія ID {task_id} з групи {group_id} успішно видалено.")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException as e:
        logger.warning(f"Помилка видалення завдання/події ID {task_id} з групи {group_id}: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при видаленні завдання/події ID {task_id} з групи {group_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при видаленні завдання/події.")

# Роутер буде підключений в backend/app/src/api/v1/tasks/__init__.py
# з префіксом /groups/{group_id}/tasks
