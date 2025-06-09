# backend/app/src/api/v1/tasks/assignments.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user
from app.src.models.auth import User as UserModel
# from app.src.models.tasks import TaskAssignment as TaskAssignmentModel # Потрібна модель призначення
from app.src.schemas.tasks.assignment import ( # Схеми для призначень
    TaskAssignmentCreate,
    TaskAssignmentResponse
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.tasks.assignment import TaskAssignmentService # Сервіс для призначень

router = APIRouter()

@router.post(
    "/", # Шлях відносно префіксу /tasks/assignments
    response_model=TaskAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового призначення задачі/події",
    description="Дозволяє адміністратору групи або суперюзеру призначити задачу або подію користувачеві."
)
async def create_task_assignment(
    assignment_in: TaskAssignmentCreate, # Включає task_id (або event_id) та user_id
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    assignment_service: TaskAssignmentService = Depends()
):
    '''
    Створює нове призначення задачі або події.

    - **task_id**: ID задачі (якщо це задача).
    - **event_id**: ID події (якщо це подія). Має бути одне з двох.
    - **user_id**: ID користувача, якому призначається.
    - **group_id**: ID групи, в контексті якої відбувається призначення (для перевірки прав).
    - ... інші поля з TaskAssignmentCreate ...
    '''
    if not hasattr(assignment_service, 'db_session') or assignment_service.db_session is None:
        assignment_service.db_session = db

    # Логіка перевірки прав та створення призначення - у сервісі
    new_assignment = await assignment_service.create_assignment(
        assignment_create_schema=assignment_in,
        requesting_user=current_user
    )
    # Сервіс має кидати HTTPException у разі помилок (не знайдено задачу/подію/користувача, заборонено, вже призначено)
    return TaskAssignmentResponse.model_validate(new_assignment)

@router.get(
    "/task/{task_id}",
    response_model=PaginatedResponse[TaskAssignmentResponse],
    summary="Список призначень для задачі",
    description="Повертає список користувачів, яким призначено вказану задачу. Доступно членам групи задачі."
)
async def list_assignments_for_task(
    task_id: int = Path(..., description="ID задачі"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    assignment_service: TaskAssignmentService = Depends()
):
    '''
    Отримує список призначень для конкретної задачі.
    '''
    if not hasattr(assignment_service, 'db_session') or assignment_service.db_session is None:
        assignment_service.db_session = db

    total_assignments, assignments = await assignment_service.get_assignments_for_task(
        task_id=task_id,
        requesting_user=current_user,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PaginatedResponse[TaskAssignmentResponse]( # Явно вказуємо тип Generic
        total=total_assignments,
        page=page_params.page,
        size=page_params.size,
        results=[TaskAssignmentResponse.model_validate(ass) for ass in assignments]
    )

@router.get(
    "/event/{event_id}",
    response_model=PaginatedResponse[TaskAssignmentResponse], # Та сама схема, якщо структура схожа
    summary="Список призначень для події",
    description="Повертає список користувачів, яким призначено вказану подію. Доступно членам групи події."
)
async def list_assignments_for_event(
    event_id: int = Path(..., description="ID події"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    assignment_service: TaskAssignmentService = Depends()
):
    '''
    Отримує список призначень для конкретної події.
    '''
    if not hasattr(assignment_service, 'db_session') or assignment_service.db_session is None:
        assignment_service.db_session = db

    total_assignments, assignments = await assignment_service.get_assignments_for_event(
        event_id=event_id,
        requesting_user=current_user,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PaginatedResponse[TaskAssignmentResponse]( # Явно вказуємо тип Generic
        total=total_assignments,
        page=page_params.page,
        size=page_params.size,
        results=[TaskAssignmentResponse.model_validate(ass) for ass in assignments]
    )

@router.get(
    "/user/{user_id}",
    response_model=PaginatedResponse[TaskAssignmentResponse],
    summary="Список задач/подій, призначених користувачу",
    description="Повертає список задач та подій, призначених вказаному користувачу. Доступно самому користувачу або адміну/суперюзеру."
)
async def list_assignments_for_user(
    user_id: int = Path(..., description="ID користувача"),
    page_params: PageParams = Depends(),
    # type: Optional[str] = Query(None, description="Фільтр за типом: 'task' або 'event'"), # Можливе розширення
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    assignment_service: TaskAssignmentService = Depends()
):
    '''
    Отримує список задач/подій, призначених вказаному користувачу.
    Перевірка прав: чи запитує користувач свої призначення, чи це адмін/суперюзер.
    '''
    if not hasattr(assignment_service, 'db_session') or assignment_service.db_session is None:
        assignment_service.db_session = db

    total_assignments, assignments = await assignment_service.get_assignments_for_user(
        user_id_target=user_id,
        requesting_user=current_user,
        skip=page_params.skip,
        limit=page_params.limit
        # type_filter=type
    )
    return PaginatedResponse[TaskAssignmentResponse]( # Явно вказуємо тип Generic
        total=total_assignments,
        page=page_params.page,
        size=page_params.size,
        results=[TaskAssignmentResponse.model_validate(ass) for ass in assignments]
    )

@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення/скасування призначення",
    description="Дозволяє адміністратору групи або суперюзеру видалити (скасувати) призначення задачі/події."
)
async def delete_task_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    assignment_service: TaskAssignmentService = Depends()
):
    '''
    Видаляє (скасовує) призначення.
    Перевірка прав - у сервісі.
    '''
    if not hasattr(assignment_service, 'db_session') or assignment_service.db_session is None:
        assignment_service.db_session = db

    success = await assignment_service.delete_assignment(
        assignment_id=assignment_id,
        requesting_user=current_user
    )
    if not success: # Сервіс має кидати HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Або 403
            detail=f"Не вдалося видалити призначення з ID {assignment_id}. Можливо, його не існує або у вас немає прав."
        )
    # HTTP 204 No Content

# Міркування:
# 1.  Схеми: `TaskAssignmentCreate`, `TaskAssignmentResponse` з `app.src.schemas.tasks.assignment`.
#     `TaskAssignmentCreate` має містити `group_id`, `user_id`, і або `task_id`, або `event_id`.
# 2.  Сервіс `TaskAssignmentService`: Керує логікою створення, отримання та видалення призначень.
#     - Валідує існування сутностей (задача, подія, користувач, група).
#     - Перевіряє права (хто може призначати, хто може переглядати).
# 3.  URL-и: Цей роутер буде підключений до `tasks_router` (в `tasks/__init__.py`)
#     з префіксом `/assignments`. Шляхи будуть, наприклад, `/api/v1/tasks/assignments/task/{task_id}`.
# 4.  Розрізнення Task/Event: `TaskAssignmentCreate` може мати `item_type: str` ('task'/'event') та `item_id: int`,
#     або окремі поля `task_id: Optional[int]` та `event_id: Optional[int]`.
#     Сервіс відповідає за правильну обробку.
# 5.  Пагінація: Для списків призначень.
# 6.  Коментарі: Українською мовою.
