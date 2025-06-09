# backend/app/src/api/v1/tasks/events.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user
from app.src.models.auth import User as UserModel
from app.src.models.tasks import Event as EventModel # Потрібна модель події
from app.src.schemas.tasks.event import ( # Схеми для подій
    EventCreate,
    EventUpdate,
    EventResponse
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.tasks.event import EventService # Сервіс для подій

router = APIRouter()

@router.post(
    "/", # Шлях відносно префіксу, який буде /tasks/events (або просто /events, якщо tasks_router включає його з префіксом /events)
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нової події",
    description="Дозволяє адміністратору групи або суперюзеру створити нову подію в межах групи."
)
async def create_event(
    event_in: EventCreate, # Очікує group_id в тілі запиту
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    event_service: EventService = Depends()
):
    '''
    Створює нову подію.

    - **title**: Назва події (обов'язково).
    - **description**: Опис події (опціонально).
    - **group_id**: ID групи, до якої належить подія (обов'язково).
    - **event_type_id**: ID типу події (опціонально, якщо є типи подій).
    - **start_time**: Час початку події (опціонально).
    - **end_time**: Час завершення події (опціонально).
    - ... інші поля з EventCreate ...
    '''
    if not hasattr(event_service, 'db_session') or event_service.db_session is None:
        event_service.db_session = db

    created_event = await event_service.create_event(
        event_create_schema=event_in,
        requesting_user=current_user
    )
    if not created_event: # Сервіс має кидати HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося створити подію."
        )
    return EventResponse.model_validate(created_event)

@router.get(
    "/",
    response_model=PaginatedResponse[EventResponse],
    summary="Отримання списку подій",
    description="""Повертає список подій з пагінацією.
    Може фільтруватися за групою (`group_id`) або повертати події, доступні поточному користувачеві."""
)
async def read_events(
    group_id: Optional[int] = Query(None, description="ID групи для фільтрації подій"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    event_service: EventService = Depends()
):
    '''
    Отримує список подій з пагінацією.
    '''
    if not hasattr(event_service, 'db_session') or event_service.db_session is None:
        event_service.db_session = db

    total_events, events = await event_service.get_events_for_user(
        user=current_user,
        group_id=group_id,
        skip=page_params.skip,
        limit=page_params.limit
    )

    return PaginatedResponse[EventResponse]( # Явно вказуємо тип Generic
        total=total_events,
        page=page_params.page,
        size=page_params.size,
        results=[EventResponse.model_validate(event) for event in events]
    )

@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Отримання інформації про подію за ID",
    description="Повертає детальну інформацію про конкретну подію. Доступно, якщо користувач має доступ до групи події."
)
async def read_event_by_id(
    event_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    event_service: EventService = Depends()
):
    '''
    Отримує інформацію про подію за її ID.
    '''
    if not hasattr(event_service, 'db_session') or event_service.db_session is None:
        event_service.db_session = db

    event = await event_service.get_event_by_id_for_user(event_id=event_id, user=current_user)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Подія з ID {event_id} не знайдена або доступ заборонено."
        )
    return EventResponse.model_validate(event)

@router.put(
    "/{event_id}",
    response_model=EventResponse,
    summary="Оновлення інформації про подію",
    description="Дозволяє адміністратору групи або суперюзеру оновити дані існуючої події."
)
async def update_event(
    event_id: int,
    event_in: EventUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    event_service: EventService = Depends()
):
    '''
    Оновлює дані події.
    '''
    if not hasattr(event_service, 'db_session') or event_service.db_session is None:
        event_service.db_session = db

    updated_event = await event_service.update_event(
        event_id=event_id,
        event_update_schema=event_in,
        requesting_user=current_user
    )
    if not updated_event: # Сервіс має кидати HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Подію з ID {event_id} не знайдено або оновлення не вдалося/заборонено."
        )
    return EventResponse.model_validate(updated_event)

@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення події",
    description="Дозволяє адміністратору групи або суперюзеру видалити подію."
)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    event_service: EventService = Depends()
):
    '''
    Видаляє подію.
    '''
    if not hasattr(event_service, 'db_session') or event_service.db_session is None:
        event_service.db_session = db

    success = await event_service.delete_event(event_id=event_id, requesting_user=current_user)
    if not success: # Сервіс має кидати HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Не вдалося видалити подію з ID {event_id}. Можливо, її не існує або у вас немає прав."
        )
    # HTTP 204 No Content

# Міркування:
# 1.  Схеми: `EventCreate`, `EventUpdate`, `EventResponse` з `app.src.schemas.tasks.event`.
#     `EventCreate` має містити `group_id`.
# 2.  Сервіс `EventService`: Аналогічно до `TaskService`, керує логікою та правами для подій.
#     Методи: `create_event`, `get_events_for_user`, `get_event_by_id_for_user`, `update_event`, `delete_event`.
# 3.  Права доступу: Аналогічні до задач.
# 4.  Пагінація: Для списку подій.
# 5.  Коментарі: Українською мовою.
# 6.  URL-и: Цей роутер буде підключений до `tasks_router` (в `tasks/__init__.py`)
#     з префіксом `/events`. Таким чином, шляхи будуть `/api/v1/tasks/events/`, `/api/v1/tasks/events/{event_id}`.
