# backend/app/src/api/v1/groups/invitation.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління запрошеннями до групи API v1.

Цей модуль надає API для:
- Створення адміністратором групи унікального посилання/QR-коду для запрошення.
- Перегляду активних запрошень для групи (адміністратором).
- Відкликання/видалення запрошення (адміністратором).
- Прийняття запрошення користувачем (приєднання до групи за посиланням/кодом).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Response
from typing import List
from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.groups.invitation import (
    GroupInvitationSchema,
    GroupInvitationCreateSchema, # Може містити параметри, як термін дії, кількість використань
    GroupInvitationCreateResponseSchema # Для відповіді з кодом/посиланням
)
from backend.app.src.schemas.groups.membership import GroupMemberSchema # Для відповіді при приєднанні
from backend.app.src.services.groups.group_invitation_service import GroupInvitationService
from backend.app.src.services.groups.group_membership_service import GroupMembershipService # Для приєднання
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

@router.post(
    "/{group_id}/invitations",
    response_model=GroupInvitationCreateResponseSchema, # Повертає посилання/код
    status_code=status.HTTP_201_CREATED,
    tags=["Groups", "Group Invitations"],
    summary="Створити запрошення до групи (адміністратор)"
)
async def create_group_invitation(
    group_id: int,
    # Можна додати параметри запрошення в тіло запиту, якщо потрібно (напр. термін дії)
    invitation_params: GroupInvitationCreateSchema = None, # Опціональні параметри
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адміністратор {current_admin.email} створює запрошення для групи ID {group_id}.")

    invitation_service = GroupInvitationService(db_session)
    try:
        # Сервіс повинен генерувати унікальний код та, можливо, посилання
        invitation_response = await invitation_service.create_invitation(
            group_id=group_id,
            creator_id=current_admin.id,
            params=invitation_params # Передаємо параметри, якщо є
        )
        return invitation_response
    except Exception as e:
        logger.error(f"Помилка створення запрошення для групи {group_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при створенні запрошення.")

@router.get(
    "/{group_id}/invitations",
    response_model=List[GroupInvitationSchema], # Список активних запрошень
    tags=["Groups", "Group Invitations"],
    summary="Отримати список активних запрошень для групи (адміністратор)"
)
async def list_group_invitations(
    group_id: int,
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адміністратор {current_admin.email} запитує список запрошень для групи ID {group_id}.")
    invitation_service = GroupInvitationService(db_session)
    invitations = await invitation_service.get_active_invitations_for_group(group_id=group_id)
    return invitations

@router.delete(
    "/{group_id}/invitations/{invitation_id_or_code}", # Може бути ID або сам код
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Groups", "Group Invitations"],
    summary="Відкликати/видалити запрошення до групи (адміністратор)"
)
async def revoke_group_invitation(
    group_id: int,
    invitation_id_or_code: str,
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} видаляє запрошення '{invitation_id_or_code}' для групи ID {group_id}."
    )
    invitation_service = GroupInvitationService(db_session)
    success = await invitation_service.revoke_invitation(
        invitation_id_or_code=invitation_id_or_code,
        group_id=group_id, # Для перевірки, що запрошення належить цій групі
        actor_id=current_admin.id
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запрошення не знайдено або не вдалося видалити.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Цей ендпоінт не повинен бути під префіксом /groups/{group_id}, бо group_id невідомий до валідації коду.
# Його краще розмістити на рівні /api/v1/invitations/join/{invitation_code} або подібному.
# Для простоти зараз залишу тут, але це потребує обговорення структури URL.
# Або ж /groups/join/{invitation_code}
@router.post(
    "/join/{invitation_code}",
    response_model=GroupMemberSchema,
    tags=["Groups", "Group Invitations"],
    summary="Приєднатися до групи за кодом запрошення"
)
async def join_group_by_invitation(
    invitation_code: str = Path(..., description="Унікальний код запрошення"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} (ID {current_user.id}) намагається приєднатися до групи за кодом: {invitation_code}.")

    invitation_service = GroupInvitationService(db_session)
    membership_service = GroupMembershipService(db_session) # Потрібен для додавання в учасники

    try:
        # Сервіс перевіряє код, термін дії, кількість використань та повертає group_id
        group_id_to_join = await invitation_service.validate_and_consume_invitation(
            invitation_code=invitation_code,
            user_id=current_user.id # Для перевірки, чи не намагається приєднатися до групи, де вже є
        )

        if not group_id_to_join: # Якщо validate_and_consume_invitation повертає None при помилці
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недійсний або використаний код запрошення.")

        # Додаємо користувача до групи (сервіс членства має обробити, якщо вже член)
        # Припускаємо, що запрошення має роль за замовчуванням (напр. "USER")
        # або ця логіка є в invitation_service/membership_service
        role_code_on_join = "USER" # TODO: Отримувати роль з налаштувань запрошення або групи

        new_membership = await membership_service.add_user_to_group(
            group_id=group_id_to_join,
            user_id_to_add=current_user.id,
            role_code=role_code_on_join, # Роль при приєднанні за запрошенням
            actor_id=current_user.id # Сам користувач є "актором"
        )
        logger.info(f"Користувач {current_user.email} успішно приєднався до групи ID {group_id_to_join}.")
        return new_membership

    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка приєднання до групи за кодом {invitation_code}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при приєднанні до групи.")

# Роутер буде підключений в backend/app/src/api/v1/groups/__init__.py
