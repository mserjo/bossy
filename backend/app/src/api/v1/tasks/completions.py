# backend/app/src/api/v1/tasks/completions.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user
from app.src.models.auth import User as UserModel
# from app.src.models.tasks import TaskCompletion as TaskCompletionModel # Потрібна модель виконання
from app.src.schemas.tasks.completion import ( # Схеми для виконань
    TaskCompletionCreateRequest, # Користувач надсилає запит на позначення виконання
    TaskCompletionResponse,      # Відповідь з інформацією про виконання
    CompletionAdminUpdateRequest # Адмін надсилає оновлення статусу (approved/rejected)
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.tasks.completion import TaskCompletionService # Сервіс для виконань

router = APIRouter()

@router.post(
    "/task/{task_id}/complete",
    response_model=TaskCompletionResponse,
    status_code=status.HTTP_201_CREATED, # Або 202 Accepted, якщо потрібна асинхронна обробка/негайне підтвердження
    summary="Позначення задачі як виконаної користувачем",
    description="Дозволяє користувачу позначити призначену йому задачу як виконану. Може потребувати підтвердження адміністратором."
)
async def mark_task_as_completed(
    task_id: int = Path(..., description="ID задачі, яку позначено як виконану"),
    completion_data: Optional[TaskCompletionCreateRequest] = None, # Може містити коментар, докази тощо.
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    completion_service: TaskCompletionService = Depends()
):
    '''
    Користувач позначає задачу як виконану.
    - `completion_data` може містити додаткову інформацію від користувача.
    - Сервіс перевіряє, чи задача призначена користувачу і чи може бути позначена як виконана.
    '''
    if not hasattr(completion_service, 'db_session') or completion_service.db_session is None:
        completion_service.db_session = db

    # Якщо completion_data не надано, створюємо порожній екземпляр або обробляємо в сервісі
    request_schema = completion_data if completion_data is not None else TaskCompletionCreateRequest()

    new_completion = await completion_service.user_mark_task_completed(
        task_id=task_id,
        requesting_user=current_user,
        completion_create_schema=request_schema
    )
    # Сервіс має кидати HTTPException у разі помилок
    return TaskCompletionResponse.model_validate(new_completion)

@router.post(
    "/event/{event_id}/complete",
    response_model=TaskCompletionResponse, # Може бути EventCompletionResponse, якщо структура відрізняється
    status_code=status.HTTP_201_CREATED,
    summary="Позначення участі/виконання події користувачем",
    description="Дозволяє користувачу позначити участь або виконання події. Може потребувати підтвердження."
)
async def mark_event_as_completed(
    event_id: int = Path(..., description="ID події, яку позначено як виконану/відвідану"),
    completion_data: Optional[TaskCompletionCreateRequest] = None, # Аналогічно до задач
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    completion_service: TaskCompletionService = Depends()
):
    '''
    Користувач позначає подію як виконану/відвідану.
    '''
    if not hasattr(completion_service, 'db_session') or completion_service.db_session is None:
        completion_service.db_session = db

    request_schema = completion_data if completion_data is not None else TaskCompletionCreateRequest()

    new_completion = await completion_service.user_mark_event_completed(
        event_id=event_id,
        requesting_user=current_user,
        completion_create_schema=request_schema # Можливо, потрібна EventCompletionCreateSchema
    )
    return TaskCompletionResponse.model_validate(new_completion)


@router.get(
    "/pending_approval",
    response_model=PaginatedResponse[TaskCompletionResponse],
    summary="Список виконань, що очікують підтвердження (Адмін/Суперюзер)",
    description="Повертає список виконань задач/подій, які потребують підтвердження адміністратором групи або суперюзером."
)
async def list_completions_pending_approval(
    group_id: Optional[int] = Query(None, description="ID групи для фільтрації"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    completion_service: TaskCompletionService = Depends()
):
    '''
    Отримує список виконань, що очікують на підтвердження.
    Доступно адміністраторам груп (фільтрація за group_id) або суперюзерам (можуть бачити для всіх груп).
    '''
    if not hasattr(completion_service, 'db_session') or completion_service.db_session is None:
        completion_service.db_session = db

    total_completions, completions = await completion_service.get_completions_pending_approval(
        requesting_user=current_user,
        group_id=group_id,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PaginatedResponse[TaskCompletionResponse]( # Явно вказуємо тип Generic
        total=total_completions,
        page=page_params.page,
        size=page_params.size,
        results=[TaskCompletionResponse.model_validate(comp) for comp in completions]
    )

@router.post(
    "/{completion_id}/approve",
    response_model=TaskCompletionResponse,
    summary="Підтвердження виконання (Адмін/Суперюзер)",
    description="Дозволяє адміністратору групи або суперюзеру підтвердити виконання задачі/події."
)
async def approve_completion(
    completion_id: int = Path(..., description="ID виконання, яке підтверджується"),
    admin_update_data: Optional[CompletionAdminUpdateRequest] = None, # Може містити коментар адміна, нараховані бали
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    completion_service: TaskCompletionService = Depends()
):
    '''
    Адміністратор підтверджує виконання.
    `admin_update_data` може містити фінальні бали, коментар тощо.
    '''
    if not hasattr(completion_service, 'db_session') or completion_service.db_session is None:
        completion_service.db_session = db

    update_schema = admin_update_data if admin_update_data is not None else CompletionAdminUpdateRequest()

    approved_completion = await completion_service.approve_completion(
        completion_id=completion_id,
        admin_user=current_user,
        admin_update_schema=update_schema
    )
    return TaskCompletionResponse.model_validate(approved_completion)

@router.post(
    "/{completion_id}/reject",
    response_model=TaskCompletionResponse,
    summary="Відхилення виконання (Адмін/Суперюзер)",
    description="Дозволяє адміністратору групи або суперюзеру відхилити виконання задачі/події."
)
async def reject_completion(
    completion_id: int = Path(..., description="ID виконання, яке відхиляється"),
    admin_update_data: Optional[CompletionAdminUpdateRequest] = None, # Має містити причину відхилення
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    completion_service: TaskCompletionService = Depends()
):
    '''
    Адміністратор відхиляє виконання.
    `admin_update_data` має містити причину відхилення.
    '''
    if not hasattr(completion_service, 'db_session') or completion_service.db_session is None:
        completion_service.db_session = db

    update_schema = admin_update_data if admin_update_data is not None else CompletionAdminUpdateRequest()
    if not update_schema.admin_comment: # Причина відхилення є важливою
        # Можна зробити це поле обов'язковим у схемі CompletionAdminUpdateRequest для reject дії
        # Або перевіряти тут / в сервісі
        # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Причина відхилення є обов'язковою.")
        pass # Припускаємо, що сервіс може мати логіку за замовчуванням або схема це валідує

    rejected_completion = await completion_service.reject_completion(
        completion_id=completion_id,
        admin_user=current_user,
        admin_update_schema=update_schema
    )
    return TaskCompletionResponse.model_validate(rejected_completion)

# Міркування:
# 1.  Схеми: `TaskCompletionCreateRequest`, `TaskCompletionResponse`, `CompletionAdminUpdateRequest` з `app.src.schemas.tasks.completion`.
# 2.  Сервіс `TaskCompletionService`: Керує логікою позначення виконання, підтвердження, відхилення.
#     - Перевіряє права (чи може користувач позначати, чи може адмін підтверджувати).
#     - Обробляє нарахування балів, зміну статусів задачі/події.
#     - Надсилає сповіщення (користувачу про підтвердження/відхилення, адміну про нове виконання на перевірку).
# 3.  URL-и: Цей роутер буде підключений до `tasks_router` (в `tasks/__init__.py`)
#     з префіксом `/completions`. Шляхи будуть, наприклад, `/api/v1/tasks/completions/task/{task_id}/complete`.
# 4.  Розділення Task/Event Completions: Ендпоінти для позначення виконання розділені для задач та подій.
#     Список на підтвердження та дії підтвердження/відхилення можуть бути спільними, якщо модель `TaskCompletion` єдина.
# 5.  Пагінація: Для списку виконань, що очікують підтвердження.
# 6.  Коментарі: Українською мовою.
