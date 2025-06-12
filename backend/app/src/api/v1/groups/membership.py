# backend/app/src/api/v1/groups/membership.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління членством користувачів у групах.

Включає перегляд списку членів, додавання нових членів, оновлення їх ролей,
видалення членів з групи, а також вихід користувача з групи.
"""
from typing import List, Optional  # Generic, TypeVar не використовуються, Any, Dict теж
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Path  # Query не використовується прямо тут
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    # Залежності для перевірки прав адміна групи або суперюзера
    # check_group_view_permission, check_group_edit_permission - визначені в groups.py, але краще мати свої або спільні
    paginator
)
# TODO: Створити та використовувати більш гранульовані залежності для прав доступу до групи,
# наприклад, `require_group_member_or_superuser` та `require_group_admin_or_superuser`.
# Поки що будемо використовувати `get_current_active_user` та `check_group_edit_permission` (концептуально).
from backend.app.src.api.v1.groups.groups import check_group_view_permission, \
    check_group_edit_permission  # Імпорт залежностей з сусіднього файлу

from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.groups.membership import (
    GroupMembershipCreateBody,  # Схема для тіла запиту при додаванні члена (user_id, role_code)
    GroupMembershipUpdateBody,  # Схема для тіла запиту при оновленні ролі члена (role_code)
    GroupMembershipResponse,
    GroupMemberResponse  # Може бути синонімом GroupMembershipResponse або мати більше деталей про User
)
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.services.groups.membership import GroupMembershipService
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter()  # Префікс /{group_id} буде додано при включенні в groups/__init__.py


# Залежність для отримання GroupMembershipService
async def get_group_membership_service(session: AsyncSession = Depends(get_api_db_session)) -> GroupMembershipService:
    """Залежність FastAPI для отримання екземпляра GroupMembershipService."""
    return GroupMembershipService(db_session=session)


@router.get(
    "/members",  # Відносно /{group_id}/members
    response_model=PagedResponse[GroupMemberResponse],  # Використовуємо GroupMemberResponse
    summary="Отримання списку членів групи",  # i18n
    description="Повертає список членів вказаної групи з пагінацією. Доступно членам групи або суперюзерам.",  # i18n
    dependencies=[Depends(check_group_view_permission)]  # Перевірка, чи користувач є членом або суперюзером
)
async def list_group_members(
        group_id: UUID = Path(..., description="ID групи"),  # i18n
        is_active_filter: Optional[bool] = Query(True,
                                                 description="Фільтр за статусом активності членства (активні/неактивні)"),
        # i18n
        page_params: PageParams = Depends(paginator),
        membership_service: GroupMembershipService = Depends(get_group_membership_service)
        # current_user_with_permission: UserModel = Depends(check_group_view_permission) # Користувач вже в current_user з check_group_view_permission
) -> PagedResponse[GroupMemberResponse]:
    """
    Отримує список членів групи.
    Доступно членам групи та суперкористувачам.
    """
    logger.info(
        f"Запит списку членів для групи ID '{group_id}', активні: {is_active_filter}, сторінка: {page_params.page}.")
    # TODO: GroupMembershipService.list_group_members має повертати (items, total_count)
    members_orm, total_members = await membership_service.list_group_members_paginated(
        group_id=group_id,
        skip=page_params.skip,
        limit=page_params.limit,
        is_active=is_active_filter
    )
    return PagedResponse[GroupMemberResponse](
        total=total_members,
        page=page_params.page,
        size=page_params.size,
        results=[GroupMemberResponse.model_validate(m) for m in members_orm]  # Pydantic v2
    )


@router.post(
    "/members",  # Відносно /{group_id}/members
    response_model=GroupMembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Додавання користувача до групи (Адмін)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру додати користувача до групи з вказаною роллю.",  # i18n
    dependencies=[Depends(check_group_edit_permission)]  # Перевірка прав адміна групи/суперюзера
)
async def add_group_member(
        group_id: UUID = Path(..., description="ID групи"),  # i18n
        member_in: GroupMembershipCreateBody,  # Схема з user_id та role_code
        current_admin_or_superuser: UserModel = Depends(check_group_edit_permission),  # Користувач, що виконує дію
        membership_service: GroupMembershipService = Depends(get_group_membership_service)
) -> GroupMembershipResponse:
    """
    Додає користувача до групи з вказаною роллю.
    Вимагає прав адміністратора групи або суперкористувача.
    """
    logger.info(
        f"Адмін/Суперюзер ID '{current_admin_or_superuser.id}' додає користувача ID '{member_in.user_id}' до групи ID '{group_id}' з роллю '{member_in.role_code}'.")
    try:
        new_membership = await membership_service.add_member_to_group(
            group_id=group_id,
            user_id=member_in.user_id,
            role_code=member_in.role_code,
            added_by_user_id=current_admin_or_superuser.id,
            commit_session=True  # Сервіс має комітити, якщо це кінцева операція
        )
        return new_membership
    except ValueError as e:
        logger.warning(f"Помилка додавання члена до групи ID '{group_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при додаванні члена до групи ID '{group_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.put(
    "/members/{user_id_to_update}",  # Відносно /{group_id}/members/{user_id_to_update}
    response_model=GroupMembershipResponse,
    summary="Оновлення ролі члена групи (Адмін)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру змінити роль існуючого члена групи.",  # i18n
    dependencies=[Depends(check_group_edit_permission)]
)
async def update_group_member_role(
        group_id: UUID = Path(..., description="ID групи"),  # i18n
        user_id_to_update: UUID = Path(..., description="ID користувача, чию роль змінюють"),  # i18n
        member_update_in: GroupMembershipUpdateBody,  # Схема з new_role_code
        current_admin_or_superuser: UserModel = Depends(check_group_edit_permission),
        membership_service: GroupMembershipService = Depends(get_group_membership_service)
) -> GroupMembershipResponse:
    """
    Оновлює роль користувача в групі.
    Вимагає прав адміністратора групи або суперкористувача.
    """
    logger.info(
        f"Адмін/Суперюзер ID '{current_admin_or_superuser.id}' оновлює роль користувача ID '{user_id_to_update}' в групі ID '{group_id}' на '{member_update_in.role_code}'.")
    try:
        updated_membership = await membership_service.update_member_role(
            group_id=group_id,
            user_id=user_id_to_update,  # Змінено з user_id_to_update на user_id для відповідності сервісу
            new_role_code=member_update_in.role_code,
            updated_by_user_id=current_admin_or_superuser.id,
            commit_session=True
        )
        return updated_membership
    except ValueError as e:  # Наприклад, користувач не член, роль не знайдена, останній адмін
        logger.warning(f"Помилка оновлення ролі для користувача ID '{user_id_to_update}' в групі ID '{group_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:  # Якщо сервіс кидає помилку прав (хоча залежність вже має перевірити)
        logger.warning(f"Заборона оновлення ролі для користувача ID '{user_id_to_update}' в групі ID '{group_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні ролі в групі ID '{group_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.delete(
    "/members/{user_id_to_remove}",  # Відносно /{group_id}/members/{user_id_to_remove}
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення члена з групи (Адмін)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру видалити (деактивувати) користувача з групи."  # i18n
    # Обмеження (наприклад, не можна видалити єдиного адміністратора) обробляються в сервісі.
)
async def remove_group_member(
        group_id: UUID = Path(..., description="ID групи"),  # i18n
        user_id_to_remove: UUID = Path(..., description="ID користувача, якого видаляють"),  # i18n
        current_admin_or_superuser: UserModel = Depends(check_group_edit_permission),
        # Перевірка прав + отримання користувача
        membership_service: GroupMembershipService = Depends(get_group_membership_service)
):
    """
    Видаляє (деактивує) користувача з групи.
    Вимагає прав адміністратора групи або суперкористувача.
    """
    logger.info(
        f"Адмін/Суперюзер ID '{current_admin_or_superuser.id}' видаляє користувача ID '{user_id_to_remove}' з групи ID '{group_id}'.")
    try:
        success = await membership_service.remove_member_from_group(
            group_id=group_id,
            user_id=user_id_to_remove,  # Змінено з user_id_to_remove на user_id
            removed_by_user_id=current_admin_or_superuser.id
        )
        if not success:  # Якщо сервіс повертає False (наприклад, користувач не був активним членом)
            logger.warning(
                f"Не вдалося видалити користувача ID '{user_id_to_remove}' з групи ID '{group_id}' (сервіс повернув False).")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Членство користувача не знайдено або вже неактивне.")
    except ValueError as e:  # Обробка бізнес-помилок з сервісу (напр., спроба видалити останнього адміна)
        logger.warning(f"Помилка видалення користувача ID '{user_id_to_remove}' з групи ID '{group_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:
        logger.warning(f"Заборона видалення користувача ID '{user_id_to_remove}' з групи ID '{group_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n

    return None  # HTTP 204 No Content


@router.post(
    "/{group_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Вихід поточного користувача з групи",  # i18n
    description="Дозволяє аутентифікованому користувачу покинути групу, членом якої він є."  # i18n
    # Обмеження (адміністратор не може покинути групу, якщо він єдиний адмін) обробляються в сервісі.
)
async def leave_group(
        group_id: UUID = Path(..., description="ID групи, яку користувач покидає"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),  # Будь-який активний користувач
        membership_service: GroupMembershipService = Depends(get_group_membership_service)
):
    """
    Поточний користувач покидає групу.
    """
    logger.info(f"Користувач ID '{current_user.id}' намагається покинути групу ID '{group_id}'.")
    try:
        # GroupMembershipService.user_leave_group має обробляти логіку "останнього адміна"
        success = await membership_service.user_leave_group(
            group_id=group_id,
            user_id=current_user.id,  # Змінено з requesting_user на user_id
            removed_by_user_id=current_user.id  # Користувач сам себе "видаляє"
        )
        if not success:
            logger.warning(
                f"Не вдалося покинути групу ID '{group_id}' для користувача ID '{current_user.id}' (сервіс повернув False).")
            # i18n
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Не вдалося покинути групу. Можливо, ви не є членом або існують обмеження.")
    except ValueError as e:  # Обробка бізнес-помилок з сервісу (напр., останній адмін)
        logger.warning(f"Помилка виходу з групи ID '{group_id}' для користувача ID '{current_user.id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:  # Хоча тут це менш імовірно, якщо логіка в сервісі
        logger.warning(f"Заборона виходу з групи ID '{group_id}' для користувача ID '{current_user.id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n

    return None  # HTTP 204 No Content


logger.info(
    "Роутер для управління членством в групах (`/groups/{group_id}/members` та `/groups/{group_id}/leave`) визначено.")
