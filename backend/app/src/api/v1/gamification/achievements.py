# backend/app/src/api/v1/gamification/achievements.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user, get_current_active_superuser
from app.src.models.auth import User as UserModel
# from app.src.models.gamification import UserAchievement as UserAchievementModel # Потрібна модель досягнення користувача
from app.src.schemas.gamification.achievement import ( # Схеми для досягнень
    UserAchievementResponse,
    # ManualAchievementAwardRequest # Якщо буде ручне нагородження
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.gamification.achievement import UserAchievementService # Сервіс для досягнень користувачів

router = APIRouter()

@router.get(
    "/me", # Шлях відносно /gamification/achievements/me
    response_model=PaginatedResponse[UserAchievementResponse],
    summary="Отримання списку моїх досягнень (нагороджених бейджів)",
    description="Повертає список бейджів, які були нагороджені поточному аутентифікованому користувачу, з пагінацією."
)
async def list_my_achievements(
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    achievement_service: UserAchievementService = Depends()
):
    '''
    Отримує список досягнень (нагороджених бейджів) для поточного користувача.
    '''
    if not hasattr(achievement_service, 'db_session') or achievement_service.db_session is None:
        achievement_service.db_session = db

    total_achievements, achievements = await achievement_service.get_user_achievements(
        user_id=current_user.id,
        requesting_user=current_user, # Для можливої перевірки, хоча тут це сам користувач
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PaginatedResponse[UserAchievementResponse]( # Явно вказуємо тип Generic
        total=total_achievements,
        page=page_params.page,
        size=page_params.size,
        results=[UserAchievementResponse.model_validate(ach) for ach in achievements]
    )

@router.get(
    "/user/{user_id}", # Шлях відносно /gamification/achievements/user/{user_id}
    response_model=PaginatedResponse[UserAchievementResponse],
    summary="Список досягнень вказаного користувача (Адмін/Суперюзер)",
    description="Повертає список бейджів, нагороджених вказаному користувачу. Доступно адміністраторам або суперюзерам."
)
async def list_user_achievements(
    user_id: int = Path(..., description="ID користувача, чиї досягнення запитуються"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser), # Або інша адмінська перевірка
    achievement_service: UserAchievementService = Depends()
):
    '''
    Отримує список досягнень для вказаного користувача.
    Потрібна перевірка прав `current_admin_user` на перегляд даних `user_id`.
    '''
    if not hasattr(achievement_service, 'db_session') or achievement_service.db_session is None:
        achievement_service.db_session = db

    total_achievements, achievements = await achievement_service.get_user_achievements(
        user_id=user_id,
        requesting_user=current_admin_user, # Для перевірки прав в сервісі
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PaginatedResponse[UserAchievementResponse]( # Явно вказуємо тип Generic
        total=total_achievements,
        page=page_params.page,
        size=page_params.size,
        results=[UserAchievementResponse.model_validate(ach) for ach in achievements]
    )

@router.get(
    "/{achievement_id}", # Отримання конкретного екземпляру нагородження бейджем
    response_model=UserAchievementResponse,
    summary="Отримання деталей конкретного досягнення (нагородженого бейджа)",
    description="Повертає детальну інформацію про конкретне нагородження бейджем."
)
async def get_achievement_details(
    achievement_id: int = Path(..., description="ID нагородженого бейджа (запису UserAchievement)"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Для перевірки доступу
    achievement_service: UserAchievementService = Depends()
):
    '''
    Отримує деталі конкретного досягнення.
    Сервіс має перевірити, чи має користувач право бачити це досягнення.
    '''
    if not hasattr(achievement_service, 'db_session') or achievement_service.db_session is None:
        achievement_service.db_session = db

    achievement = await achievement_service.get_user_achievement_by_id(
        achievement_id=achievement_id,
        requesting_user=current_user
    )
    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Досягнення з ID {achievement_id} не знайдено або доступ заборонено."
        )
    return UserAchievementResponse.model_validate(achievement)

# @router.post(
#     "/manual_award",
#     response_model=UserAchievementResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Ручне нагородження бейджем (Адмін/Суперюзер)",
#     description="Дозволяє адміністратору або суперюзеру вручну нагородити користувача бейджем.",
#     dependencies=[Depends(get_current_active_superuser)]
# )
# async def manual_award_achievement(
#     award_in: ManualAchievementAwardRequest, # Схема має містити user_id, badge_id, причину
#     db: AsyncSession = Depends(get_db_session),
#     current_admin_user: UserModel = Depends(get_current_active_superuser),
#     achievement_service: UserAchievementService = Depends()
# ):
#     '''
#     Ручне нагородження користувача бейджем.
#     '''
#     # ... реалізація ...
#     pass


# Міркування:
# 1.  Фокус на перегляді: Основні ендпоінти для перегляду досягнень користувачів.
#     Нагородження бейджами зазвичай є результатом автоматичних процесів в системі (наприклад, досягнення певних умов, виконання завдань).
# 2.  Ручне нагородження: Закоментований приклад ендпоінту для ручного нагородження. Якщо така функціональність потрібна, її можна реалізувати.
# 3.  Схеми: `UserAchievementResponse` для представлення нагородженого бейджа.
#     `ManualAchievementAwardRequest` - якщо буде ручне нагородження.
# 4.  Сервіс `UserAchievementService`: Логіка отримання інформації про досягнення користувачів.
#     Якщо є ручне нагородження, сервіс також обробляє цю логіку.
# 5.  Права доступу:
#     - Користувачі бачать свої досягнення.
#     - Адміністратори/Суперюзери можуть бачити досягнення інших користувачів (в межах своєї видимості).
# 6.  Коментарі: Українською мовою.
# 7.  URL-и: Цей роутер буде підключений до `gamification_router` з префіксом `/achievements`.
