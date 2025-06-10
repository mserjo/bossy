# backend/app/src/api/v1/tasks/tasks.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user # May need get_current_active_superuser for some actions
from app.src.models.auth import User as UserModel
from app.src.models.tasks import Task as TaskModel # Потрібна модель задачі
from app.src.schemas.tasks.task import ( # Схеми для задач
    TaskCreate,
    TaskUpdate,
    TaskResponse
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams # Схема для пагінації
from app.src.services.tasks.task import TaskService # Сервіс для задач
# from app.src.core.permissions import TaskPermissionsChecker # Для перевірки прав доступу до задач

router = APIRouter()

@router.post(
    "/", # Шлях відносно префіксу, який буде /tasks
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нової задачі",
    description="Дозволяє адміністратору групи або суперюзеру створити нову задачу в межах групи."
)
async def create_task(
    task_in: TaskCreate, # Очікує group_id в тілі запиту для прив'язки задачі до групи
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Повинен бути адміном групи або суперюзером
    task_service: TaskService = Depends()
):
    '''
    Створює нову задачу.

    - **title**: Назва задачі (обов'язково).
    - **description**: Опис задачі (опціонально).
    - **group_id**: ID групи, до якої належить задача (обов'язково).
    - **task_type_id**: ID типу задачі (обов'язково).
    - **due_date**: Термін виконання (опціонально).
    - **points**: Кількість балів за виконання (опціонально).
    - ... інші поля з TaskCreate ...
    '''
    if not hasattr(task_service, 'db_session') or task_service.db_session is None:
        task_service.db_session = db

    # Перевірка прав (чи є користувач адміном вказаної group_id або суперюзером) - логіка в сервісі
    created_task = await task_service.create_task(
        task_create_schema=task_in,
        requesting_user=current_user
    )
    if not created_task: # Сервіс має кидати HTTPException у разі помилок
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Або більш конкретну помилку з сервісу
            detail="Не вдалося створити задачу."
        )
    return TaskResponse.model_validate(created_task)

@router.get(
    "/",
    response_model=PaginatedResponse[TaskResponse],
    summary="Отримання списку задач",
    description="""Повертає список задач з пагінацією.
    Може фільтруватися за групою (`group_id`) або повертати задачі, доступні поточному користувачеві."""
)
async def read_tasks(
    group_id: Optional[int] = Query(None, description="ID групи для фільтрації задач"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    task_service: TaskService = Depends()
):
    '''
    Отримує список задач з пагінацією.
    Якщо `group_id` вказано, показує задачі для цієї групи (з перевіркою доступу).
    Якщо `group_id` не вказано, логіка може залежати від ролі користувача (наприклад, всі доступні йому задачі).
    '''
    if not hasattr(task_service, 'db_session') or task_service.db_session is None:
        task_service.db_session = db

    total_tasks, tasks = await task_service.get_tasks_for_user(
        user=current_user,
        group_id=group_id, # Передаємо group_id для фільтрації
        skip=page_params.skip,
        limit=page_params.limit
    )

    return PaginatedResponse[TaskResponse]( # Явно вказуємо тип Generic
        total=total_tasks,
        page=page_params.page,
        size=page_params.size,
        results=[TaskResponse.model_validate(task) for task in tasks]
    )

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Отримання інформації про задачу за ID",
    description="Повертає детальну інформацію про конкретну задачу. Доступно, якщо користувач має доступ до групи задачі."
)
async def read_task_by_id(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    task_service: TaskService = Depends()
):
    '''
    Отримує інформацію про задачу за її ID.
    Перевірка доступу до задачі (через групу) виконується в сервісі.
    '''
    if not hasattr(task_service, 'db_session') or task_service.db_session is None:
        task_service.db_session = db

    task = await task_service.get_task_by_id_for_user(task_id=task_id, user=current_user)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача з ID {task_id} не знайдена або доступ заборонено."
        )
    return TaskResponse.model_validate(task)

@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Оновлення інформації про задачу",
    description="Дозволяє адміністратору групи або суперюзеру оновити дані існуючої задачі."
)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи задачі або суперюзер
    task_service: TaskService = Depends()
):
    '''
    Оновлює дані задачі.
    Перевірка прав (чи є користувач адміном групи, до якої належить задача, або суперюзером) - у сервісі.
    '''
    if not hasattr(task_service, 'db_session') or task_service.db_session is None:
        task_service.db_session = db

    updated_task = await task_service.update_task(
        task_id=task_id,
        task_update_schema=task_in,
        requesting_user=current_user
    )
    if not updated_task: # Сервіс має кидати HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Або 403, якщо права не дозволяють
            detail=f"Задачу з ID {task_id} не знайдено або оновлення не вдалося/заборонено."
        )
    return TaskResponse.model_validate(updated_task)

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення задачі",
    description="Дозволяє адміністратору групи або суперюзеру видалити задачу."
)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи задачі або суперюзер
    task_service: TaskService = Depends()
):
    '''
    Видаляє задачу.
    Перевірка прав - у сервісі.
    '''
    if not hasattr(task_service, 'db_session') or task_service.db_session is None:
        task_service.db_session = db

    success = await task_service.delete_task(task_id=task_id, requesting_user=current_user)
    if not success: # Сервіс має кидати HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Або 403
            detail=f"Не вдалося видалити задачу з ID {task_id}. Можливо, її не існує або у вас немає прав."
        )
    # HTTP 204 No Content

# Міркування:
# 1.  Схеми: `TaskCreate`, `TaskUpdate`, `TaskResponse` з `app.src.schemas.tasks.task`.
#     `TaskCreate` має містити `group_id` для визначення, до якої групи належить задача.
# 2.  Сервіс `TaskService`: Інкапсулює бізнес-логіку та перевірку прав.
#     Методи: `create_task`, `get_tasks_for_user`, `get_task_by_id_for_user`, `update_task`, `delete_task`.
# 3.  Права доступу:
#     - Створення, оновлення, видалення: адміністратори групи, до якої належить задача, або суперюзери.
#     - Перегляд: члени групи, до якої належить задача, або суперюзери.
#     Логіка перевірки прав має бути в `TaskService`.
# 4.  Пагінація: Для списку задач. Фільтрація за `group_id` є важливим параметром.
# 5.  Коментарі: Українською мовою.
# 6.  Залежності: `get_current_active_user` для ідентифікації користувача. `TaskService = Depends()`.
# 7.  Модель `TaskModel`: Потрібна SQLAlchemy модель для задачі, що включає зв'язок з групою.
