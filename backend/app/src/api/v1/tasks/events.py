# backend/app/src/api/v1/tasks/events.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для CRUD операцій над сутністю "Подія".
Події є схожими на завдання, але зазвичай представляють заплановані заходи.
"""
from typing import List, Optional
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    # TODO: Використати або створити залежності для перевірки прав доступу до подій/груп,
    # аналогічні тим, що можуть бути для завдань (наприклад, check_event_view_permission)
    paginator
)
from backend.app.src.api.v1.groups.groups import check_group_edit_permission, check_group_view_permission  # Тимчасово
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.tasks.event import (
    EventCreate, EventUpdate, EventResponse, EventDetailedResponse
)
from backend.app.src.core.pagination import PagedResponse, PageParams  # Використовуємо з core.pagination
from backend.app.src.services.tasks.event import EventService
from backend.app.src.services.groups.membership import GroupMembershipService  # Для перевірки членства
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter()


# Залежність для отримання EventService
async def get_event_service(session: AsyncSession = Depends(get_api_db_session)) -> EventService:
    """Залежність FastAPI для отримання екземпляра EventService."""
    return EventService(db_session=session)


# Залежність для GroupMembershipService (для перевірки прав)
async def get_membership_service_dep(session: AsyncSession = Depends(get_api_db_session)) -> GroupMembershipService:
    return GroupMembershipService(db_session=session)


# Допоміжна функція-залежність для перевірки прав редагування події
async def event_edit_permission_dependency(
        event_id: UUID = Path(..., description="ID Події"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        event_service: EventService = Depends(get_event_service),
        membership_service: GroupMembershipService = Depends(get_membership_service_dep)
) -> UserModel:
    event_orm = await event_service.get_event_orm_by_id(event_id)  # Потрібен метод, що повертає ORM модель
    if not event_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Подію не знайдено")  # i18n
    if current_user.is_superuser:
        return current_user

    membership = await membership_service.get_membership_details(group_id=event_orm.group_id, user_id=current_user.id)
    if not membership or not membership.is_active or membership.role.code != "ADMIN":  # ADMIN_ROLE_CODE
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Недостатньо прав для редагування цієї події.")
    return current_user


# Допоміжна функція-залежність для перевірки прав перегляду події
async def event_view_permission_dependency(
        event_id: UUID = Path(..., description="ID Події"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        event_service: EventService = Depends(get_event_service),
        membership_service: GroupMembershipService = Depends(get_membership_service_dep)
) -> UserModel:
    event_orm = await event_service.get_event_orm_by_id(event_id)
    if not event_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Подію не знайдено")  # i18n
    if current_user.is_superuser:
        return current_user

    membership = await membership_service.get_membership_details(group_id=event_orm.group_id, user_id=current_user.id)
    if not membership or not membership.is_active:
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ви не є членом групи цієї події.")
    return current_user


@router.post(
    "/",
    response_model=EventDetailedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нової події",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру створити нову подію в межах групи."  # i18n
)
async def create_event(
        event_in: EventCreate,  # group_id має бути в EventCreate
        # TODO: Використати залежність, що перевіряє права адміна на event_in.group_id
        current_user: UserModel = Depends(get_current_active_user),  # Тимчасово, потрібна перевірка адміна групи
        event_service: EventService = Depends(get_event_service),
        membership_service: GroupMembershipService = Depends(get_membership_service_dep)  # Для перевірки прав
) -> EventDetailedResponse:
    """
    Створює нову подію.
    Перевіряє, чи є `current_user` адміністратором групи, вказаної в `event_in.group_id`, або суперюзером.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' намагається створити подію '{event_in.title}' в групі ID '{event_in.group_id}'.")

    if not current_user.is_superuser:
        membership = await membership_service.get_membership_details(group_id=event_in.group_id,
                                                                     user_id=current_user.id)
        if not membership or not membership.is_active or membership.role.code != "ADMIN":  # ADMIN_ROLE_CODE
            # i18n
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Ви не є адміністратором вказаної групи для створення події.")

    try:
        # EventService.create_event тепер приймає event_create_data та creator_id
        created_event = await event_service.create_event(
            event_create_data=event_in,
            creator_user_id=current_user.id
        )
        return created_event  # Сервіс вже повертає EventDetailedResponse
    except ValueError as e:
        logger.warning(f"Помилка створення події '{event_in.title}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні події '{event_in.title}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/",
    response_model=PagedResponse[EventResponse],
    summary="Отримання списку подій",  # i18n
    description="""Повертає список подій з пагінацією.
    Фільтрується за `group_id`, якщо надано (користувач має бути членом групи або суперюзером).
    Якщо `group_id` не надано, суперюзер бачить усі події, звичайний користувач - події з усіх своїх груп."""  # i18n
)
async def read_events(
        group_id: Optional[UUID] = Query(None, description="ID групи для фільтрації подій"),  # i18n
        page_params: PageParams = Depends(paginator),
        current_user: UserModel = Depends(get_current_active_user),
        event_service: EventService = Depends(get_event_service),
        membership_service: GroupMembershipService = Depends(get_membership_service_dep)
) -> PagedResponse[EventResponse]:
    """
    Отримує список подій з пагінацією.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' запитує список подій. Група: {group_id}, сторінка: {page_params.page}.")

    if group_id and not current_user.is_superuser:
        membership = await membership_service.get_membership_details(group_id=group_id, user_id=current_user.id)
        if not membership or not membership.is_active:
            # i18n
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ви не є членом вказаної групи.")

    # TODO: EventService.list_events_paginated має обробляти логіку доступу та повертати (items, total_count)
    events_orm, total_events = await event_service.list_events_paginated(
        user_id_context=current_user.id,
        is_superuser_context=current_user.is_superuser,
        group_id_filter=group_id,
        skip=page_params.skip,
        limit=page_params.limit
        # TODO: Передати інші фільтри (статус, тип, дати) з Query параметрів сюди
    )

    return PagedResponse[EventResponse](
        total=total_events,
        page=page_params.page,
        size=page_params.size,
        results=[EventResponse.model_validate(event) for event in events_orm]  # Pydantic v2
    )


@router.get(
    "/{event_id}",
    response_model=EventDetailedResponse,
    summary="Отримання інформації про подію за ID",  # i18n
    description="Повертає детальну інформацію про конкретну подію. Доступно члену групи події або суперюзеру.",  # i18n
    dependencies=[Depends(event_view_permission_dependency)]
)
async def read_event_by_id(
        event_id: UUID,
        # current_user_with_permission: UserModel = Depends(event_view_permission_dependency), # Вже перевірено
        event_service: EventService = Depends(get_event_service)
) -> EventDetailedResponse:
    """
    Отримує інформацію про подію за її ID.
    Доступ контролюється залежністю `event_view_permission_dependency`.
    """
    logger.debug(f"Запит деталей події ID: {event_id}")
    event_details = await event_service.get_event_by_id(event_id=event_id, include_details=True)
    if not event_details:  # Малоймовірно
        logger.warning(f"Подію з ID '{event_id}' не знайдено (після перевірки прав).")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Подію не знайдено.")
    return event_details


@router.put(
    "/{event_id}",
    response_model=EventDetailedResponse,
    summary="Оновлення інформації про подію",  # i18n
    description="Дозволяє адміністратору групи події або суперюзеру оновити дані існуючої події.",  # i18n
    dependencies=[Depends(event_edit_permission_dependency)]
)
async def update_event(
        event_id: UUID,
        event_in: EventUpdate,
        current_user_with_permission: UserModel = Depends(event_edit_permission_dependency),
        event_service: EventService = Depends(get_event_service)
) -> EventDetailedResponse:
    """
    Оновлює дані події.
    Доступно адміністратору групи події або суперюзеру.
    """
    logger.info(f"Користувач ID '{current_user_with_permission.id}' намагається оновити подію ID '{event_id}'.")
    try:
        updated_event = await event_service.update_event(
            event_id=event_id,
            event_update_data=event_in,
            current_user_id=current_user_with_permission.id
        )
        if not updated_event:  # Малоймовірно
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Подію не знайдено або оновлення не вдалося.")
        return updated_event
    except ValueError as e:
        logger.warning(f"Помилка валідації при оновленні події ID '{event_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні події ID '{event_id}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення події",  # i18n
    description="Дозволяє адміністратору групи події або суперюзеру видалити подію.",  # i18n
    dependencies=[Depends(event_edit_permission_dependency)]
)
async def delete_event(
        event_id: UUID,
        current_user_with_permission: UserModel = Depends(event_edit_permission_dependency),
        event_service: EventService = Depends(get_event_service)
):
    """
    Видаляє подію.
    Доступно адміністратору групи події або суперюзеру.
    """
    logger.info(f"Користувач ID '{current_user_with_permission.id}' намагається видалити подію ID '{event_id}'.")
    try:
        success = await event_service.delete_event(
            event_id=event_id,
            current_user_id=current_user_with_permission.id
        )
        if not success:
            logger.warning(f"Не вдалося видалити подію ID '{event_id}' (сервіс повернув False).")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Подію не знайдено або не вдалося видалити.")
    except ValueError as e:
        logger.warning(f"Помилка бізнес-логіки при видаленні події ID '{event_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні події ID '{event_id}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    return None


logger.info("Роутер для CRUD операцій з подіями визначено.")
