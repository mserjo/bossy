# backend/app/src/api/v1/tasks/reviews.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user
from app.src.models.auth import User as UserModel
# from app.src.models.tasks import TaskReview as TaskReviewModel # Потрібна модель відгуку
from app.src.schemas.tasks.review import ( # Схеми для відгуків
    TaskReviewCreate,
    TaskReviewUpdate, # Може бути не потрібна, якщо create_or_update_task_review використовує TaskReviewCreate
    TaskReviewResponse
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.tasks.review import TaskReviewService # Сервіс для відгуків

router = APIRouter()

@router.post(
    "/task/{task_id}", # Шлях відносно префіксу /tasks/reviews
    response_model=TaskReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення або оновлення відгуку на задачу",
    description="Дозволяє користувачу залишити або оновити свій відгук (рейтинг, коментар) на задачу, з якою він взаємодіяв."
)
async def create_or_update_task_review(
    task_id: int = Path(..., description="ID задачі, для якої залишається відгук"),
    review_in: TaskReviewCreate, # Або схема, що дозволяє і створення, і оновлення
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    review_service: TaskReviewService = Depends()
):
    '''
    Створює новий відгук або оновлює існуючий відгук користувача на задачу.
    - Сервіс має перевірити, чи користувач може залишити відгук (наприклад, чи була йому призначена задача, чи він її виконав).
    - Зазвичай один користувач = один відгук на задачу.
    '''
    if not hasattr(review_service, 'db_session') or review_service.db_session is None:
        review_service.db_session = db

    # Логіка створення/оновлення відгуку - у сервісі
    # Сервіс може вирішувати, чи створювати новий, чи оновлювати існуючий відгук від цього користувача для цієї задачі.
    review = await review_service.create_or_update_review(
        task_id=task_id,
        review_create_schema=review_in, # TaskReviewCreate може містити rating, comment
        requesting_user=current_user
    )
    # Сервіс має кидати HTTPException у разі помилок
    return TaskReviewResponse.model_validate(review)

@router.get(
    "/task/{task_id}",
    response_model=PaginatedResponse[TaskReviewResponse],
    summary="Список відгуків для задачі",
    description="Повертає список відгуків для вказаної задачі з пагінацією. Доступно користувачам, що мають доступ до задачі."
)
async def list_reviews_for_task(
    task_id: int = Path(..., description="ID задачі"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Для перевірки доступу до задачі
    review_service: TaskReviewService = Depends()
):
    '''
    Отримує список відгуків для конкретної задачі.
    '''
    if not hasattr(review_service, 'db_session') or review_service.db_session is None:
        review_service.db_session = db

    total_reviews, reviews = await review_service.get_reviews_for_task(
        task_id=task_id,
        requesting_user=current_user, # Сервіс може перевірити, чи користувач має доступ до задачі, щоб бачити відгуки
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PaginatedResponse[TaskReviewResponse]( # Явно вказуємо тип Generic
        total=total_reviews,
        page=page_params.page,
        size=page_params.size,
        results=[TaskReviewResponse.model_validate(rev) for rev in reviews]
    )

@router.get(
    "/{review_id}", # Отримання конкретного відгуку за його ID
    response_model=TaskReviewResponse,
    summary="Отримання конкретного відгуку за ID",
    description="Повертає деталі конкретного відгуку. Доступно автору відгуку, адміну групи або суперюзеру."
)
async def get_task_review_by_id(
    review_id: int = Path(..., description="ID відгуку"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    review_service: TaskReviewService = Depends()
):
    '''
    Отримує відгук за його ID.
    '''
    if not hasattr(review_service, 'db_session') or review_service.db_session is None:
        review_service.db_session = db

    review = await review_service.get_review_by_id(
        review_id=review_id,
        requesting_user=current_user # Сервіс перевіряє права доступу
    )
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Відгук не знайдено або доступ заборонено.")
    return TaskReviewResponse.model_validate(review)


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення відгуку",
    description="Дозволяє автору відгуку, адміністратору групи або суперюзеру видалити відгук."
)
async def delete_task_review(
    review_id: int = Path(..., description="ID відгуку, який видаляється"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Автор, адмін групи або суперюзер
    review_service: TaskReviewService = Depends()
):
    '''
    Видаляє відгук.
    Перевірка прав (чи є користувач автором відгуку, адміном групи задачі, або суперюзером) - у сервісі.
    '''
    if not hasattr(review_service, 'db_session') or review_service.db_session is None:
        review_service.db_session = db

    success = await review_service.delete_review(
        review_id=review_id,
        requesting_user=current_user
    )
    if not success: # Сервіс має кидати HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Або 403
            detail=f"Не вдалося видалити відгук з ID {review_id}. Можливо, його не існує або у вас немає прав."
        )
    # HTTP 204 No Content

# Міркування:
# 1.  Схеми: `TaskReviewCreate`, `TaskReviewUpdate` (може бути об'єднано з Create), `TaskReviewResponse` з `app.src.schemas.tasks.review`.
# 2.  Сервіс `TaskReviewService`: Керує логікою створення, отримання та видалення відгуків.
#     - Перевіряє права (хто може залишати відгук, хто може видаляти).
#     - Обробляє логіку "один користувач - один відгук на задачу" (upsert логіка).
# 3.  URL-и: Цей роутер буде підключений до `tasks_router` (в `tasks/__init__.py`)
#     з префіксом `/reviews`. Шляхи будуть, наприклад, `/api/v1/tasks/reviews/task/{task_id}`.
# 4.  Фокус на задачах: Поки що відгуки реалізовані тільки для задач (`Task`). Якщо потрібні відгуки для подій,
#     структура може бути розширена або дубльована.
# 5.  Пагінація: Для списку відгуків.
# 6.  Коментарі: Українською мовою.
