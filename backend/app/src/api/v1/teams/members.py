# backend/app/src/api/v1/teams/members.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління членством у команді API v1.

Цей модуль надає API для:
- Додавання користувачів до команди (адміністратором групи або лідером команди).
- Видалення користувачів з команди.
- Перегляду списку учасників команди.
- Можливо, призначення ролей всередині команди (лідер, учасник), якщо це передбачено.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Response, Body
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.teams.membership import TeamMemberSchema, TeamMemberCreateSchema
# TeamMemberUpdateSchema - якщо можна оновлювати роль в команді
from backend.app.src.services.teams.team_membership_service import TeamMembershipService
from backend.app.src.services.teams.team_service import TeamService # Для перевірки існування команди
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission, group_member_permission
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Залежність для перевірки прав на управління членами команди
# (адміністратор групи або, можливо, лідер команди - цю логіку треба визначити)
async def check_team_management_permissions(
    group_id: int = Path(...),
    team_id: int = Path(...),
    admin_check: dict = Depends(group_admin_permission), # Поки що тільки адмін групи
    db_session: DBSession = Depends()
) -> dict:
    # Перевірка, чи команда належить групі
    team_service = TeamService(db_session)
    team = await team_service.get_team_by_id_and_group_id(team_id=team_id, group_id=group_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Команду не знайдено в цій групі.")
    return {"team": team, "current_user": admin_check["current_user"], "group_id": group_id}

# Залежність для перевірки прав на перегляд членів команди
# (учасник групи, до якої належить команда)
async def check_team_view_permissions(
    group_id: int = Path(...),
    team_id: int = Path(...),
    member_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends()
) -> dict:
    team_service = TeamService(db_session)
    team = await team_service.get_team_by_id_and_group_id(team_id=team_id, group_id=group_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Команду не знайдено в цій групі.")
    return {"team": team, "current_user": member_check["current_user"], "group_id": group_id}


@router.post(
    "",
    response_model=TeamMemberSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Teams", "Team Membership"],
    summary="Додати учасника до команди (адміністратор групи)"
)
async def add_user_to_team(
    member_in: TeamMemberCreateSchema, # В тілі user_id, можливо team_role_code
    team_context: dict = Depends(check_team_management_permissions),
    db_session: DBSession = Depends()
):
    team = team_context["team"]
    current_admin: UserModel = team_context["current_user"]
    group_id: int = team_context["group_id"]

    logger.info(
        f"Адміністратор {current_admin.email} додає користувача ID {member_in.user_id} "
        f"до команди ID {team.id} (група {group_id})."
    )

    if member_in.team_id != team.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Невідповідність ID команди.")

    membership_service = TeamMembershipService(db_session)
    try:
        new_member = await membership_service.add_user_to_team(
            team_id=team.id,
            user_id_to_add=member_in.user_id,
            # role_code=member_in.team_role_code, # Якщо є ролі в команді
            actor_id=current_admin.id,
            group_id_context=group_id # Для перевірки, що користувач є членом групи
        )
        return new_member
    except HTTPException as e:
        raise e
    except ValueError as ve: # Наприклад, користувач вже в команді або не член групи
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.get(
    "",
    response_model=List[TeamMemberSchema],
    tags=["Teams", "Team Membership"],
    summary="Отримати список учасників команди"
)
async def list_team_members_in_team(
    team_context: dict = Depends(check_team_view_permissions),
    db_session: DBSession = Depends()
):
    team = team_context["team"]
    current_user: UserModel = team_context["current_user"]
    group_id: int = team_context["group_id"]

    logger.info(f"Користувач {current_user.email} запитує список учасників команди {team.id} (група {group_id}).")
    membership_service = TeamMembershipService(db_session)
    members = await membership_service.get_members_of_team(team_id=team.id)
    return members

@router.delete(
    "/{user_id_to_remove}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Teams", "Team Membership"],
    summary="Видалити учасника з команди (адміністратор групи)"
)
async def remove_user_from_team(
    user_id_to_remove: int = Path(..., description="ID користувача, якого видаляють з команди"),
    team_context: dict = Depends(check_team_management_permissions),
    db_session: DBSession = Depends()
):
    team = team_context["team"]
    current_admin: UserModel = team_context["current_user"]
    group_id: int = team_context["group_id"]

    logger.info(
        f"Адміністратор {current_admin.email} видаляє користувача ID {user_id_to_remove} "
        f"з команди ID {team.id} (група {group_id})."
    )
    membership_service = TeamMembershipService(db_session)

    # TODO: Додати перевірку, чи не видаляється останній учасник/лідер, якщо є така логіка

    success = await membership_service.remove_user_from_team(
        team_id=team.id,
        user_id_to_remove=user_id_to_remove,
        actor_id=current_admin.id
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Учасника не знайдено в команді або не вдалося видалити.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/teams/__init__.py
# з префіксом /groups/{group_id}/teams/{team_id}/members
