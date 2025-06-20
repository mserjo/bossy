# backend/app/src/api/v1/tasks/tasks.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для CRUD операцій над сутністю "Завдання".

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List, Optional
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    get_current_active_superuser, paginator, get_group_membership_service
)
# TODO: Створити та використовувати залежності для перевірки прав доступу до завдань/груп:
#  - `require_group_member_or_superuser(group_id: UUID = Path(...))`
#  - `require_group_admin_or_superuser(group_id: UUID = Path(...))`
#  - `require_task_editor_or_superuser(task_id: UUID = Path(...))` (перевіряє, що юзер - адмін групи завдання або суперюзер)
#  - `require_task_viewer_or_superuser(task_id: UUID = Path(...))` (перевіряє, що юзер - член групи завдання або суперюзер)
from backend.app.src.api.v1.groups.groups import check_group_edit_permission, \
    check_group_view_permission  # Тимчасово для прикладу

from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.tasks.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskDetailedResponse
)
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.services.tasks.task import TaskService
from backend.app.src.services.groups.membership import GroupMembershipService  # Для перевірки членства в групі
from backend.app.src.core.constants import ADMIN_ROLE_CODE # Для перевірки ролі адміна
from backend.app.src.config import settings as global_settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter()


# Залежність для отримання TaskService
async def get_task_service(session: AsyncSession = Depends(get_api_db_session)) -> TaskService:
    """Залежність FastAPI для отримання екземпляра TaskService."""
    return TaskService(db_session=session)


# Залежність для GroupMembershipService (для перевірки прав)
# async def get_membership_service_dep(session: AsyncSession = Depends(get_api_db_session)) -> GroupMembershipService:
#     return GroupMembershipService(db_session=session)
# Використовуємо get_group_membership_service з dependencies


