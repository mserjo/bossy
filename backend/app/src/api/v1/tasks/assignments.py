# backend/app/src/api/v1/tasks/assignments.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління призначеннями завдань (та потенційно подій) користувачам.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List, Optional  # Generic, TypeVar, BaseModel не потрібні тут, якщо імпортуються з core
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    # TODO: Створити/використати залежності для перевірки прав, наприклад:
    #  `require_item_admin_or_superuser(item_id: UUID, item_type: str)`
    #  `require_item_viewer_or_superuser(item_id: UUID, item_type: str)`
    paginator
)
from backend.app.src.api.v1.groups.groups import check_group_edit_permission, check_group_view_permission  # Тимчасово

from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.tasks.assignment import (
    TaskAssignmentCreateBody,  # Схема для тіла запиту: user_id
    TaskAssignmentResponse
)
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.services.tasks.assignment import TaskAssignmentService
from backend.app.src.services.tasks.task import TaskService  # Для отримання group_id завдання
from backend.app.src.services.tasks.event import EventService  # Для отримання group_id події
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter(
    # Префікс /assignments буде додано в __init__.py батьківського роутера tasks
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання TaskAssignmentService
async def get_task_assignment_service(session: AsyncSession = Depends(get_api_db_session)) -> TaskAssignmentService:
    """Залежність FastAPI для отримання екземпляра TaskAssignmentService."""
    return TaskAssignmentService(db_session=session)


# Залежність для TaskService (для перевірки прав через групу завдання)
async def get_task_service_dep(session: AsyncSession = Depends(get_api_db_session)) -> TaskService:
    return TaskService(db_session=session)


# Залежність для EventService (для перевірки прав через групу події)
async def get_event_service_dep(session: AsyncSession = Depends(get_api_db_session)) -> EventService:
    return EventService(db_session=session)

# ПРИМІТКА: Ця залежність призначена для перевірки прав на редагування призначень
# до завдання. Поточна реалізація є неповною і потребує доопрацювання
# логіки перевірки прав адміністратора групи завдання або суперюзера,
# як зазначено в TODO.
# Допоміжна залежність для перевірки прав на редагування призначень до завдання
async def task_assignment_edit_dependency(
        task_id: UUID = Path(..., description="ID Завдання"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        task_service: TaskService = Depends(get_task_service_dep),
        # Використовуємо check_group_edit_permission, передаючи group_id завдання
        # Це потребує, щоб check_group_edit_permission був адаптований або викликався з group_id
) -> UserModel:
    task_orm = await task_service.get_task_orm_by_id(task_id)
    if not task_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Завдання не знайдено")  # i18n
    # Тепер викликаємо check_group_edit_permission для групи цього завдання
    # Це припускає, що check_group_edit_permission може бути використаний так,
    # або потрібно створити нову залежність, що інкапсулює цю логіку.
    # Для простоти, припустимо, що ми передаємо group_id в залежність, яка неявно використовується.
    # Або, якщо check_group_edit_permission приймає group_id:
    # await check_group_edit_permission(group_id=task_orm.group_id, current_user=current_user, ...)
    # Поки що, для прикладу, просто повертаємо користувача, якщо завдання знайдено,
    # а реальна перевірка прав адміна групи завдання має бути реалізована.
    # TODO: Реалізувати належну перевірку прав: current_user має бути адміном task_orm.group_id або суперюзером.
    # Наприклад, за допомогою `check_group_edit_permission(group_id=task_orm.group_id, ...)`
    if not current_user.is_superuser:  # Спрощена перевірка, потрібна перевірка адміна групи
        logger.warning(
            f"Користувач {current_user.id} не суперюзер, потрібна перевірка адміна групи завдання {task_id}.")
    return current_user


@router.post(
    "/task/{task_id}",  # Шлях: /assignments/task/{task_id}
    response_model=TaskAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Призначення завдання користувачеві (Адмін)",  # i18n
    description="Дозволяє адміністратору групи завдання або суперюзеру призначити завдання користувачеві."  # i18n
)
# ПРИМІТКА: Безпека цього ендпоінта залежить від коректної реалізації
# залежності `task_assignment_edit_dependency` для перевірки прав.
async def assign_task_to_user_endpoint(  # Перейменовано
        task_id: UUID = Path(..., description="ID завдання для призначення"),  # i18n
        assignment_in: TaskAssignmentCreateBody,  # Тіло запиту з user_id
        # TODO: Замінити current_user на залежність, що перевіряє права адміна групи завдання або суперюзера
        current_admin_or_superuser: UserModel = Depends(task_assignment_edit_dependency),  # Використовуємо залежність
        assignment_service: TaskAssignmentService = Depends(get_task_assignment_service)
) -> TaskAssignmentResponse:
    """
    Призначає завдання користувачеві.
    Вимагає прав адміністратора групи завдання або суперюзера.
    """
    logger.info(
        f"Адмін/Суперюзер ID '{current_admin_or_superuser.id}' призначає завдання ID '{task_id}' користувачу ID '{assignment_in.user_id}'.")
    try:
        new_assignment = await assignment_service.assign_task_to_user(
            task_id=task_id,
            user_id=assignment_in.user_id,
            assigned_by_user_id=current_admin_or_superuser.id
        )
        return new_assignment
    except ValueError as e:
        logger.warning(f"Помилка призначення завдання ID '{task_id}' користувачу '{assignment_in.user_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка: {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/task/{task_id}",  # Шлях: /assignments/task/{task_id}
    response_model=PagedResponse[TaskAssignmentResponse],
    summary="Список призначень для завдання",  # i18n
    description="Повертає список користувачів, яким призначено вказане завдання. Доступно членам групи завдання.",
    # i18n
    # TODO: Додати залежність для перевірки прав перегляду (член групи завдання або суперюзер)
)
# ПРИМІТКА: Для цього ендпоінта необхідно реалізувати залежність, що перевіряє
# права поточного користувача на перегляд призначень для завдання (наприклад,
# чи є він членом групи, до якої належить завдання, або суперюзером).
# Також, сервіс має коректно обробляти пагінацію.
async def list_assignments_for_task_endpoint(  # Перейменовано
        task_id: UUID = Path(..., description="ID завдання"),  # i18n
        page_params: PageParams = Depends(paginator),
        # current_user: UserModel = Depends(get_current_active_user), # Для перевірки прав
        assignment_service: TaskAssignmentService = Depends(get_task_assignment_service)
) -> PagedResponse[TaskAssignmentResponse]:
    """Отримує список призначень для конкретного завдання."""
    # TODO: Перевірити права доступу поточного користувача до завдання task_id
    logger.debug(f"Запит списку призначень для завдання ID '{task_id}'.")
    # TODO: TaskAssignmentService.list_assignments_for_task має повертати (items, total_count)
    assignments_orm, total_assignments = await assignment_service.list_assignments_for_task_paginated(
        task_id=task_id,
        skip=page_params.skip,
        limit=page_params.limit,
        is_active=True  # За замовчуванням показуємо тільки активні призначення
    )
    return PagedResponse[TaskAssignmentResponse](
        total=total_assignments,
        page=page_params.page,
        size=page_params.size,
        results=[TaskAssignmentResponse.model_validate(ass) for ass in assignments_orm]  # Pydantic v2
    )


# TODO: Додати аналогічні ендпоінти для призначення Подій (/event/{event_id}), якщо потрібно,
#  або зробити TaskAssignmentCreate більш гнучким з `item_id` та `item_type`.

@router.get(
    "/user/{user_id_target}",  # Шлях: /assignments/user/{user_id_target}
    response_model=PagedResponse[TaskAssignmentResponse],
    summary="Список завдань/подій, призначених користувачу",  # i18n
    description="""Повертає список завдань та подій, призначених вказаному користувачу.
    Доступно самому користувачу для своїх призначень, або суперюзеру для будь-якого користувача."""  # i18n
)
# ПРИМІТКА: Цей ендпоінт дозволяє користувачу переглядати власні призначення
# або суперюзеру переглядати призначення будь-кого. Важливою є коректна
# реалізація пагінації в сервісному шарі.
async def list_assignments_for_user_endpoint(  # Перейменовано
        user_id_target: UUID = Path(..., description="ID користувача, чиї призначення переглядаються"),  # i18n
        page_params: PageParams = Depends(paginator),
        current_user: UserModel = Depends(get_current_active_user),
        assignment_service: TaskAssignmentService = Depends(get_task_assignment_service)
) -> PagedResponse[TaskAssignmentResponse]:
    """Отримує список завдань/подій, призначених вказаному користувачеві."""
    logger.debug(f"Користувач ID '{current_user.id}' запитує призначення для користувача ID '{user_id_target}'.")
    if user_id_target != current_user.id and not current_user.is_superuser:
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Ви можете переглядати тільки власні призначення.")

    # TODO: TaskAssignmentService.list_tasks_for_user має повертати (items, total_count)
    assignments_orm, total_assignments = await assignment_service.list_items_for_user_paginated(
        user_id=user_id_target,
        skip=page_params.skip,
        limit=page_params.limit,
        is_active_assignment=True  # За замовчуванням тільки активні
    )
    return PagedResponse[TaskAssignmentResponse](
        total=total_assignments,
        page=page_params.page,
        size=page_params.size,
        results=[TaskAssignmentResponse.model_validate(ass) for ass in assignments_orm]  # Pydantic v2
    )


@router.delete(
    "/{task_id}/user/{user_id_to_unassign}",  # Шлях: /assignments/{task_id}/user/{user_id_to_unassign}
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення/скасування призначення завдання користувачеві (Адмін)",  # i18n
    description="Дозволяє адміністратору групи завдання або суперюзеру скасувати призначення завдання користувачеві."
    # i18n
)
# ПРИМІТКА: Скасування призначення завдання, як і його створення, залежить від
# коректної реалізації перевірки прав через `task_assignment_edit_dependency`.
async def unassign_task_from_user_endpoint(  # Перейменовано
        task_id: UUID = Path(..., description="ID завдання"),  # i18n
        user_id_to_unassign: UUID = Path(..., description="ID користувача, якого потрібно відкріпити"),  # i18n
        # TODO: Замінити current_user на залежність, що перевіряє права адміна групи завдання або суперюзера
        current_admin_or_superuser: UserModel = Depends(task_assignment_edit_dependency),
        # Використовуємо залежність для завдання
        assignment_service: TaskAssignmentService = Depends(get_task_assignment_service)
):
    """
    Скасовує призначення завдання користувачеві (встановлює is_active=False).
    Вимагає прав адміністратора групи завдання або суперюзера.
    """
    logger.info(
        f"Адмін/Суперюзер ID '{current_admin_or_superuser.id}' скасовує призначення завдання ID '{task_id}' для користувача ID '{user_id_to_unassign}'.")
    try:
        success = await assignment_service.unassign_task_from_user(
            task_id=task_id,
            user_id=user_id_to_unassign,
            unassigned_by_user_id=current_admin_or_superuser.id
        )
        if not success:
            logger.warning(
                f"Не вдалося скасувати призначення завдання ID '{task_id}' для користувача ID '{user_id_to_unassign}' (сервіс повернув False).")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Призначення не знайдено або вже неактивне.")
    except ValueError as e:
        logger.warning(f"Помилка скасування призначення: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n

    return None  # HTTP 204 No Content


# TODO: Розглянути, чи потрібен окремий ендпоінт для видалення призначення за ID самого призначення (`assignment_id`),
#  або поточна логіка через task_id/user_id є достатньою.
#  Якщо за `assignment_id`, то шлях може бути просто `/{assignment_id}`.

logger.info("Роутер для управління призначеннями завдань (`/assignments`) визначено.")
