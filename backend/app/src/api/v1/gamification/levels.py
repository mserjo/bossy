# backend/app/src/api/v1/gamification/levels.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління визначеннями Рівнів та перегляду рівнів користувачів.

- Визначення рівнів (CRUD): Доступно адміністраторам/суперкористувачам.
- Рівні користувачів (перегляд): Користувачі бачать свій рівень, адміни/СУ - рівні інших.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List, Optional  # Generic, TypeVar, BaseModel не потрібні, якщо імпортуються з core
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    get_current_active_superuser, paginator, get_group_membership_service
)
# TODO: Створити/використати гранульовані залежності для прав доступу
from backend.app.src.api.v1.groups.groups import check_group_edit_permission, check_group_view_permission  # Тимчасово

from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.gamification.level import (
    LevelCreate, LevelUpdate, LevelResponse, UserLevelResponse
)
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.services.gamification.level import LevelService
from backend.app.src.services.gamification.user_level import UserLevelService
from backend.app.src.services.groups.group import GroupService  # Для перевірки групи при створенні/фільтрації
from backend.app.src.services.groups.membership import GroupMembershipService
from backend.app.src.config import settings as global_settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter(
    # Префікс /levels буде додано в __init__.py батьківського роутера gamification
    # Теги також успадковуються/додаються звідти
)


# --- Залежності для сервісів ---
async def get_level_service(session: AsyncSession = Depends(get_api_db_session)) -> LevelService:
    """Залежність FastAPI для отримання екземпляра LevelService."""
    return LevelService(db_session=session)


async def get_user_level_service(session: AsyncSession = Depends(get_api_db_session)) -> UserLevelService:
    """Залежність FastAPI для отримання екземпляра UserLevelService."""
    return UserLevelService(db_session=session)


async def get_group_service_dep(session: AsyncSession = Depends(get_api_db_session)) -> GroupService:
    return GroupService(db_session=session)


# --- Ендпоінти для управління визначеннями рівнів (Level Definitions) ---
definitions_router = APIRouter()

