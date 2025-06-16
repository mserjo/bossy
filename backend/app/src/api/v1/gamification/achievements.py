# backend/app/src/api/v1/gamification/achievements.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перегляду досягнень користувачів (нагороджених значків-бейджів).
Також може включати функціонал для ручного нагородження (адміністраторами).

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List, Optional # Generic, TypeVar, BaseModel не потрібні, якщо імпортуються з core
from uuid import UUID # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    get_current_active_superuser, paginator
)
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.gamification.achievement import (
    UserAchievementResponse,
    ManualAchievementAwardRequest # Для ручного нагородження (якщо буде реалізовано)
)
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.services.gamification.achievement import UserAchievementService
from backend.app.src.config.logging import logger # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter(
    # Префікс /achievements буде додано в __init__.py батьківського роутера gamification
    # Теги також успадковуються/додаються звідти
)

# Залежність для отримання UserAchievementService
async def get_user_achievement_service(session: AsyncSession = Depends(get_api_db_session)) -> UserAchievementService:
    """Залежність FastAPI для отримання екземпляра UserAchievementService."""
    return UserAchievementService(db_session=session)

# ПРИМІТКА: Цей ендпоінт залежить від реалізації `list_achievements_for_user_paginated`
# в `UserAchievementService`, включаючи коректну фільтрацію за `group_id` та
# підрахунок загальної кількості для пагінації.
@router.get(
    "/me",
    response_model=PagedResponse[UserAchievementResponse],
    summary="Отримання списку моїх досягнень", # i18n
    description="Повертає список бейджів, якими було нагороджено поточного аутентифікованого користувача, з пагінацією." # i18n
)
async def list_my_achievements(
    group_id: Optional[UUID] = Query(None, description="Фільтрувати досягнення за ID групи (показує досягнення в цій групі та глобальні)"), # i18n
    page_params: PageParams = Depends(paginator),
    current_user: UserModel = Depends(get_current_active_user),
    achievement_service: UserAchievementService = Depends(get_user_achievement_service)
) -> PagedResponse[UserAchievementResponse]:
    """
    Отримує список досягнень (нагороджених бейджів) для поточного користувача.
    Може фільтруватися за групою.
    """
    logger.info(f"Користувач ID '{current_user.id}' запитує свої досягнення. Група: {group_id}, сторінка: {page_params.page}.")
    # TODO: UserAchievementService.list_achievements_for_user_paginated має повертати (items, total_count)
    achievements_orm, total_achievements = await achievement_service.list_achievements_for_user_paginated(
        user_id=current_user.id,
        group_id=group_id, # Сервіс має обробити None як "глобальні + всі групи користувача" або тільки "глобальні"
        filter_global_only= (group_id is None), # Приклад: якщо group_id не вказано, показувати тільки глобальні, або сервіс вирішує
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PagedResponse[UserAchievementResponse](
        total=total_achievements,
        page=page_params.page,
        size=page_params.size,
        results=[UserAchievementResponse.model_validate(ach) for ach in achievements_orm] # Pydantic v2
    )

# ПРИМІТКА: Важливою є реалізація гранульованої перевірки прав доступу
# (наприклад, чи є поточний користувач адміністратором групи, до якої належить
# цільовий користувач), як зазначено в TODO. Поточна залежність від
# `get_current_active_superuser` може бути недостатньою для всіх сценаріїв.
@router.get(
    "/user/{user_id_target}", # target_user_id перейменовано на user_id_target для уникнення конфлікту
    response_model=PagedResponse[UserAchievementResponse],
    summary="Список досягнень вказаного користувача (Адмін/Суперюзер)", # i18n
    description="Повертає список бейджів, нагороджених вказаному користувачу. Доступно адміністраторам відповідних груп або суперюзерам.", # i18n
    dependencies=[Depends(get_current_active_superuser)] # TODO: Замінити на більш гранульовану перевірку (адмін групи користувача)
)
async def list_user_achievements_admin( # Перейменовано
    user_id_target: UUID = Path(..., description="ID користувача, чиї досягнення запитуються"), # i18n
    group_id: Optional[UUID] = Query(None, description="Фільтрувати досягнення за ID групи"), # i18n
    page_params: PageParams = Depends(paginator),
    current_admin_user: UserModel = Depends(get_current_active_superuser), # Поточний адмін/суперюзер
    achievement_service: UserAchievementService = Depends(get_user_achievement_service)
) -> PagedResponse[UserAchievementResponse]:
    """
    Отримує список досягнень для вказаного користувача.
    Потрібна перевірка прав `current_admin_user` на перегляд даних `user_id_target` (наприклад, чи є адміном спільної групи).
    """
    # TODO: Реалізувати логіку перевірки прав в залежності або сервісі:
    #  чи може current_admin_user переглядати досягнення user_id_target (наприклад, в спільній групі).
    logger.info(f"Адмін/Суперюзер ID '{current_admin_user.id}' запитує досягнення для користувача ID '{user_id_target}'. Група: {group_id}.")
    achievements_orm, total_achievements = await achievement_service.list_achievements_for_user_paginated(
        user_id=user_id_target,
        group_id=group_id,
        filter_global_only= (group_id is None and not current_admin_user.is_superuser), # Суперюзер бачить все, якщо група не вказана
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PagedResponse[UserAchievementResponse](
        total=total_achievements,
        page=page_params.page,
        size=page_params.size,
        results=[UserAchievementResponse.model_validate(ach) for ach in achievements_orm] # Pydantic v2
    )

# ПРИМІТКА: Доступ до деталей конкретного досягнення має перевірятися.
# Поточна реалізація покладається на метод `get_user_achievement_by_id_for_user`
# в `UserAchievementService`, який має інкапсулювати цю логіку перевірки прав.
@router.get(
    "/{achievement_id}",
    response_model=UserAchievementResponse,
    summary="Отримання деталей конкретного досягнення", # i18n
    description="Повертає детальну інформацію про конкретне нагородження бейджем (запис UserAchievement)." # i18n
    # TODO: Додати залежність для перевірки прав: власник досягнення, адмін групи, або суперюзер.
)
async def get_achievement_details(
    achievement_id: UUID = Path(..., description="ID запису нагородження бейджем"), # i18n
    current_user: UserModel = Depends(get_current_active_user), # Для перевірки прав
    achievement_service: UserAchievementService = Depends(get_user_achievement_service)
) -> UserAchievementResponse:
    """
    Отримує деталі конкретного досягнення.
    Сервіс має перевірити, чи має користувач право бачити це досягнення.
    """
    logger.debug(f"Користувач ID '{current_user.id}' запитує деталі досягнення ID '{achievement_id}'.")
    # UserAchievementService.get_user_achievement_by_id має перевіряти права або повертати достатньо даних для цього.
    achievement = await achievement_service.get_user_achievement_by_id_for_user( # Потрібен такий метод
        achievement_id=achievement_id,
        requesting_user_id=current_user.id,
        is_superuser=current_user.is_superuser
    )
    if not achievement:
        logger.warning(f"Досягнення з ID '{achievement_id}' не знайдено або доступ для користувача ID '{current_user.id}' заборонено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Досягнення не знайдено або доступ заборонено.")
    return achievement


# TODO: Розглянути ендпоінт для ручного нагородження бейджем (POST)
# @router.post(
#     "/award",
#     response_model=UserAchievementResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Ручне нагородження бейджем (Адмін/Суперюзер)", # i18n
#     description="Дозволяє адміністратору або суперюзеру вручну нагородити користувача бейджем.", # i18n
#     dependencies=[Depends(get_current_active_superuser)] # Або більш гранульована перевірка прав на групу
# )
# async def manual_award_achievement(
#     award_in: ManualAchievementAwardRequest, # Схема має містити user_id, badge_id, group_id (опціонально), context_details
#     current_admin_user: UserModel = Depends(get_current_active_superuser),
#     achievement_service: UserAchievementService = Depends(get_user_achievement_service)
# ):
#     """Ручне нагородження користувача бейджем."""
#     logger.info(f"Адмін/Суперюзер ID '{current_admin_user.id}' нагороджує користувача ID '{award_in.user_id}' бейджем ID '{award_in.badge_id}'.")
#     try:
#         # UserAchievementService.award_achievement_to_user вже існує і може бути використаний тут
#         # Потрібно адаптувати UserAchievementCreate з ManualAchievementAwardRequest
#         from backend.app.src.schemas.gamification.achievement import UserAchievementCreate # Локальний імпорт
#         achievement_create_data = UserAchievementCreate(
#             group_id=award_in.group_id,
#             context_details=award_in.context_details
#         )
#         awarded_achievement = await achievement_service.award_achievement_to_user(
#             user_id=award_in.user_id,
#             badge_id=award_in.badge_id,
#             achievement_data=achievement_create_data,
#             awarded_by_user_id=current_admin_user.id
#         )
#         return awarded_achievement
#     except ValueError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) # i18n
#     except Exception as e:
#         logger.error(f"Неочікувана помилка при ручному нагородженні: {e}", exc_info=global_settings.DEBUG)
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.") # i18n

logger.info(f"Роутер для досягнень користувачів (`{router.prefix}`) визначено.")
