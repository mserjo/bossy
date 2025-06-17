# backend/app/src/api/v1/groups/groups.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для CRUD операцій над сутністю "Група".

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List, Optional  # Generic, TypeVar, Any, Dict не використовуються
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query  # Query для можливих фільтрів
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.api.dependencies import (
    get_api_db_session,
    get_current_active_user,
    get_current_active_superuser,
    get_group_membership_service,  # Для перевірки членства/адмінства
    get_user_service,  # Непрямо може бути потрібен для GroupService
    paginator
)
from backend.app.src.models.auth.user import User as UserModel
# from backend.app.src.models.groups.group import Group as GroupModel # Не використовується прямо, відповіді через схеми
from backend.app.src.schemas.groups.group import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupDetailedResponse
)
from backend.app.src.core.pagination import PagedResponse, PageParams  # Використовуємо з core.pagination
from backend.app.src.services.groups.group import GroupService
from backend.app.src.services.groups.membership import GroupMembershipService  # Для перевірки прав
from backend.app.src.core.constants import ADMIN_ROLE_CODE # Для перевірки ролі адміна
from backend.app.src.config import settings as global_settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# TODO: Створити та використовувати залежність `get_current_active_group_admin_or_superuser`
#  яка приймає `group_id: UUID = Path(...)` та перевіряє, чи є поточний користувач
#  адміном вказаної групи або суперюзером.

router = APIRouter()


# Залежність для отримання GroupService
async def get_group_service(session: AsyncSession = Depends(get_api_db_session)) -> GroupService:
    """Залежність FastAPI для отримання екземпляра GroupService."""
    return GroupService(db_session=session)


