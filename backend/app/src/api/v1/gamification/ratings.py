# backend/app/src/api/v1/gamification/ratings.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user # May need get_current_active_superuser
from app.src.models.auth import User as UserModel
# from app.src.models.gamification import UserGroupRating as UserGroupRatingModel # Потрібна модель рейтингу
from app.src.schemas.gamification.rating import ( # Схеми для рейтингів
    UserGroupRatingResponse
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.gamification.rating import UserRatingService # Сервіс для рейтингів

router = APIRouter()

@router.get(
    "/group/{group_id}", # Шлях відносно /gamification/ratings/group/{group_id}
    response_model=PaginatedResponse[UserGroupRatingResponse],
    summary="Отримання рейтингу користувачів у групі (лідерборд)",
    description="Повертає відсортований список користувачів у вказаній групі на основі їхніх балів або іншого критерію рейтингу, з пагінацією."
)
async def get_group_ratings_leaderboard(
    group_id: int = Path(..., description="ID групи, для якої запитується лідерборд"),
    page_params: PageParams = Depends(),
    # sort_by: Optional[str] = Query("points", description="Поле для сортування (наприклад, 'points', 'tasks_completed')"), # Майбутнє розширення
    # sort_order: Optional[str] = Query("desc", description="Порядок сортування ('asc' або 'desc')"), # Майбутнє розширення
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Для перевірки доступу до групи
    rating_service: UserRatingService = Depends()
):
    '''
    Отримує лідерборд (рейтинг користувачів) для вказаної групи.
    Користувач повинен бути членом групи або мати відповідні права для перегляду.
    '''
    if not hasattr(rating_service, 'db_session') or rating_service.db_session is None:
        rating_service.db_session = db

    # Логіка отримання та сортування рейтингу - у сервісі
    # Сервіс також перевіряє права current_user на перегляд рейтингу цієї групи
    total_ratings, ratings = await rating_service.get_group_leaderboard(
        group_id=group_id,
        requesting_user=current_user,
        skip=page_params.skip,
        limit=page_params.limit
        # sort_by=sort_by,
        # sort_order=sort_order
    )

    return PaginatedResponse[UserGroupRatingResponse]( # Явно вказуємо тип Generic
        total=total_ratings,
        page=page_params.page,
        size=page_params.size,
        results=[UserGroupRatingResponse.model_validate(rating) for rating in ratings]
    )

@router.get(
    "/me/group/{group_id}", # Шлях відносно /gamification/ratings/me/group/{group_id}
    response_model=UserGroupRatingResponse, # Або якась більш детальна схема з позицією в рейтингу
    summary="Отримання рейтингової інформації поточного користувача в групі",
    description="Повертає інформацію про рейтинг поточного користувача (наприклад, бали, позиція) у вказаній групі."
)
async def get_my_rating_in_group(
    group_id: int = Path(..., description="ID групи"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    rating_service: UserRatingService = Depends()
):
    '''
    Отримує рейтингову інформацію поточного користувача для конкретної групи.
    '''
    if not hasattr(rating_service, 'db_session') or rating_service.db_session is None:
        rating_service.db_session = db

    rating_info = await rating_service.get_user_rating_in_group(
        user_id=current_user.id,
        group_id=group_id,
        requesting_user=current_user # Для перевірки членства в групі
    )
    if not rating_info:
        # Може означати, що користувач не в групі, або для нього ще немає рейтингових даних
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рейтингову інформацію для поточного користувача в групі ID {group_id} не знайдено."
        )
    return UserGroupRatingResponse.model_validate(rating_info)

# Міркування:
# 1.  Фокус на перегляді: API для рейтингів переважно для читання даних.
#     Розрахунок рейтингів та їх оновлення - це зазвичай внутрішня логіка сервісів,
#     яка може запускатися періодично або при певних діях (наприклад, завершення задачі).
# 2.  Схеми: `UserGroupRatingResponse` для представлення позиції користувача в рейтингу групи.
# 3.  Сервіс `UserRatingService`: Відповідає за отримання та форматування даних рейтингів.
#     Може взаємодіяти з іншими сервісами для отримання даних (наприклад, балів з UserAccountService).
# 4.  Права доступу:
#     - Лідерборд групи: Члени групи або адміністратори/суперюзери.
#     - Свій рейтинг в групі: Сам користувач (якщо він член групи).
# 5.  Сортування та фільтрація: Лідерборди можуть потребувати параметрів сортування (за балами, за кількістю виконаних завдань тощо).
#     Це позначено як майбутнє розширення.
# 6.  Коментарі: Українською мовою.
# 7.  URL-и: Цей роутер буде підключений до `gamification_router` з префіксом `/ratings`.