# ПРИМІТКА: Створення визначення рівня потребує ретельної перевірки прав доступу
# (адміністратор групи або суперюзер). Логіка створення також залежить від
# можливостей `LevelService` та `BaseDictionaryService` (наприклад, `created_by_user_id`).
@definitions_router.post(
    "/",
    response_model=LevelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового визначення рівня (Адмін/Суперюзер)",  # i18n
    description="""Дозволяє адміністратору групи (для рівнів своєї групи) або суперюзеру
    (для будь-яких рівнів, включаючи глобальні) створити нове визначення рівня."""  # i18n
)
async def create_level_definition(
        level_in: LevelCreate,  # Схема містить group_id (опціонально)
        current_user: UserModel = Depends(get_current_active_user),
        level_service: LevelService = Depends(get_level_service),
        # group_service: GroupService = Depends(get_group_service_dep) # Для перевірки прав на групу
        membership_service: GroupMembershipService = Depends(get_group_membership_service)  # Оновлено залежність
):
    """
    Створює нове визначення рівня.
    Якщо `level_in.group_id` вказано, користувач має бути адміном цієї групи або суперюзером.
    Якщо `level_in.group_id` не вказано (глобальний рівень), тільки суперюзер може його створити.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' намагається створити рівень '{level_in.name}'. Група: {level_in.group_id or 'Глобальний'}.")

    # Перевірка прав
    if level_in.group_id:
        if not current_user.is_superuser:
            membership = await membership_service.get_membership_details(group_id=level_in.group_id,
                                                                         user_id=current_user.id)
            if not membership or not membership.is_active or membership.role.code != "ADMIN":  # ADMIN_ROLE_CODE
                # i18n
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Ви не є адміністратором вказаної групи для створення рівня.")
    elif not current_user.is_superuser:
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Тільки суперкористувачі можуть створювати глобальні рівні.")

    try:
        # LevelService.create (успадкований та розширений) має обробляти унікальність name та min_points_required
        # в межах group_id/глобально, та валідувати пов'язані ID (icon_file_id).
        created_level = await level_service.create(data=level_in, created_by_user_id=current_user.id)
        return created_level
    except ValueError as e:
        logger.warning(f"Помилка створення рівня '{level_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні рівня '{level_in.name}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@definitions_router.get(
    "/",
    response_model=PagedResponse[LevelResponse],
    summary="Отримання списку визначень рівнів",  # i18n
    description="""Повертає список визначень рівнів з пагінацією.
    Доступно всім автентифікованим користувачам. Фільтрується за групою (`group_id`),
    показуючи глобальні рівні та рівні вказаної групи."""  # i18n
)
# ПРИМІТКА: Фільтрація та пагінація визначень рівнів залежать від реалізації
# `LevelService.list_levels_paginated`, включаючи обробку прав доступу
# та коректний підрахунок загальної кількості елементів.
async def read_level_definitions(
        group_id: Optional[UUID] = Query(None, description="ID групи для фільтрації (показує рівні групи + глобальні)"),
        # i18n
        page_params: PageParams = Depends(paginator),
        current_user: UserModel = Depends(get_current_active_user),  # Для контексту доступу
        level_service: LevelService = Depends(get_level_service)
) -> PagedResponse[LevelResponse]:
    """
    Отримує список визначень рівнів.
    Користувачі бачать глобальні рівні та рівні груп, до яких вони належать (якщо group_id вказано і вони члени).
    Суперюзери бачать усі рівні.
    """
    logger.debug(f"Користувач ID '{current_user.id}' запитує список визначень рівнів. Група: {group_id}.")
    # TODO: LevelService.list_levels_paginated має враховувати права current_user та group_id.
    levels_orm, total_levels = await level_service.list_levels_paginated(
        requesting_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        group_id_filter=group_id,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PagedResponse[LevelResponse](
        total=total_levels,
        page=page_params.page,
        size=page_params.size,
        results=[LevelResponse.model_validate(lvl) for lvl in levels_orm]  # Pydantic v2
    )


# ПРИМІТКА: Ця залежність перевіряє права доступу до конкретного визначення рівня.
# Логіка враховує суперкористувача, належність до групи (якщо рівень груповий)
# та доступність глобальних рівнів.
async def check_level_def_access_permission(  # Залежність для перевірки прав на конкретне визначення рівня
        level_id: UUID = Path(..., description="ID визначення рівня"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        level_service: LevelService = Depends(get_level_service),
        membership_service: GroupMembershipService = Depends(get_group_membership_service) # Оновлено залежність
) -> LevelResponse:
    level = await level_service.get_by_id(item_id=level_id)
    if not level:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Визначення рівня не знайдено.")  # i18n
    if current_user.is_superuser:
        return level
    if level.group_id:
        membership = await membership_service.get_membership_details(group_id=level.group_id, user_id=current_user.id)
        if not membership or not membership.is_active:
            # i18n
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Ви не маєте доступу до цього групового визначення рівня.")
    return level  # Глобальні рівні доступні всім автентифікованим


@definitions_router.get(
    "/{level_id}",  # Змінено з level_def_id
    response_model=LevelResponse,
    summary="Отримання інформації про визначення рівня за ID",  # i18n
    description="""Повертає детальну інформацію про конкретне визначення рівня.
    Доступно, якщо рівень глобальний або користувач є членом групи рівня.""",  # i18n
    dependencies=[Depends(check_level_def_access_permission)]
)
async def read_level_definition_by_id(
        level_id: UUID,  # Змінено з level_def_id
        retrieved_level: LevelResponse = Depends(check_level_def_access_permission)
) -> LevelResponse:
    """Отримує інформацію про визначення рівня за його ID."""
    logger.debug(f"Запит деталей визначення рівня ID: {level_id}.")
    return retrieved_level


# ПРИМІТКА: Ця залежність перевіряє права на редагування/видалення визначення рівня.
# Вона гарантує, що тільки адміністратори відповідної групи або суперкористувачі
# можуть вносити зміни або видаляти рівні.
async def check_level_def_edit_permission(
        level_id: UUID = Path(..., description="ID визначення рівня"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        level_service: LevelService = Depends(get_level_service),
        membership_service: GroupMembershipService = Depends(get_group_membership_service) # Оновлено залежність
) -> LevelResponse:
    level = await level_service.get_by_id(item_id=level_id)
    if not level:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Визначення рівня не знайдено.")  # i18n
    if current_user.is_superuser:
        return level
    if level.group_id:
        membership = await membership_service.get_membership_details(group_id=level.group_id, user_id=current_user.id)
        if not membership or not membership.is_active or membership.role.code != "ADMIN":  # ADMIN_ROLE_CODE
            # i18n
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Ви не є адміністратором групи цього визначення рівня.")
    else:  # Глобальний рівень може редагувати тільки суперюзер
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Тільки суперкористувачі можуть редагувати глобальні визначення рівнів.")
    return level


@definitions_router.put(
    "/{level_id}",  # Змінено з level_def_id
    response_model=LevelResponse,
    summary="Оновлення визначення рівня (Адмін/Суперюзер)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру оновити існуюче визначення рівня.",  # i18n
    dependencies=[Depends(check_level_def_edit_permission)]
)
async def update_level_definition(
        level_id: UUID,  # Змінено з level_def_id
        level_in: LevelUpdate,
        # retrieved_level_for_update: LevelResponse = Depends(check_level_def_edit_permission), # Не використовується прямо
        current_user: UserModel = Depends(get_current_active_user),  # Для updated_by_user_id
        level_service: LevelService = Depends(get_level_service)
) -> LevelResponse:
    """Оновлює дані визначення рівня."""
    logger.info(f"Користувач ID '{current_user.id}' намагається оновити визначення рівня ID '{level_id}'.")
    try:
        updated_level = await level_service.update(
            item_id=level_id, data=level_in, updated_by_user_id=current_user.id
        )
        if not updated_level:  # Малоймовірно
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Визначення рівня не знайдено для оновлення.")
        return updated_level
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка: {e}", exc_info=global_settings.DEBUG)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера.")  # i18n


@definitions_router.delete(
    "/{level_id}",  # Змінено з level_def_id
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення визначення рівня (Адмін/Суперюзер)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру видалити визначення рівня.",  # i18n
    dependencies=[Depends(check_level_def_edit_permission)]
)
# ПРИМІТКА: Видалення визначення рівня є критичною операцією. Необхідно забезпечити,
# щоб сервіс `LevelService.delete` перевіряв, чи не використовується рівень
# в активних `UserLevel` записах або інших залежностях, як зазначено в TODO.
async def delete_level_definition(
        level_id: UUID,  # Змінено з level_def_id
        current_user: UserModel = Depends(get_current_active_user),  # Для логування
        level_service: LevelService = Depends(get_level_service)
):
    """Видаляє визначення рівня."""
    logger.info(f"Користувач ID '{current_user.id}' намагається видалити визначення рівня ID '{level_id}'.")
    try:
        # TODO: LevelService.delete має перевіряти, чи не використовується рівень в UserLevel або інших залежностях.
        success = await level_service.delete(item_id=level_id)
        if not success:
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не вдалося видалити визначення рівня.")
    except ValueError as e:  # Наприклад, якщо рівень використовується
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n

    return None


# --- Ендпоінти для перегляду рівнів користувачів (User Levels) ---
user_levels_router = APIRouter()


@user_levels_router.get(
    "/me",
    response_model=List[UserLevelResponse],  # Користувач може мати рівні в різних групах + глобальний
    summary="Отримання поточних рівнів користувача",  # i18n
    description="Повертає інформацію про поточні рівні аутентифікованого користувача (глобальний та в групах)."  # i18n
)
# ПРИМІТКА: Повна реалізація отримання всіх рівнів користувача (глобального та групових)
# залежить від доопрацювання логіки в `UserLevelService` та отримання списку груп користувача,
# як зазначено в TODO.
async def get_my_user_levels(  # Перейменовано
        group_id: Optional[UUID] = Query(None,
                                         description="ID групи для фільтрації (показати рівень тільки для цієї групи або глобальний, якщо не вказано)"),
        # i18n
        current_user: UserModel = Depends(get_current_active_user),
        user_level_service: UserLevelService = Depends(get_user_level_service)
) -> List[UserLevelResponse]:
    """Отримує поточний(і) рівень(ні) користувача."""
    logger.debug(f"Користувач ID '{current_user.id}' запитує свої рівні. Контекст групи: {group_id}.")
    # TODO: UserLevelService.get_user_levels має повертати список, якщо group_id не вказано (всі рівні користувача).
    #  Або один рівень, якщо group_id вказано (чи None для глобального).
    #  Поточна реалізація UserLevelService.get_user_level повертає один Optional[UserLevelResponse].

    user_level_responses: List[UserLevelResponse] = []
    if group_id is not None:  # Запит рівня для конкретної групи
        user_level = await user_level_service.get_user_level(user_id=current_user.id, group_id=group_id)
        if user_level: user_level_responses.append(user_level)
    else:  # Запит всіх рівнів користувача (глобальний + всі групові)
        # Спочатку глобальний
        global_level = await user_level_service.get_user_level(user_id=current_user.id, group_id=None)
        if global_level: user_level_responses.append(global_level)
        # Потім групові (потребує отримання списку груп користувача)
        # TODO: Додати отримання групових рівнів.
        logger.warning("Отримання всіх групових рівнів для /me ще не реалізовано повністю.")

    if not user_level_responses:
        logger.info(f"Інформацію про рівні для користувача ID '{current_user.id}' (група: {group_id}) не знайдено.")
        # Це не помилка, користувач може просто не мати рівня.
    return user_level_responses


@user_levels_router.get(
    "/{user_id_target}",  # Змінено з user_id
    response_model=List[UserLevelResponse],
    summary="Отримання рівнів конкретного користувача (Адмін/Суперюзер)",  # i18n
    description="Повертає інформацію про рівні вказаного користувача. Доступно адміністраторам або суперюзерам.",
    # i18n
    dependencies=[Depends(get_current_active_superuser)]  # TODO: Розширити права для адмінів груп
)
# ПРИМІТКА: Цей ендпоінт для адміністраторів потребує ретельної перевірки прав доступу
# (не тільки суперюзер, але й адміністратор групи, якщо запитується рівень в контексті групи).
# Також залежить від повноти реалізації отримання всіх рівнів в `UserLevelService`.
async def get_user_levels_by_id_admin(  # Перейменовано
        user_id_target: UUID = Path(..., description="ID користувача"),  # i18n
        group_id: Optional[UUID] = Query(None, description="ID групи для фільтрації"),  # i18n
        current_admin_or_superuser: UserModel = Depends(get_current_active_superuser),  # Поточний адмін/СУ
        user_level_service: UserLevelService = Depends(get_user_level_service)
) -> List[UserLevelResponse]:
    """Отримує рівні вказаного користувача. Потрібна перевірка прав."""
    # TODO: Реалізувати перевірку прав: чи може current_admin_or_superuser бачити рівні user_id_target
    #  (наприклад, якщо він адмін спільної групи).
    logger.debug(
        f"Адмін/СУ ID '{current_admin_or_superuser.id}' запитує рівні для користувача ID '{user_id_target}'. Група: {group_id}.")

    user_level_responses: List[UserLevelResponse] = []  # Аналогічно /me
    if group_id is not None:
        user_level = await user_level_service.get_user_level(user_id=user_id_target, group_id=group_id)
        if user_level: user_level_responses.append(user_level)
    else:
        global_level = await user_level_service.get_user_level(user_id=user_id_target, group_id=None)
        if global_level: user_level_responses.append(global_level)
        # TODO: Додати групові рівні.
        logger.warning(f"Отримання всіх групових рівнів для /user/{user_id_target} ще не реалізовано повністю.")

    if not user_level_responses:
        logger.info(f"Інформацію про рівні для користувача ID '{user_id_target}' (група: {group_id}) не знайдено.")
    return user_level_responses


# Об'єднання роутерів
router.include_router(definitions_router, prefix="/definitions")
router.include_router(user_levels_router, prefix="/user")

logger.info("Роутер для рівнів (`/levels`) та рівнів користувачів (`/levels/user`) визначено.")
