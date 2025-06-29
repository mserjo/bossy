# backend/app/src/api/v1/teams/teams.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для основного управління командами в групі API v1.

Цей модуль надає API для:
- Створення нової команди адміністратором групи.
- Отримання списку команд у групі.
- Отримання детальної інформації про команду.
- Оновлення інформації про команду (адміністратором групи).
- Видалення команди (адміністратором групи).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Response
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.teams.team import TeamSchema, TeamCreateSchema, TeamUpdateSchema
from backend.app.src.services.teams.team_service import TeamService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission, group_member_permission
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти будуть мати префікс /groups/{group_id}/teams

@router.post(
    "", # Шлях буде /groups/{group_id}/teams
    response_model=TeamSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Teams"],
    summary="Створити нову команду в групі (адміністратор групи)"
)
async def create_team_in_group(
    team_in: TeamCreateSchema,
    group_id: int = Path(..., description="ID групи, в якій створюється команда"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    """
    Створює нову команду в зазначеній групі.
    Доступно лише адміністраторам цієї групи.
    `team_in` має містити `group_id`, який буде перевірено на відповідність `group_id` у шляху.
    """
    current_admin: UserModel = group_with_admin_rights["current_user"]

    if team_in.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID групи в тілі запиту ({team_in.group_id}) не співпадає з ID групи у шляху ({group_id})."
        )

    logger.info(
        f"Адміністратор {current_admin.email} створює нову команду '{team_in.name}' "
        f"в групі ID {group_id}."
    )
    team_service = TeamService(db_session)
    try:
        # TeamService.create_team повинен приймати TeamCreateSchema та ID користувача-творця (адміна)
        new_team = await team_service.create_team(
            team_create_data=team_in,
            creator_id=current_admin.id # або group_id, якщо сервіс так очікує
        )
        logger.info(
            f"Команда '{new_team.name}' (ID: {new_team.id}) успішно створена "
            f"в групі ID {group_id} адміністратором {current_admin.email}."
        )
        return new_team
    except HTTPException as e:
        logger.warning(f"Помилка створення команди '{team_in.name}' в групі {group_id}: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при створенні команди '{team_in.name}' в групі {group_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при створенні команди.")


@router.get(
    "", # Шлях буде /groups/{group_id}/teams
    response_model=List[TeamSchema],
    tags=["Teams"],
    summary="Отримати список команд у групі"
)
async def list_teams_in_group(
    group_id: int = Path(..., description="ID групи, для якої отримуються команди"),
    access_check: dict = Depends(group_member_permission), # Учасники групи можуть бачити команди
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
):
    """
    Повертає список команд для зазначеної групи з пагінацією.
    Доступно учасникам групи.
    """
    current_user: UserModel = access_check["current_user"]
    logger.info(
        f"Користувач {current_user.email} запитує список команд для групи ID {group_id} "
        f"(сторінка: {page}, розмір: {page_size})."
    )
    team_service = TeamService(db_session)

    teams_data = await team_service.get_teams_by_group_id(
        group_id=group_id,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    if isinstance(teams_data, dict): # Якщо сервіс повертає пагіновані дані
        teams = teams_data.get("teams", [])
        # total_teams = teams_data.get("total", 0) # Для заголовків пагінації
    else: # Якщо сервіс повертає просто список
        teams = teams_data

    return teams


@router.get(
    "/{team_id}", # Шлях буде /groups/{group_id}/teams/{team_id}
    response_model=TeamSchema,
    tags=["Teams"],
    summary="Отримати детальну інформацію про команду"
)
async def get_team_details(
    group_id: int = Path(..., description="ID групи"),
    team_id: int = Path(..., description="ID команди"),
    access_check: dict = Depends(group_member_permission), # Учасники групи можуть бачити деталі команди
    db_session: DBSession = Depends()
):
    """
    Повертає детальну інформацію про конкретну команду в групі.
    Доступно учасникам групи.
    """
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує деталі команди ID {team_id} з групи ID {group_id}.")
    team_service = TeamService(db_session)

    team = await team_service.get_team_by_id_and_group_id(team_id=team_id, group_id=group_id)
    if not team:
        logger.warning(
            f"Команду ID {team_id} в групі ID {group_id} не знайдено або доступ заборонено "
            f"для користувача {current_user.email}."
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Команду не знайдено або доступ заборонено.")
    return team


@router.put(
    "/{team_id}",
    response_model=TeamSchema,
    tags=["Teams"],
    summary="Оновити інформацію про команду (адміністратор групи)"
)
async def update_existing_team(
    team_in: TeamUpdateSchema,
    group_id: int = Path(..., description="ID групи"),
    team_id: int = Path(..., description="ID команди для оновлення"),
    group_with_admin_rights: dict = Depends(group_admin_permission), # Перевірка, що користувач адмін групи
    db_session: DBSession = Depends()
):
    """
    Оновлює інформацію про існуючу команду в групі.
    Доступно лише адміністраторам цієї групи.
    """
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} оновлює команду ID {team_id} в групі ID {group_id}."
    )
    team_service = TeamService(db_session)
    try:
        updated_team = await team_service.update_team(
            team_id=team_id,
            team_update_data=team_in,
            group_id_context=group_id,
            actor_id=current_admin.id
        )
        if not updated_team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Команду не знайдено для оновлення.")
        logger.info(f"Команда ID {team_id} в групі {group_id} успішно оновлена.")
        return updated_team
    except HTTPException as e:
        logger.warning(f"Помилка оновлення команди ID {team_id} в групі {group_id}: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при оновленні команди ID {team_id} в групі {group_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при оновленні команди.")


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Teams"],
    summary="Видалити команду (адміністратор групи)"
)
async def delete_existing_team(
    group_id: int = Path(..., description="ID групи"),
    team_id: int = Path(..., description="ID команди для видалення"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    """
    Видаляє існуючу команду з групи.
    Доступно лише адміністраторам цієї групи.
    """
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} видаляє команду ID {team_id} з групи ID {group_id}."
    )
    team_service = TeamService(db_session)
    try:
        success = await team_service.delete_team(
            team_id=team_id,
            group_id_context=group_id,
            actor_id=current_admin.id
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Команду не знайдено або не вдалося видалити.")
        logger.info(f"Команда ID {team_id} з групи {group_id} успішно видалена.")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException as e:
        logger.warning(f"Помилка видалення команди ID {team_id} з групи {group_id}: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при видаленні команди ID {team_id} з групи {group_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при видаленні команди.")

# Роутер буде підключений в backend/app/src/api/v1/teams/__init__.py
# з префіксом /groups/{group_id}/teams
