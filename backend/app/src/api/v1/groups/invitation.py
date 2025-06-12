# backend/app/src/api/v1/groups/invitation.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління запрошеннями до груп.

Включає створення, перегляд, відкликання запрошень (для адміністраторів групи)
та прийняття/відхилення запрошень (для користувачів).
"""
from typing import List, Optional  # Generic, TypeVar, Any, Dict не використовуються
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Path  # Query не використовується прямо тут
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    # TODO: Створити get_current_active_group_admin_or_superuser (або використовувати check_group_edit_permission з groups.py)
    # Для простоти, поки що будемо використовувати get_current_active_superuser для адмінських дій
    get_current_active_superuser,
    paginator
)
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.groups.invitation import (
    GroupInvitationCreate,
    GroupInvitationResponse,
    # InvitationAcceptAction - не використовується, дія визначається ендпоінтом
)
from backend.app.src.schemas.groups.membership import GroupMembershipResponse  # Для відповіді при прийнятті запрошення
from backend.app.src.core.pagination import PagedResponse, PageParams  # Використовуємо з core.pagination
from backend.app.src.services.groups.invitation import GroupInvitationService
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings  # Для DEBUG тощо

# Головний роутер для цього модуля, який буде включено в /groups в __init__.py
router = APIRouter()


# Залежність для отримання GroupInvitationService
async def get_group_invitation_service(session: AsyncSession = Depends(get_api_db_session)) -> GroupInvitationService:
    """Залежність FastAPI для отримання екземпляра GroupInvitationService."""
    return GroupInvitationService(db_session=session)


# --- Ендпоінти, що стосуються конкретної групи (керування запрошеннями адміном) ---
# Ці ендпоінти будуть доступні за префіксом /{group_id}/invitations,
# встановленим при включенні цього group_specific_admin_actions_router до основного router нижче.
group_specific_admin_actions_router = APIRouter()


@group_specific_admin_actions_router.post(
    "/",  # Відносно /{group_id}/invitations
    response_model=GroupInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення запрошення до групи (Адмін)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру створити запрошення для користувача приєднатися до групи."
    # i18n
    # Дозволи перевіряються на рівні основного роутера або тут
)
async def create_group_invitation(
        group_id: UUID = Path(..., description="ID групи, до якої створюється запрошення"),  # i18n
        invitation_in: GroupInvitationCreate,  # Має містити email та role_code_to_assign
        # TODO: Замінити get_current_active_superuser на залежність, що перевіряє права адміна саме цієї групи або суперюзера
        current_admin_or_superuser: UserModel = Depends(get_current_active_superuser),
        invitation_service: GroupInvitationService = Depends(get_group_invitation_service)
) -> GroupInvitationResponse:
    """
    Створює нове запрошення до групи.
    Вимагає прав адміністратора групи або суперкористувача.
    """
    logger.info(
        f"Користувач ID '{current_admin_or_superuser.id}' створює запрошення до групи ID '{group_id}'. Дані: {invitation_in.model_dump_minimal()}")
    try:
        # Сервіс GroupInvitationService.create_invitation має приймати role_code_to_assign
        # та перевіряти існування ролі.
        # У схемі GroupInvitationCreate має бути поле role_code_to_assign.
        if not hasattr(invitation_in, 'role_code_to_assign') or not invitation_in.role_code_to_assign:
            # i18n
            raise ValueError("Необхідно вказати код ролі для призначення (role_code_to_assign).")

        created_invitation = await invitation_service.create_invitation(
            group_id=group_id,
            inviter_user_id=current_admin_or_superuser.id,
            role_to_assign_code=invitation_in.role_code_to_assign,  # type: ignore
            invite_data=invitation_in  # Передаємо всю схему, сервіс розбереться
        )
        return created_invitation
    except ValueError as e:
        logger.warning(f"Помилка створення запрошення для групи ID '{group_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні запрошення для групи ID '{group_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@group_specific_admin_actions_router.get(
    "/",  # Відносно /{group_id}/invitations
    response_model=PagedResponse[GroupInvitationResponse],
    summary="Список запрошень для групи (Адмін)",  # i18n
    description="Повертає список активних (pending) запрошень для вказаної групи. Доступно адміністраторам групи або суперюзерам."
    # i18n
)
async def list_group_invitations(
        group_id: UUID = Path(..., description="ID групи для перегляду запрошень"),  # i18n
        page_params: PageParams = Depends(paginator),
        # TODO: Замінити get_current_active_superuser на залежність адміна групи/суперюзера
        current_admin_or_superuser: UserModel = Depends(get_current_active_superuser),
        invitation_service: GroupInvitationService = Depends(get_group_invitation_service)
) -> PagedResponse[GroupInvitationResponse]:
    """
    Отримує список активних запрошень для конкретної групи.
    Вимагає прав адміністратора групи або суперкористувача.
    """
    logger.debug(f"Користувач ID '{current_admin_or_superuser.id}' запитує список запрошень для групи ID '{group_id}'.")
    # TODO: GroupInvitationService має надати метод для отримання запрошень з пагінацією та загальною кількістю.
    #  Наприклад, `list_pending_invitations_for_group_paginated(group_id, skip, limit)`
    invitations_list = await invitation_service.list_pending_invitations_for_group(
        group_id=group_id, skip=page_params.skip, limit=page_params.limit
    )
    # total_count = await invitation_service.count_pending_invitations_for_group(group_id=group_id) # Потрібен такий метод
    total_count = len(invitations_list)  # ЗАГЛУШКА для total_count
    logger.warning("Використовується заглушка для total_count при переліку запрошень групи.")

    return PagedResponse[GroupInvitationResponse](
        total=total_count,
        page=page_params.page,
        size=page_params.size,
        results=invitations_list  # Сервіс вже повертає список Pydantic моделей
    )


@group_specific_admin_actions_router.delete(
    "/{invitation_id}",  # Відносно /{group_id}/invitations
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Відкликання запрошення (Адмін)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру відкликати (видалити) запрошення."  # i18n
)
async def revoke_group_invitation(
        group_id: UUID = Path(..., description="ID групи, до якої належить запрошення"),  # i18n
        invitation_id: UUID = Path(..., description="ID запрошення, яке відкликається"),  # i18n
        # TODO: Замінити get_current_active_superuser на залежність адміна групи/суперюзера
        current_admin_or_superuser: UserModel = Depends(get_current_active_superuser),
        invitation_service: GroupInvitationService = Depends(get_group_invitation_service)
):
    """
    Відкликає (видаляє) запрошення.
    Вимагає прав адміністратора групи або суперкористувача.
    """
    logger.info(
        f"Користувач ID '{current_admin_or_superuser.id}' намагається відкликати запрошення ID '{invitation_id}' для групи ID '{group_id}'.")
    try:
        # TODO: GroupInvitationService.revoke_invitation має перевіряти, чи запрошення належить вказаній групі.
        success = await invitation_service.revoke_invitation(
            invitation_id=invitation_id,
            revoker_user_id=current_admin_or_superuser.id
            # group_id=group_id # Можна передати для додаткової валідації в сервісі
        )
        if not success:  # Якщо сервіс повертає False (наприклад, не знайдено або не вдалося відкликати)
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Запрошення не знайдено або не вдалося відкликати.")
    except ValueError as e:  # Обробка помилок валідації/логіки з сервісу
        logger.warning(f"Помилка відкликання запрошення ID '{invitation_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:  # Якщо сервіс кидає помилку прав доступу
        logger.warning(f"Заборона відкликання запрошення ID '{invitation_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n

    return None  # HTTP 204 No Content


# --- Загальні ендпоінти для запрошень (для користувачів, що приймають/відхиляють) ---
# Ці ендпоінти будуть доступні за префіксом /invitations, встановленим при включенні цього user_actions_router.
user_actions_router = APIRouter()


@user_actions_router.get(
    "/pending",
    response_model=List[GroupInvitationResponse],
    summary="Список моїх активних запрошень",  # i18n
    description="Повертає список активних запрошень для поточного аутентифікованого користувача."  # i18n
)
async def list_my_pending_invitations(
        current_user: UserModel = Depends(get_current_active_user),
        invitation_service: GroupInvitationService = Depends(get_group_invitation_service)
) -> List[GroupInvitationResponse]:
    """
    Отримує список активних запрошень, надісланих поточному користувачеві (за email або user_id).
    """
    logger.debug(f"Користувач ID '{current_user.id}' запитує свої активні запрошення.")
    # TODO: GroupInvitationService має мати метод list_pending_invitations_for_user(user_id, email)
    invitations = await invitation_service.list_pending_invitations_for_user(  # type: ignore
        user_id=current_user.id, user_email=current_user.email
    )
    return invitations


@user_actions_router.post(
    "/{invitation_code}/accept",  # invitation_code - це унікальний код з GroupInvitation.invitation_code
    response_model=GroupMembershipResponse,  # Повертає інформацію про нове членство
    status_code=status.HTTP_200_OK,  # Або 201, якщо членство завжди нове
    summary="Прийняття запрошення до групи",  # i18n
    description="Дозволяє користувачу прийняти запрошення, використовуючи його унікальний код."  # i18n
)
async def accept_group_invitation(
        invitation_code: str = Path(..., description="Унікальний код запрошення"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        invitation_service: GroupInvitationService = Depends(get_group_invitation_service)
) -> GroupMembershipResponse:
    """
    Приймає запрошення до групи за його кодом.
    Сервіс має валідувати код, перевірити статус/термін дії запрошення,
    та додати користувача до групи з відповідною роллю.
    """
    logger.info(f"Користувач ID '{current_user.id}' намагається прийняти запрошення за кодом '{invitation_code}'.")
    try:
        new_membership = await invitation_service.accept_invitation(
            invitation_code=invitation_code,
            accepting_user_id=current_user.id
        )
        return new_membership
    except ValueError as e:  # Обробка помилок типу "не знайдено", "прострочено", "вже член" з сервісу
        logger.warning(f"Помилка прийняття запрошення '{invitation_code}' користувачем ID '{current_user.id}': {e}")
        # i18n (повідомлення від сервісу має бути готовим для відображення)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:  # Якщо запрошення для іншого користувача
        logger.warning(f"Заборона прийняття запрошення '{invitation_code}' користувачем ID '{current_user.id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при прийнятті запрошення '{invitation_code}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при прийнятті запрошення.")


@user_actions_router.post(
    "/{invitation_code}/decline",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Відхилення запрошення до групи",  # i18n
    description="Дозволяє користувачу відхилити запрошення, використовуючи його унікальний код."  # i18n
)
async def decline_group_invitation(
        invitation_code: str = Path(..., description="Унікальний код запрошення"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        invitation_service: GroupInvitationService = Depends(get_group_invitation_service)
):
    """
    Відхиляє запрошення до групи.
    Запрошення позначається як відхилене.
    """
    logger.info(f"Користувач ID '{current_user.id}' намагається відхилити запрошення за кодом '{invitation_code}'.")
    try:
        success = await invitation_service.decline_invitation(
            invitation_code=invitation_code,
            declining_user_id=current_user.id
        )
        if not success:  # Якщо сервіс повернув False (наприклад, запрошення не знайдено або не в тому статусі)
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Не вдалося відхилити запрошення. Можливо, воно не існує або вже оброблене.")
    except ValueError as e:
        logger.warning(f"Помилка відхилення запрошення '{invitation_code}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:
        logger.warning(f"Заборона відхилення запрошення '{invitation_code}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n

    return None  # HTTP 204 No Content


# Об'єднуємо роутери: адмінські дії під /{group_id}/invitations, користувацькі під /invitations
router.include_router(group_specific_admin_actions_router, prefix="/{group_id}/invitations")
router.include_router(user_actions_router, prefix="/invitations")  # Без додаткового префіксу тут, він буде від /groups

logger.info("Роутер для запрошень до груп (`/groups/.../invitations` та `/groups/invitations/...`) визначено.")
