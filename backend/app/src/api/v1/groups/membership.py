# backend/app/src/api/v1/groups/membership.py
from typing import List, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user
from app.src.models.auth import User as UserModel
from app.src.schemas.groups.membership import ( # Схеми для членства в групі
    GroupMembershipCreate,
    GroupMembershipUpdate,
    GroupMembershipResponse
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams # Для пагінації списку членів
from app.src.services.groups.membership import GroupMembershipService # Сервіс для членства
# from app.src.core.permissions import GroupPermissionsChecker

router = APIRouter()

@router.get(
    "/{group_id}/members",
    response_model=PaginatedResponse[GroupMembershipResponse],
    summary="Отримання списку членів групи",
    description="Повертає список членів вказаної групи з пагінацією. Доступно членам групи або суперюзерам."
)
async def list_group_members(
    group_id: int,
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    membership_service: GroupMembershipService = Depends()
):
    '''
    Отримує список членів групи.
    Перевірка прав: користувач має бути членом групи або суперюзером.
    '''
    if not hasattr(membership_service, 'db_session') or membership_service.db_session is None:
        membership_service.db_session = db

    # Логіка перевірки прав та отримання даних - у сервісі
    total_members, members = await membership_service.get_members_in_group(
        group_id=group_id,
        requesting_user=current_user,
        skip=page_params.skip,
        limit=page_params.limit
    )

    return PaginatedResponse[GroupMembershipResponse]( # Явно вказуємо тип Generic
        total=total_members,
        page=page_params.page,
        size=page_params.size,
        results=[GroupMembershipResponse.model_validate(member) for member in members]
    )

@router.post(
    "/{group_id}/members",
    response_model=GroupMembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Додавання користувача до групи",
    description="Дозволяє адміністратору групи або суперюзеру додати користувача до групи."
)
async def add_group_member(
    group_id: int,
    member_in: GroupMembershipCreate, # Включає user_id та group_role_id
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    membership_service: GroupMembershipService = Depends()
):
    '''
    Додає користувача до групи з вказаною роллю.
    Перевірка прав: поточний користувач має бути адміністратором групи або суперюзером.
    '''
    if not hasattr(membership_service, 'db_session') or membership_service.db_session is None:
        membership_service.db_session = db

    # Логіка перевірки прав та додавання - у сервісі
    new_membership = await membership_service.add_member_to_group(
        group_id=group_id,
        membership_create_schema=member_in,
        requesting_user=current_user
    )
    # Сервіс має кидати HTTPException у разі помилок (не знайдено, заборонено, користувач вже член)
    return GroupMembershipResponse.model_validate(new_membership)

@router.put(
    "/{group_id}/members/{user_id}",
    response_model=GroupMembershipResponse,
    summary="Оновлення ролі члена групи",
    description="Дозволяє адміністратору групи або суперюзеру змінити роль існуючого члена групи."
)
async def update_group_member_role(
    group_id: int,
    user_id: int, # ID користувача, чию роль змінюють
    member_update: GroupMembershipUpdate, # Включає новий group_role_id
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    membership_service: GroupMembershipService = Depends()
):
    '''
    Оновлює роль користувача в групі.
    Перевірка прав: поточний користувач має бути адміністратором групи або суперюзером.
    '''
    if not hasattr(membership_service, 'db_session') or membership_service.db_session is None:
        membership_service.db_session = db

    updated_membership = await membership_service.update_member_role(
        group_id=group_id,
        user_id_to_update=user_id,
        membership_update_schema=member_update,
        requesting_user=current_user
    )
    # Сервіс має кидати HTTPException у разі помилок
    return GroupMembershipResponse.model_validate(updated_membership)

@router.delete(
    "/{group_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення члена з групи",
    description="Дозволяє адміністратору групи або суперюзеру видалити користувача з групи. Адміністратор не може видалити себе, якщо він єдиний адмін."
)
async def remove_group_member(
    group_id: int,
    user_id: int, # ID користувача, якого видаляють
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    membership_service: GroupMembershipService = Depends()
):
    '''
    Видаляє користувача з групи.
    Перевірка прав: поточний користувач має бути адміністратором групи або суперюзером.
    Обмеження: не можна видалити єдиного адміністратора.
    '''
    if not hasattr(membership_service, 'db_session') or membership_service.db_session is None:
        membership_service.db_session = db

    success = await membership_service.remove_member_from_group(
        group_id=group_id,
        user_id_to_remove=user_id,
        requesting_user=current_user
    )
    if not success:
        # Сервіс має кидати відповідні HTTPException (403, 404, 400)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Або більш конкретний код
            detail="Не вдалося видалити члена групи. Можливо, користувач не є членом, або існують обмеження (наприклад, видалення єдиного адміністратора)."
        )
    # HTTP 204 No Content

@router.post(
    "/{group_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Вихід поточного користувача з групи",
    description="Дозволяє аутентифікованому користувачу покинути групу, членом якої він є. Адміністратор не може покинути групу, якщо він єдиний адмін."
)
async def leave_group(
    group_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    membership_service: GroupMembershipService = Depends()
):
    '''
    Поточний користувач покидає групу.
    Обмеження: Адміністратор не може покинути групу, якщо він єдиний адміністратор у цій групі.
    '''
    if not hasattr(membership_service, 'db_session') or membership_service.db_session is None:
        membership_service.db_session = db

    success = await membership_service.user_leave_group(
        group_id=group_id,
        requesting_user=current_user
    )
    if not success:
        # Сервіс має кидати відповідні HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Або більш конкретний код
            detail="Не вдалося покинути групу. Можливо, ви не є членом групи, або існують обмеження (наприклад, ви єдиний адміністратор)."
        )
    # HTTP 204 No Content

# Міркування:
# 1.  URL-и: Всі ендпоінти знаходяться під `/{group_id}/members` або `/{group_id}/leave`.
#     Цей роутер буде підключений до `groups_router` без додаткового префіксу.
# 2.  Схеми: `GroupMembershipCreate`, `GroupMembershipUpdate`, `GroupMembershipResponse` з `app.src.schemas.groups.membership`.
#     `PaginatedResponse` для списку членів.
# 3.  Сервіс `GroupMembershipService`: Керує всією логікою членства, включаючи:
#     - Перевірку прав (хто може додавати, видаляти, змінювати роль, переглядати список).
#     - Валідацію (чи існує користувач, чи існує роль групи, чи не є користувач вже членом).
#     - Обмеження (не можна видалити/покинути, якщо ти єдиний адмін).
#     Методи: `get_members_in_group`, `add_member_to_group`, `update_member_role`, `remove_member_from_group`, `user_leave_group`.
# 4.  Права доступу:
#     - Список членів: члени групи, адміни групи, суперюзери.
#     - Додавання/видалення/зміна ролі: адміни групи, суперюзери.
#     - Покинути групу: сам користувач (якщо він член).
# 5.  Коментарі: Українською мовою.
# 6.  `group_role_id`: Схеми `GroupMembershipCreate` та `GroupMembershipUpdate` мають містити це поле,
#     що посилається на довідник ролей у групі (не системних ролей користувачів).
