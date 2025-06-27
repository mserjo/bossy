# backend/app/src/api/v1/groups/membership.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління членством у групі API v1.

Цей модуль надає API для адміністраторів групи для:
- Перегляду списку учасників групи.
- Додавання нових учасників до групи (якщо це не через запрошення).
- Видалення учасників з групи.
- Зміни ролі учасника в групі.

Також може містити ендпоінт для користувача, щоб покинути групу.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Response
from typing import List
from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.groups.membership import (
    GroupMemberSchema,
    GroupMemberCreateSchema, # Для додавання/запрошення з роллю
    GroupMemberUpdateRoleSchema # Для зміни ролі
)
from backend.app.src.services.groups.group_membership_service import GroupMembershipService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission # Для адмінських дій
from backend.app.src.models.auth.user import UserModel
from backend.app.src.models.groups.group import GroupModel # Для type hint

logger = get_logger(__name__)
router = APIRouter()

# Залежність для перевірки, чи користувач є учасником групи (для перегляду списку членів)
async def group_member_permission(
    group_id: int,
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
) -> dict:
    membership_service = GroupMembershipService(db_session)
    is_member = await membership_service.is_user_member_of_group(user_id=current_user.id, group_id=group_id)
    if not is_member:
        # Можливо, варто перевірити, чи група взагалі існує, щоб не показувати 403 на неіснуючу групу
        # Але якщо група існує, а користувач не член - то 403.
        # group_service = GroupService(db_session)
        # if not await group_service.get_by_id(group_id):
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Групу не знайдено")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ви не є учасником цієї групи.")
    # Повертаємо словник, щоб відповідати формату group_admin_permission, якщо потрібно
    return {"group_id": group_id, "current_user": current_user}


@router.get(
    "/{group_id}/members",
    response_model=List[GroupMemberSchema],
    tags=["Groups", "Group Membership"],
    summary="Отримати список учасників групи"
)
async def list_group_members(
    group_id: int,
    # Або group_admin_permission, якщо тільки адміни можуть бачити повний список з ролями
    # Або group_member_permission, якщо всі учасники можуть бачити список
    access_check: dict = Depends(group_member_permission), # Дозволяємо всім учасникам бачити
    db_session: DBSession = Depends()
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує список учасників для групи ID {group_id}.")
    membership_service = GroupMembershipService(db_session)
    members = await membership_service.get_members_of_group(group_id=group_id)
    return members

@router.post(
    "/{group_id}/members", # Змінено шлях, user_id тепер в тілі запиту
    response_model=GroupMemberSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Groups", "Group Membership"],
    summary="Додати учасника до групи (адміністратор)"
)
async def add_member_to_group(
    group_id: int,
    member_data: GroupMemberCreateSchema, # В тілі user_id та role_code
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} додає користувача ID {member_data.user_id} "
        f"до групи ID {group_id} з роллю '{member_data.role_code}'."
    )
    membership_service = GroupMembershipService(db_session)
    try:
        new_member = await membership_service.add_user_to_group(
            group_id=group_id,
            user_id_to_add=member_data.user_id,
            role_code=member_data.role_code,
            actor_id=current_admin.id
        )
        return new_member
    except HTTPException as e:
        raise e
    except Exception as e_gen: # Загальний виняток
        logger.error(f"Помилка додавання учасника до групи {group_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


@router.delete(
    "/{group_id}/members/{user_id_to_remove}", # user_id_to_remove - це ID користувача, якого видаляють
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Groups", "Group Membership"],
    summary="Видалити учасника з групи (адміністратор)"
)
async def remove_member_from_group(
    group_id: int,
    user_id_to_remove: int,
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} видаляє користувача ID {user_id_to_remove} з групи ID {group_id}."
    )
    membership_service = GroupMembershipService(db_session)

    if current_admin.id == user_id_to_remove:
        # Перевірка, чи адмін не видаляє сам себе, якщо він останній адмін
        # Цю логіку краще мати в сервісі
        is_last_admin = await membership_service.is_user_last_admin(user_id=current_admin.id, group_id=group_id)
        if is_last_admin:
            logger.warning(f"Адмін {current_admin.email} не може видалити себе з групи {group_id}, бо він останній адмін.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ви не можете видалити себе, оскільки є останнім адміністратором групи.")

    success = await membership_service.remove_user_from_group(
        group_id=group_id,
        user_id_to_remove=user_id_to_remove,
        actor_id=current_admin.id
    )
    if not success:
        # Можливо, користувач вже не був членом, або інша помилка
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Учасника не знайдено в групі або не вдалося видалити.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{group_id}/members/{user_id_to_update}/role",
    response_model=GroupMemberSchema,
    tags=["Groups", "Group Membership"],
    summary="Змінити роль учаснику групи (адміністратор)"
)
async def update_member_role_in_group(
    group_id: int,
    user_id_to_update: int,
    role_data: GroupMemberUpdateRoleSchema, # Тіло запиту з new_role_code
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} змінює роль для користувача ID {user_id_to_update} "
        f"в групі ID {group_id} на '{role_data.new_role_code}'."
    )
    membership_service = GroupMembershipService(db_session)
    try:
        updated_member = await membership_service.update_user_role_in_group(
            group_id=group_id,
            user_id_to_update=user_id_to_update,
            new_role_code=role_data.new_role_code,
            actor_id=current_admin.id
        )
        return updated_member
    except HTTPException as e:
        raise e
    except ValueError as ve: # Наприклад, якщо роль недійсна
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.post(
    "/{group_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Groups", "Group Membership"],
    summary="Покинути групу"
)
async def leave_group(
    group_id: int,
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} (ID {current_user.id}) покидає групу ID {group_id}.")
    membership_service = GroupMembershipService(db_session)
    try:
        await membership_service.user_leave_group(user_id=current_user.id, group_id=group_id)
    except HTTPException as e: # Сервіс може кидати помилки (напр. останній адмін)
        raise e

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/groups/__init__.py