# ПРИМІТКА: Ця залежність перевіряє права на редагування завдання.
# Важливою є логіка перевірки адміністратора групи (`ADMIN_ROLE_CODE`) або суперюзера.
# Допоміжна функція-залежність для перевірки прав редагування завдання
async def task_edit_permission_dependency(
        task_id: UUID = Path(..., description="ID Завдання"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        task_service: TaskService = Depends(get_task_service),
        membership_service: GroupMembershipService = Depends(get_group_membership_service) # Оновлено залежність
) -> UserModel:
    task_orm = await task_service.get_task_orm_by_id(task_id)  # Потрібен метод, що повертає ORM модель
    if not task_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Завдання не знайдено")  # i18n
    if current_user.is_superuser:
        return current_user

    membership = await membership_service.get_membership_details(group_id=task_orm.group_id, user_id=current_user.id)
    if not membership or not membership.is_active or membership.role.code != ADMIN_ROLE_CODE: # Використання ADMIN_ROLE_CODE
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Недостатньо прав для редагування цього завдання.")
    return current_user


# ПРИМІТКА: Ця залежність перевіряє права на перегляд завдання, гарантуючи,
# що користувач є членом групи завдання або суперюзером.
# Допоміжна функція-залежність для перевірки прав перегляду завдання
async def task_view_permission_dependency(
        task_id: UUID = Path(..., description="ID Завдання"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        task_service: TaskService = Depends(get_task_service),
        membership_service: GroupMembershipService = Depends(get_group_membership_service) # Оновлено залежність
) -> UserModel:
    task_orm = await task_service.get_task_orm_by_id(task_id)
    if not task_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Завдання не знайдено")  # i18n
    if current_user.is_superuser:
        return current_user

    membership = await membership_service.get_membership_details(group_id=task_orm.group_id, user_id=current_user.id)
    if not membership or not membership.is_active:
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ви не є членом групи цього завдання.")
    return current_user


@router.post(
    "/",
    response_model=TaskDetailedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового завдання",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру створити нове завдання в межах групи."  # i18n
)
# ПРИМІТКА: Перевірка прав на створення завдання (адміністратор групи або суперюзер)
# наразі реалізована всередині ендпоінта. В майбутньому її варто винести
# в окрему, більш гранульовану залежність, як зазначено в TODO.
async def create_task(
        task_in: TaskCreate,  # group_id має бути в TaskCreate
        # Використовуємо залежність `check_group_edit_permission` з groups.py, передаючи group_id з тіла запиту.
        # Це не ідеально, краще мати залежність, що приймає group_id з Path або Query.
        # Оскільки group_id для нового завдання береться з task_in, перевірка прав тут має бути адаптована.
        # Поки що, припускаємо, що `creator_id` (current_user) має права на `task_in.group_id`.
        # TODO: Реалізувати залежність, що перевіряє права адміна на `task_in.group_id`.
        current_user: UserModel = Depends(get_current_active_user),  # Тимчасово, потрібна перевірка адміна групи
        task_service: TaskService = Depends(get_task_service),
        membership_service: GroupMembershipService = Depends(get_group_membership_service)  # Оновлено залежність
):
    """
    Створює нове завдання.
    Перевіряє, чи є `current_user` адміністратором групи, вказаної в `task_in.group_id`, або суперюзером.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' намагається створити завдання '{task_in.title}' в групі ID '{task_in.group_id}'.")

    # Перевірка прав доступу до групи
    if not current_user.is_superuser:
        membership = await membership_service.get_membership_details(group_id=task_in.group_id, user_id=current_user.id)
        if not membership or not membership.is_active or membership.role.code != ADMIN_ROLE_CODE: # Використання ADMIN_ROLE_CODE
            # i18n
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ви не є адміністратором вказаної групи.")

    try:
        # TaskService.create_task тепер приймає task_create_data та creator_id
        created_task = await task_service.create_task(
            task_create_data=task_in,
            creator_user_id=current_user.id
        )
        # Сервіс має повертати TaskDetailedResponse або сумісну ORM модель
        return created_task
    except ValueError as e:
        logger.warning(f"Помилка створення завдання '{task_in.title}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні завдання '{task_in.title}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/",
    response_model=PagedResponse[TaskResponse],
    summary="Отримання списку завдань",  # i18n
    description="""Повертає список завдань з пагінацією.
    Фільтрується за `group_id`, якщо надано (користувач має бути членом групи або суперюзером).
    Якщо `group_id` не надано, суперюзер бачить усі завдання, звичайний користувач - завдання з усіх своїх груп."""
    # i18n
)
# ПРИМІТКА: Фільтрація завдань за групою та правами доступу, а також пагінація,
# залежать від коректної реалізації методу `list_tasks_paginated` в `TaskService`.
# TODO щодо розширених фільтрів також важливий.
async def read_tasks(
        group_id: Optional[UUID] = Query(None, description="ID групи для фільтрації завдань"),  # i18n
        page_params: PageParams = Depends(paginator),
        current_user: UserModel = Depends(get_current_active_user),
        task_service: TaskService = Depends(get_task_service),
        membership_service: GroupMembershipService = Depends(get_membership_service_dep)  # Для перевірки членства
):
    """
    Отримує список завдань з пагінацією.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' запитує список завдань. Група: {group_id}, сторінка: {page_params.page}.")

    if group_id and not current_user.is_superuser:  # Якщо вказана група і користувач не суперюзер, перевірити членство
        membership = await membership_service.get_membership_details(group_id=group_id, user_id=current_user.id)
        if not membership or not membership.is_active:
            # i18n
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ви не є членом вказаної групи.")

    # TODO: TaskService.list_tasks_for_user_or_group має повертати (items, total_count)
    #  і обробляти логіку: якщо group_id є, то фільтр по ньому; якщо немає, то для суперюзера всі, для юзера - з його груп.
    tasks_orm, total_tasks = await task_service.list_tasks_paginated(
        user_id_context=current_user.id,  # Для визначення доступних груп, якщо group_id не вказано
        is_superuser_context=current_user.is_superuser,
        group_id_filter=group_id,
        skip=page_params.skip,
        limit=page_params.limit
        # TODO: Передати інші фільтри (статус, тип тощо) з Query параметрів сюди
    )

    return PagedResponse[TaskResponse](
        total=total_tasks,
        page=page_params.page,
        size=page_params.size,
        results=[TaskResponse.model_validate(task) for task in tasks_orm]  # Pydantic v2
    )


@router.get(
    "/{task_id}",
    response_model=TaskDetailedResponse,  # Повертаємо деталізовану відповідь
    summary="Отримання інформації про завдання за ID",  # i18n
    description="Повертає детальну інформацію про конкретне завдання. Доступно члену групи завдання або суперюзеру.",
    # i18n
    dependencies=[Depends(task_view_permission_dependency)]  # Перевірка прав
)
async def read_task_by_id(
        task_id: UUID,  # ID тепер UUID
        # current_user_with_permission: UserModel = Depends(task_view_permission_dependency), # Користувач вже в current_user з залежності
        task_service: TaskService = Depends(get_task_service)
) -> TaskDetailedResponse:
    """
    Отримує інформацію про завдання за його ID.
    Доступ контролюється залежністю `task_view_permission_dependency`.
    """
    logger.debug(f"Запит деталей завдання ID: {task_id}")
    # TaskService.get_task_by_id тепер повертає Pydantic схему
    task_details = await task_service.get_task_by_id(task_id=task_id, include_details=True)
    if not task_details:  # Малоймовірно, якщо task_view_permission_dependency не кинув 404
        logger.warning(f"Завдання з ID '{task_id}' не знайдено (після перевірки прав).")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Завдання не знайдено.")
    return task_details


@router.put(
    "/{task_id}",
    response_model=TaskDetailedResponse,
    summary="Оновлення інформації про завдання",  # i18n
    description="Дозволяє адміністратору групи завдання або суперюзеру оновити дані існуючого завдання.",  # i18n
    dependencies=[Depends(task_edit_permission_dependency)]  # Перевірка прав
)
async def update_task(
        task_id: UUID,  # ID тепер UUID
        task_in: TaskUpdate,
        current_user_with_permission: UserModel = Depends(task_edit_permission_dependency),
        task_service: TaskService = Depends(get_task_service)
) -> TaskDetailedResponse:
    """
    Оновлює дані завдання.
    Доступно адміністратору групи завдання або суперюзеру.
    """
    logger.info(f"Користувач ID '{current_user_with_permission.id}' намагається оновити завдання ID '{task_id}'.")
    try:
        updated_task = await task_service.update_task(
            task_id=task_id,
            task_update_data=task_in,
            current_user_id=current_user_with_permission.id  # Для аудиту в сервісі
        )
        # Сервіс TaskService.update_task має повертати оновлену Pydantic схему або ORM модель
        if not updated_task:  # Малоймовірно, якщо сервіс кидає винятки
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Завдання не знайдено або оновлення не вдалося.")
        return updated_task
    except ValueError as e:
        logger.warning(f"Помилка валідації при оновленні завдання ID '{task_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні завдання ID '{task_id}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення завдання",  # i18n
    description="Дозволяє адміністратору групи завдання або суперюзеру видалити завдання.",  # i18n
    dependencies=[Depends(task_edit_permission_dependency)]  # Перевірка прав
)
async def delete_task(
        task_id: UUID,  # ID тепер UUID
        current_user_with_permission: UserModel = Depends(task_edit_permission_dependency),
        task_service: TaskService = Depends(get_task_service)
):
    """
    Видаляє завдання.
    Доступно адміністратору групи завдання або суперюзеру.
    Сервіс `delete_task` має обробляти бізнес-логіку (напр., чи можна видаляти завдання з активними виконаннями).
    """
    logger.info(f"Користувач ID '{current_user_with_permission.id}' намагається видалити завдання ID '{task_id}'.")
    try:
        success = await task_service.delete_task(
            task_id=task_id,
            current_user_id=current_user_with_permission.id  # Передаємо для можливих перевірок в сервісі
        )
        if not success:  # Якщо сервіс повернув False
            logger.warning(f"Не вдалося видалити завдання ID '{task_id}' (сервіс повернув False).")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Завдання не знайдено або не вдалося видалити.")
    except ValueError as e:  # Обробка специфічних бізнес-помилок з сервісу
        logger.warning(f"Помилка бізнес-логіки при видаленні завдання ID '{task_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні завдання ID '{task_id}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    return None  # HTTP 204 No Content


logger.info(f"Роутер для CRUD операцій з завданнями визначено.")
