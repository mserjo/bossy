# backend/app/src/api/v1/gamification/badges.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління визначеннями Значків (Бейджів).

Бейджі є типом нагород, які користувачі можуть заробити. Цей модуль
дозволяє адміністраторам та суперкористувачам створювати, переглядати,
оновлювати та видаляти визначення цих бейджів.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List, Optional  # Generic, TypeVar, BaseModel не потрібні, якщо імпортуються з core
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    get_current_active_superuser, paginator
)
# TODO: Створити та використовувати гранульовані залежності для прав доступу, наприклад:
#  `require_badge_editor_permission(badge_id: UUID = Path(...))`
#  `require_badge_viewer_permission(badge_id: UUID = Path(...))`
from backend.app.src.api.v1.groups.groups import check_group_edit_permission  # Тимчасово для адмінських дій в групі
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.gamification.badge import (
    BadgeCreate, BadgeUpdate, BadgeResponse
)
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.services.gamification.badge import BadgeService
from backend.app.src.services.groups.group import GroupService  # Для перевірки групи при створенні
from backend.app.src.config import settings as global_settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter(
    # Префікс /badges буде додано в __init__.py батьківського роутера gamification
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання BadgeService
async def get_badge_service(session: AsyncSession = Depends(get_api_db_session)) -> BadgeService:
    """Залежність FastAPI для отримання екземпляра BadgeService."""
    return BadgeService(db_session=session)


# Залежність для GroupService (для перевірки існування групи при створенні бейджа для групи)
async def get_group_service_dep(session: AsyncSession = Depends(get_api_db_session)) -> GroupService:
    return GroupService(db_session=session)

# ПРИМІТКА: Ключовим моментом є реалізація надійної перевірки прав доступу
# (адміністратор групи або суперюзер), як зазначено в TODO.
# Також, сервіс `create` має обробляти `created_by_user_id`.
@router.post(
    "/",
    response_model=BadgeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового визначення бейджа (Адмін/Суперюзер)",  # i18n
    description="""Дозволяє адміністратору групи (для бейджів своєї групи) або суперюзеру
    (для будь-яких бейджів, включаючи глобальні) створити нове визначення бейджа."""  # i18n
)
async def create_badge_definition(
        badge_in: BadgeCreate,  # Схема містить group_id (опціонально)
        current_user: UserModel = Depends(get_current_active_user),  # Поточний користувач для перевірки прав
        badge_service: BadgeService = Depends(get_badge_service),
        # group_service: GroupService = Depends(get_group_service_dep) # Не потрібен, якщо сервіс бейджів сам валідує групу
):
    """
    Створює нове визначення бейджа.
    Якщо `badge_in.group_id` вказано, користувач має бути адміном цієї групи або суперюзером.
    Якщо `badge_in.group_id` не вказано (глобальний бейдж), тільки суперюзер може його створити.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' намагається створити бейдж '{badge_in.name}'. Група: {badge_in.group_id or 'Глобальний'}.")

    # Перевірка прав доступу (має бути інкапсульована в сервісі або спеціальній залежності)
    # TODO: Реалізувати перевірку прав: якщо badge_in.group_id, то current_user - адмін цієї групи або СУ.
    #  Якщо badge_in.group_id is None, то current_user - СУ.
    if badge_in.group_id:
        # Приклад простої перевірки (потребує GroupMembershipService)
        # if not current_user.is_superuser:
        #     membership_service = GroupMembershipService(badge_service.db_session) # Або ін'єктувати
        #     is_admin = await membership_service.is_user_group_admin(current_user.id, badge_in.group_id)
        #     if not is_admin:
        #         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ви не є адміністратором вказаної групи.") # i18n
        pass  # Припускаємо, що сервіс `create` обробляє цю логіку або вона винесена в залежність
    elif not current_user.is_superuser:
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Тільки суперкористувачі можуть створювати глобальні бейджі.")

    try:
        # BadgeService.create (успадкований та розширений) має обробляти унікальність імені в межах group_id/глобально
        # та валідувати пов'язані ID (icon_file_id).
        # Також передаємо created_by_user_id.
        created_badge = await badge_service.create(data=badge_in, created_by_user_id=current_user.id)
        return created_badge
    except ValueError as e:
        logger.warning(f"Помилка створення бейджа '{badge_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні бейджа '{badge_in.name}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/",
    response_model=PagedResponse[BadgeResponse],
    summary="Отримання списку визначень бейджів",  # i18n
    description="""Повертає список визначень бейджів з пагінацією.
    Доступно всім автентифікованим користувачам. Фільтрується за групою (`group_id`),
    показуючи глобальні бейджі та бейджі вказаної групи (якщо користувач є її членом)."""  # i18n
)
async def read_badge_definitions(
        group_id: Optional[UUID] = Query(None,
                                         description="ID групи для фільтрації (показує бейджі групи + глобальні)"),
        # i18n
        is_active: Optional[bool] = Query(None, description="Фільтр за статусом активності"),  # i18n
        page_params: PageParams = Depends(paginator),
        current_user: UserModel = Depends(get_current_active_user),  # Для контексту доступу
        badge_service: BadgeService = Depends(get_badge_service)
) -> PagedResponse[BadgeResponse]:
    """
    Отримує список визначень бейджів.
    Користувачі бачать глобальні бейджі та бейджі груп, до яких вони належать (якщо group_id вказано і вони є членами).
    Суперюзери бачать усі бейджі.
    """
    # TODO: BadgeService.list_badges_paginated має враховувати права current_user
    #  та параметр group_id для фільтрації (показувати глобальні + доступні групові).
    #  Також має повертати (items, total_count).
    logger.debug(f"Користувач ID '{current_user.id}' запитує список бейджів. Група: {group_id}, Активні: {is_active}.")

    badges_orm, total_badges = await badge_service.list_badges_paginated(
        requesting_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        group_id_filter=group_id,
        is_active_filter=is_active,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PagedResponse[BadgeResponse](
        total=total_badges,
        page=page_params.page,
        size=page_params.size,
        results=[BadgeResponse.model_validate(b) for b in badges_orm]  # Pydantic v2
    )

# ПРИМІТКА: Доступність бейджів для користувача має визначатися логікою
# в `BadgeService.list_badges_paginated`, враховуючи членство в групах та
# налаштування самих бейджів, як вказано в TODO.
# TODO: Створити залежність `check_badge_access_permission(badge_id: UUID, current_user: UserModel, ...)`
#  яка перевіряє, чи може користувач бачити/редагувати цей бейдж.

# ПРИМІТКА: Логіка перевірки доступу до конкретного бейджа (глобальний, груповий,
# чи є користувач членом групи) має бути інкапсульована в методі
# `BadgeService.get_by_id_for_user` або спеціальній залежності.
@router.get(
    "/{badge_id}",  # Змінено з badge_def_id на badge_id для узгодженості
    response_model=BadgeResponse,
    summary="Отримання інформації про визначення бейджа за ID",  # i18n
    description="""Повертає детальну інформацію про конкретне визначення бейджа.
    Доступно, якщо бейдж глобальний або користувач є членом групи бейджа."""  # i18n
    # dependencies=[Depends(check_badge_access_permission)] # TODO
)
async def read_badge_definition_by_id(
        badge_id: UUID = Path(..., description="ID визначення бейджа"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),  # Для перевірки доступу
        badge_service: BadgeService = Depends(get_badge_service)
) -> BadgeResponse:
    """
    Отримує інформацію про визначення бейджа за його ID.
    Сервіс має перевіряти доступність бейджа для користувача.
    """
    logger.debug(f"Користувач ID '{current_user.id}' запитує бейдж ID '{badge_id}'.")
    # BadgeService.get_by_id_for_user має перевіряти права
    badge = await badge_service.get_by_id_for_user(  # Потрібен такий метод в сервісі
        item_id=badge_id,
        requesting_user_id=current_user.id,
        is_superuser=current_user.is_superuser
    )
    if not badge:
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Визначення бейджа з ID {badge_id} не знайдено або доступ заборонено.")
    return badge

# ПРИМІТКА: Оновлення визначення бейджа вимагає ретельної перевірки прав
# (адміністратор групи бейджа або суперюзер). Ця логіка має бути реалізована
# або в сервісі, або через спеціалізовану залежність (див. TODO).
@router.put(
    "/{badge_id}",
    response_model=BadgeResponse,
    summary="Оновлення визначення бейджа (Адмін/Суперюзер)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру оновити існуюче визначення бейджа.",  # i18n
    # dependencies=[Depends(check_badge_editor_permission)] # TODO
)
async def update_badge_definition(
        badge_id: UUID,
        badge_in: BadgeUpdate,
        current_user: UserModel = Depends(get_current_active_superuser),
        # TODO: Замінити на check_badge_editor_permission
        badge_service: BadgeService = Depends(get_badge_service)
) -> BadgeResponse:
    """Оновлює дані визначення бейджа."""
    logger.info(f"Користувач ID '{current_user.id}' намагається оновити бейдж ID '{badge_id}'.")
    try:
        # BadgeService.update (успадкований та розширений) має обробляти унікальність імені в межах group_id/глобально
        # та валідувати пов'язані ID (icon_file_id).
        # Також передаємо updated_by_user_id.
        updated_badge = await badge_service.update(
            item_id=badge_id,
            data=badge_in,
            updated_by_user_id=current_user.id  # Передаємо через kwargs в BaseDictionaryService.update
        )
        if not updated_badge:  # Малоймовірно, якщо права перевірено і сервіс кидає винятки
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бейдж не знайдено для оновлення.")
        return updated_badge
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка: {e}", exc_info=global_settings.DEBUG)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера.")  # i18n


@router.delete(
    "/{badge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення визначення бейджа (Адмін/Суперюзер)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру видалити визначення бейджа.",  # i18n
    # dependencies=[Depends(check_badge_editor_permission)] # TODO
)
async def delete_badge_definition(
        badge_id: UUID,
        current_user: UserModel = Depends(get_current_active_superuser),  # TODO: Замінити
        badge_service: BadgeService = Depends(get_badge_service)
):
    """Видаляє визначення бейджа."""
    logger.info(f"Користувач ID '{current_user.id}' намагається видалити бейдж ID '{badge_id}'.")
    try:
        # TODO: BadgeService.delete має перевіряти права та чи не використовується бейдж.
        success = await badge_service.delete_badge_with_permission_check(  # Потрібен такий метод
            item_id=badge_id,
            requesting_user_id=current_user.id,
            is_superuser=current_user.is_superuser
        )
        if not success:
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Не вдалося видалити бейдж. Можливо, його не існує або у вас немає прав.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n

    return None

# ПРИМІТКА: Видалення визначення бейджа також потребує ретельної перевірки прав,
# аналогічно до оновлення, та перевірки, чи не використовується бейдж
# в активних досягненнях.
logger.info(f"Роутер для визначень бейджів (`{router.prefix}`) визначено.")