@router.post(
    "/",
    response_model=GroupDetailedResponse,  # Повертаємо деталізовану відповідь після створення
    status_code=status.HTTP_201_CREATED,
    summary="Створення нової групи",  # i18n
    description="Дозволяє автентифікованому користувачу створити нову групу. Творець автоматично стає адміністратором групи."
    # i18n
)
async def create_group(
        group_in: GroupCreate,
        current_user: UserModel = Depends(get_current_active_user),  # Будь-який активний користувач може створити групу
        group_service: GroupService = Depends(get_group_service)
) -> GroupDetailedResponse:
    """
    Створює нову групу. Творець автоматично стає її адміністратором.
    """
    logger.info(f"Користувач ID '{current_user.id}' намагається створити групу '{group_in.name}'.")
    try:
        # GroupService.create_group має обробляти створення членства для творця з роллю ADMIN
        created_group = await group_service.create_group(
            group_create_data=group_in,
            creator_id=current_user.id
        )
        # create_group в сервісі вже повертає GroupDetailedResponse
        return created_group
    except ValueError as e:  # Помилки валідації з сервісу (напр., не знайдено тип групи)
        logger.warning(f"Помилка створення групи '{group_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except IntegrityError as e:  # На випадок, якщо сервіс не обробив унікальність (малоймовірно, але можливо)
        logger.error(f"Помилка цілісності при створенні групи '{group_in.name}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Група з такими параметрами вже існує або виник конфлікт даних.")
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні групи '{group_in.name}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при створенні групи.")


@router.get(
    "/",
    response_model=PagedResponse[GroupResponse],  # Список груп зазвичай не потребує всіх деталей
    summary="Отримання списку груп",  # i18n
    description="""Повертає список груп. Суперюзер бачить усі групи.
    Звичайний користувач бачить групи, до яких він належить.
    TODO: Додати фільтри (публічні/приватні, за назвою, типом тощо)."""  # i18n
)
# ПРИМІТКА: Реалізація цього ендпоінта потребує значного доопрацювання в сервісному шарі
# (`GroupService`) для коректного отримання списку груп для суперюзера,
# правильної пагінації (повернення total_count), та реалізації фільтрів,
# як зазначено в TODO. Поточна реалізація є частковою/заглушкою.
async def read_groups(
        page_params: PageParams = Depends(paginator),
        current_user: UserModel = Depends(get_current_active_user),  # Потрібен для визначення контексту
        group_service: GroupService = Depends(get_group_service)
        # TODO: Додати параметри фільтрації як Query(...)
) -> PagedResponse[GroupResponse]:
    """
    Отримує список груп з пагінацією.
    - Суперкористувачі бачать усі групи.
    - Звичайні користувачі бачать лише ті групи, членом яких вони є.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' запитує список груп (сторінка {page_params.page}, розмір {page_params.size}).")

    if current_user.is_superuser:
        # TODO: Реалізувати `group_service.list_all_groups_admin(skip, limit, filters...)`
        #  який може мати більше опцій фільтрації для суперюзера.
        #  Поки що використовуємо загальний метод list_user_groups, що може бути неоптимально для всіх груп.
        #  Або створити `group_service.get_all_groups_paginated(skip, limit)`
        logger.warning("[ЗАГЛУШКА] Суперюзер запитує всі групи. Потребує реалізації `list_all_groups_admin` в сервісі.")
        # Тимчасово, повернемо порожній список для суперюзера, щоб не реалізовувати повний список без фільтрів.
        # Або, якщо list_user_groups може працювати без user_id для суперюзера:
        # groups_orm, total_groups = await group_service.list_all_groups(skip=page_params.skip, limit=page_params.limit)
        groups_orm: List[Group] = []  # type: ignore
        total_groups = 0
    else:
        # GroupService.list_user_groups повертає список GroupResponse, а не ORM
        # Потрібно адаптувати або сервіс, або відповідь тут.
        # Припускаємо, що list_user_groups повертає ORM моделі для PagedResponse
        # TODO: `list_user_groups` має повертати (items, total_count) для PagedResponse
        groups_page_response_list = await group_service.list_user_groups(
            user_id=current_user.id, skip=page_params.skip, limit=page_params.limit
        )
        # Це не зовсім правильно, бо list_user_groups повертає List[GroupResponse], а не ORM
        # Для коректної пагінації потрібен метод сервісу, що повертає (List[ORM_Model], total_count)
        groups_orm = groups_page_response_list  # Тимчасово, припускаючи, що це ORM, хоча це не так
        total_groups = len(groups_orm)  # ЗАГЛУШКА для total_count
        logger.warning("Використовується заглушка для total_count при переліку груп користувача.")

    return PagedResponse[GroupResponse](
        total=total_groups,
        page=page_params.page,
        size=page_params.size,
        results=[GroupResponse.model_validate(g) for g in groups_orm]  # Pydantic v2
    )


async def check_group_view_permission(  # Залежність для перевірки прав на перегляд групи
        group_id: UUID = Path(..., description="ID групи для перевірки"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        membership_service: GroupMembershipService = Depends(get_group_membership_service)
):
    if current_user.is_superuser:
        return  # Суперюзер має доступ до будь-якої групи

    membership = await membership_service.get_membership_details(group_id=group_id, user_id=current_user.id)
    if not membership or not membership.is_active:
        logger.warning(f"Користувач ID '{current_user.id}' не має доступу до перегляду групи ID '{group_id}'.")
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Ви не є членом цієї групи або доступ обмежено.")
    return  # Доступ дозволено

# ПРИМІТКА: Ця залежність (`check_group_view_permission`) є ключовою для контролю доступу
# до інформації про групу. Вона має коректно обробляти випадки суперкористувача
# та активного членства в групі.
@router.get(
    "/{group_id}",
    response_model=GroupDetailedResponse,  # Завжди повертаємо деталі, якщо є доступ
    summary="Отримання інформації про групу за ID",  # i18n
    description="""Повертає детальну інформацію про конкретну групу.
    Доступно суперюзеру або активному члену групи.""",  # i18n
    dependencies=[Depends(check_group_view_permission)]  # Перевірка прав перед виконанням
)
async def read_group_by_id(
        group_id: UUID,  # ID тепер UUID
        group_service: GroupService = Depends(get_group_service)
        # current_user вже перевірено в check_group_view_permission
) -> GroupDetailedResponse:
    """
    Отримує інформацію про групу за її ID.
    Доступ контролюється залежністю `check_group_view_permission`.
    """
    logger.debug(f"Запит деталей групи ID: {group_id}")
    # get_group_by_id з include_details=True повертає GroupDetailedResponse
    group_details = await group_service.get_group_by_id(group_id=group_id, include_details=True)
    if not group_details:  # Малоймовірно, якщо check_group_view_permission не кинув 404 раніше
        logger.warning(f"Групу з ID '{group_id}' не знайдено (після перевірки прав).")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Групу не знайдено.")
    return group_details


# ПРИМІТКА: Ця залежність (`check_group_edit_permission`) контролює доступ до операцій
# редагування та видалення групи. Важливою є перевірка ролі адміністратора групи
# (з використанням `ADMIN_ROLE_CODE`) або прав суперкористувача.
async def check_group_edit_permission(  # Залежність для перевірки прав на редагування/видалення групи
        group_id: UUID = Path(..., description="ID групи для перевірки"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        membership_service: GroupMembershipService = Depends(get_group_membership_service)
) -> UserModel:  # Повертає UserModel для використання в ендпоінті
    if current_user.is_superuser:
        logger.debug(
            f"Користувач ID '{current_user.id}' (суперюзер) має права на редагування/видалення групи ID '{group_id}'.")
        return current_user

    membership = await membership_service.get_membership_details(group_id=group_id, user_id=current_user.id)
    if not membership or not membership.is_active or not membership.role or membership.role.code != ADMIN_ROLE_CODE:
        logger.warning(f"Користувач ID '{current_user.id}' не є адміністратором групи ID '{group_id}'. Дія заборонена.")
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Недостатньо прав для виконання цієї дії в групі.")
    logger.debug(
        f"Користувач ID '{current_user.id}' (адмін групи) має права на редагування/видалення групи ID '{group_id}'.")
    return current_user


@router.put(
    "/{group_id}",
    response_model=GroupDetailedResponse,  # Повертаємо деталізовану відповідь після оновлення
    summary="Оновлення інформації про групу",  # i18n
    description="Дозволяє суперюзеру або адміністратору групи оновити дані групи.",  # i18n
    dependencies=[Depends(check_group_edit_permission)]  # Перевірка прав
)
async def update_group(
        group_id: UUID,  # ID тепер UUID
        group_in: GroupUpdate,
        current_user_with_permission: UserModel = Depends(check_group_edit_permission),
        # Отримуємо користувача з залежності
        group_service: GroupService = Depends(get_group_service)
) -> GroupDetailedResponse:
    """
    Оновлює дані групи. Доступно суперюзеру або адміністратору групи.
    """
    logger.info(f"Користувач ID '{current_user_with_permission.id}' намагається оновити групу ID '{group_id}'.")
    try:
        updated_group = await group_service.update_group(
            group_id=group_id,
            group_update_data=group_in,
            current_user_id=current_user_with_permission.id  # Для аудиту в сервісі
        )
        if not updated_group:  # Сервіс може повернути None, якщо група не знайдена (хоча перевірка прав мала б це виявити)
            logger.warning(f"Групу ID '{group_id}' не знайдено під час оновлення (після перевірки прав).")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Групу не знайдено для оновлення.")
        return updated_group
    except ValueError as e:
        logger.warning(f"Помилка валідації при оновленні групи ID '{group_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні групи ID '{group_id}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при оновленні групи.")


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення групи",  # i18n
    description="Дозволяє суперюзеру або адміністратору групи видалити групу.",  # i18n
    dependencies=[Depends(check_group_edit_permission)]  # Перевірка прав
)
async def delete_group(
        group_id: UUID,  # ID тепер UUID
        current_user_with_permission: UserModel = Depends(check_group_edit_permission),
        group_service: GroupService = Depends(get_group_service)
):
    """
    Видаляє групу.
    Доступно суперюзеру або адміністратору групи.
    Сервіс `delete_group` має обробляти бізнес-логіку (напр., неможливість видалення, якщо єдиний адмін).
    """
    logger.info(f"Користувач ID '{current_user_with_permission.id}' намагається видалити групу ID '{group_id}'.")
    try:
        success = await group_service.delete_group(
            group_id=group_id,
            requesting_user_id=current_user_with_permission.id  # Передаємо ID для логіки сервісу
        )
        if not success:  # Якщо сервіс повертає False (наприклад, група не знайдена або не вдалося видалити)
            logger.warning(f"Не вдалося видалити групу ID '{group_id}' (сервіс повернув False).")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Групу не знайдено або не вдалося видалити.")
    except ValueError as e:  # Обробка специфічних бізнес-помилок з сервісу (напр., не можна видалити останнього адміна)
        logger.warning(f"Помилка бізнес-логіки при видаленні групи ID '{group_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні групи ID '{group_id}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при видаленні групи.")

    # Успішна відповідь HTTP 204 No Content не повинна мати тіла
    return None


# TODO: Додати ендпоінти для отримання звітів по групі (перемістити з reports.py сюди, якщо вони стосуються конкретної групи)
# або залишити reports.py, якщо це загальні звіти по групах.

logger.info("Роутер для CRUD операцій з групами визначено.")
