# backend/app/src/api/v1/groups/polls.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління опитуваннями/голосуваннями в групі API v1.

Цей модуль надає API для адміністраторів групи для:
- Створення нових опитувань/голосувань.
- Перегляду списку опитувань в групі.
- Отримання деталей та результатів конкретного опитування.
- Оновлення (наприклад, закриття) опитування.
- Видалення опитування.

Також може включати ендпоінти для учасників групи для голосування.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body, Response
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.groups.poll import (
    PollSchema,
    PollCreateSchema,
    PollUpdateSchema,
    PollVoteSchema, # Для голосування
    PollWithResultsSchema # Для відображення результатів
)
from backend.app.src.services.groups.poll_service import PollService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission, group_member_permission
from backend.app.src.models.auth.user import UserModel
from backend.app.src.models.groups.poll import PollModel # Для type hint

logger = get_logger(__name__)
router = APIRouter()

# Залежність для перевірки прав на опитування (адмін групи для CRUD, учасник для голосування/перегляду)
async def check_poll_permissions(
    group_id: int = Path(...),
    poll_id: int = Path(...),
    access_check: dict = Depends(group_member_permission), # Перевіряє членство в групі
    db_session: DBSession = Depends()
) -> dict: # Повертає опитування, поточного користувача та group_id
    poll_service = PollService(db_session)
    poll = await poll_service.get_poll_by_id_and_group_id(poll_id=poll_id, group_id=group_id)
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Опитування не знайдено в цій групі.")
    return {"poll": poll, "current_user": access_check["current_user"], "group_id": group_id}


@router.post(
    "", # Відповідає /groups/{group_id}/polls
    response_model=PollSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Groups", "Group Polls"],
    summary="Створити нове опитування в групі (адміністратор групи)"
)
async def create_group_poll_endpoint(
    group_id: int = Path(..., description="ID групи"),
    poll_in: PollCreateSchema,
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адмін {current_admin.email} створює нове опитування '{poll_in.question}' для групи {group_id}.")

    if poll_in.group_id != group_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Невідповідність ID групи.")

    poll_service = PollService(db_session)
    try:
        new_poll = await poll_service.create_poll(
            poll_create_data=poll_in,
            creator_id=current_admin.id
        )
        return new_poll
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка створення опитування в групі {group_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

@router.get(
    "",
    response_model=List[PollSchema], # Може бути PollWithResultsSchema, якщо показувати результати адміну
    tags=["Groups", "Group Polls"],
    summary="Отримати список опитувань в групі"
)
async def list_group_polls_endpoint(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission), # Учасники бачать список
    db_session: DBSession = Depends(),
    is_open: Optional[bool] = Query(None, description="Фільтр за статусом відкритості опитування")
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує список опитувань для групи {group_id}.")
    poll_service = PollService(db_session)
    polls = await poll_service.get_polls_for_group(group_id=group_id, is_open_filter=is_open)
    return polls

@router.get(
    "/{poll_id}",
    response_model=PollWithResultsSchema, # Показуємо результати, якщо опитування закрите або користувач - адмін
    tags=["Groups", "Group Polls"],
    summary="Отримати деталі та результати опитування"
)
async def get_group_poll_details_endpoint(
    poll_context: dict = Depends(check_poll_permissions) # Залежність повертає опитування
):
    poll: PollModel = poll_context["poll"]
    current_user: UserModel = poll_context["current_user"]
    # is_admin = await PollService(DBSessionManager.get_session()).is_user_group_admin(user_id=current_user.id, group_id=poll.group_id)
    # TODO: Логіка відображення результатів (PollService має повернути PollWithResultsSchema)
    # Наприклад, якщо опитування закрите, або користувач адмін - показувати результати.
    # Інакше - лише питання та опції.
    logger.info(f"Користувач {current_user.email} запитує деталі опитування ID {poll.id}.")
    # Потрібно, щоб сервіс повернув дані у форматі PollWithResultsSchema
    # або тут конвертувати PollModel в PollWithResultsSchema
    return poll # Припускаємо, що сервіс повертає вже збагачену модель або Pydantic валідує


@router.post(
    "/{poll_id}/vote",
    response_model=PollSchema, # Повертаємо оновлене опитування (можливо, без результатів для користувача)
    tags=["Groups", "Group Polls"],
    summary="Проголосувати в опитуванні"
)
async def vote_in_group_poll_endpoint(
    vote_in: PollVoteSchema, # Містить poll_option_id
    poll_context: dict = Depends(check_poll_permissions),
    db_session: DBSession = Depends()
):
    poll: PollModel = poll_context["poll"]
    current_user: UserModel = poll_context["current_user"]

    if poll.id != vote_in.poll_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Невідповідність ID опитування.")

    logger.info(f"Користувач {current_user.email} голосує в опитуванні ID {poll.id} за опцію {vote_in.poll_option_id}.")
    poll_service = PollService(db_session)
    try:
        updated_poll = await poll_service.submit_vote(
            poll_id=poll.id,
            user_id=current_user.id,
            poll_option_id=vote_in.poll_option_id
        )
        return updated_poll # Або тільки статус успіху
    except HTTPException as e:
        raise e
    except ValueError as ve: # Напр., опитування закрите, вже голосував, невірна опція
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.put(
    "/{poll_id}",
    response_model=PollSchema,
    tags=["Groups", "Group Polls"],
    summary="Оновити опитування (напр., закрити) (адміністратор групи)"
)
async def update_group_poll_endpoint( # Перейменовано з close_group_poll
    poll_update_data: PollUpdateSchema, # Може містити is_open, question, options
    poll_context: dict = Depends(check_poll_permissions), # Використовуємо загальну перевірку
    db_session: DBSession = Depends()
):
    poll: PollModel = poll_context["poll"]
    current_user: UserModel = poll_context["current_user"]

    # Додаткова перевірка, що це адмін, якщо оновлення дозволено тільки адміну
    is_admin = await PollService(db_session).is_user_group_admin(user_id=current_user.id, group_id=poll.group_id)
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Лише адміністратор групи може оновлювати опитування.")

    logger.info(f"Адміністратор {current_user.email} оновлює опитування ID {poll.id}.")
    poll_service = PollService(db_session)
    try:
        updated_poll = await poll_service.update_poll(
            poll_id=poll.id,
            poll_update_data=poll_update_data,
            actor_id=current_user.id
        )
        return updated_poll
    except HTTPException as e:
        raise e
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.delete(
    "/{poll_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Groups", "Group Polls"],
    summary="Видалити опитування (адміністратор групи)"
)
async def delete_group_poll_endpoint(
    poll_context: dict = Depends(check_poll_permissions),
    db_session: DBSession = Depends()
):
    poll: PollModel = poll_context["poll"]
    current_user: UserModel = poll_context["current_user"]

    is_admin = await PollService(db_session).is_user_group_admin(user_id=current_user.id, group_id=poll.group_id)
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Лише адміністратор групи може видаляти опитування.")

    logger.info(f"Адміністратор {current_user.email} видаляє опитування ID {poll.id}.")
    poll_service = PollService(db_session)
    success = await poll_service.delete_poll(poll_id=poll.id, actor_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Опитування не знайдено або не вдалося видалити.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/groups/__init__.py
# з префіксом /{group_id}/polls
