# backend/app/src/api/v1/groups/invitation.py
from typing import List, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Query
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user
from app.src.models.auth import User as UserModel
from app.src.schemas.groups.invitation import ( # Схеми для запрошень
    GroupInvitationCreate,
    GroupInvitationResponse,
    # InvitationAcceptAction # Може бути просто ID або код, або порожнє тіло для decline - зараз не використовується явно
)
from app.src.schemas.groups.membership import GroupMembershipResponse # Для відповіді при прийнятті запрошення
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams # Для пагінації списку запрошень
from app.src.services.groups.invitation import GroupInvitationService # Сервіс для запрошень
# from app.src.core.permissions import GroupPermissionsChecker

router = APIRouter()

# Ендпоінти, що стосуються конкретної групи (керування запрошеннями адміном)
group_specific_router = APIRouter()

@group_specific_router.post(
    "/", # Відносно {group_id}/invitations
    response_model=GroupInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення запрошення до групи",
    description="Дозволяє адміністратору групи або суперюзеру створити запрошення для користувача приєднатися до групи."
)
async def create_group_invitation(
    group_id: int = Path(... , description="ID групи, до якої створюється запрошення"),
    invitation_in: GroupInvitationCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    invitation_service: GroupInvitationService = Depends()
):
    '''
    Створює нове запрошення до групи.
    - `invitation_in` може вказувати конкретного `user_id` (пряме запрошення) або тип запрошення (наприклад, багаторазовий код).
    - Потрібна перевірка прав: `current_user` має бути адміном `group_id` або суперюзером.
    '''
    if not hasattr(invitation_service, 'db_session') or invitation_service.db_session is None:
        invitation_service.db_session = db

    new_invitation = await invitation_service.create_invitation(
        group_id=group_id,
        invitation_create_schema=invitation_in,
        requesting_user=current_user
    )
    # Сервіс має обробляти помилки (група не знайдена, користувач не адмін, помилка створення)
    return GroupInvitationResponse.model_validate(new_invitation)

@group_specific_router.get(
    "/", # Відносно {group_id}/invitations
    response_model=PaginatedResponse[GroupInvitationResponse],
    summary="Список запрошень для групи (Адмін/Суперюзер)",
    description="Повертає список активних запрошень для вказаної групи. Доступно адміністраторам групи або суперюзерам."
)
async def list_group_invitations(
    group_id: int = Path(... , description="ID групи, для якої переглядаються запрошення"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    invitation_service: GroupInvitationService = Depends()
):
    '''
    Отримує список запрошень для конкретної групи.
    '''
    if not hasattr(invitation_service, 'db_session') or invitation_service.db_session is None:
        invitation_service.db_session = db

    total_invitations, invitations = await invitation_service.get_invitations_for_group(
        group_id=group_id,
        requesting_user=current_user,
        skip=page_params.skip,
        limit=page_params.limit
    )

    return PaginatedResponse[GroupInvitationResponse]( # Явно вказуємо тип Generic
        total=total_invitations,
        page=page_params.page,
        size=page_params.size,
        results=[GroupInvitationResponse.model_validate(inv) for inv in invitations]
    )

@group_specific_router.delete(
    "/{invitation_id}", # Відносно {group_id}/invitations
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Відкликання/видалення запрошення (Адмін/Суперюзер)",
    description="Дозволяє адміністратору групи або суперюзеру відкликати (видалити) запрошення."
)
async def revoke_group_invitation(
    group_id: int = Path(... , description="ID групи, до якої належить запрошення"),
    invitation_id: int = Path(... , description="ID запрошення, яке відкликається"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    invitation_service: GroupInvitationService = Depends()
):
    '''
    Відкликає (видаляє) запрошення.
    '''
    if not hasattr(invitation_service, 'db_session') or invitation_service.db_session is None:
        invitation_service.db_session = db

    success = await invitation_service.revoke_invitation(
        invitation_id=invitation_id,
        group_id=group_id, # Для додаткової перевірки, що запрошення належить групі
        requesting_user=current_user
    )
    if not success:
        # Сервіс має кидати відповідні HTTPException (403, 404)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Або інший код, якщо логіка сервісу це передбачає
            detail="Не вдалося відкликати запрошення. Можливо, воно не існує, не належить цій групі, або у вас немає прав."
        )
    # HTTP 204 No Content

# Загальні ендпоінти для запрошень (для користувачів, що приймають/відхиляють)
user_invitations_router = APIRouter()

@user_invitations_router.get(
    "/pending",
    response_model=List[GroupInvitationResponse], # Зазвичай не так багато, щоб потребувати пагінації
    summary="Список моїх активних запрошень",
    description="Повертає список активних запрошень для поточного аутентифікованого користувача."
)
async def list_my_pending_invitations(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    invitation_service: GroupInvitationService = Depends()
):
    '''
    Отримує список активних запрошень, надісланих поточному користувачеві.
    '''
    if not hasattr(invitation_service, 'db_session') or invitation_service.db_session is None:
        invitation_service.db_session = db

    invitations = await invitation_service.get_pending_invitations_for_user(user=current_user)
    return [GroupInvitationResponse.model_validate(inv) for inv in invitations]

@user_invitations_router.post(
    "/{invitation_identifier}/accept", # invitation_identifier може бути ID або унікальним кодом
    response_model=GroupMembershipResponse, # Повертає інформацію про нове членство
    status_code=status.HTTP_201_CREATED,
    summary="Прийняття запрошення до групи",
    description="Дозволяє користувачу прийняти запрошення, використовуючи його ID або унікальний код."
)
async def accept_group_invitation(
    invitation_identifier: str = Path(..., description="ID запрошення або унікальний код"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    invitation_service: GroupInvitationService = Depends()
):
    '''
    Приймає запрошення до групи.
    `invitation_identifier` може бути числовим ID (якщо це пряме запрошення для користувача)
    або рядковим кодом (для загальних запрошень-посилань).
    Сервіс має розрізняти ці випадки.
    '''
    if not hasattr(invitation_service, 'db_session') or invitation_service.db_session is None:
        invitation_service.db_session = db

    new_membership = await invitation_service.accept_invitation(
        invitation_identifier=invitation_identifier,
        user_accepting=current_user
    )
    # Сервіс має обробляти помилки (запрошення не знайдено, недійсне, користувач вже член)
    # та створити GroupMembership
    return GroupMembershipResponse.model_validate(new_membership)

@user_invitations_router.post(
    "/{invitation_identifier}/decline", # invitation_identifier може бути ID або унікальним кодом
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Відхилення запрошення до групи",
    description="Дозволяє користувачу відхилити запрошення, використовуючи його ID або унікальний код."
)
async def decline_group_invitation(
    invitation_identifier: str = Path(..., description="ID запрошення або унікальний код"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    invitation_service: GroupInvitationService = Depends()
):
    '''
    Відхиляє запрошення до групи.
    Запрошення може бути позначене як відхилене або видалене.
    '''
    if not hasattr(invitation_service, 'db_session') or invitation_service.db_session is None:
        invitation_service.db_session = db

    success = await invitation_service.decline_invitation(
        invitation_identifier=invitation_identifier,
        user_declining=current_user
    )
    if not success:
        # Сервіс має кидати відповідні HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Або інший код
            detail="Не вдалося відхилити запрошення. Можливо, воно не існує або вже неактивне."
        )
    # HTTP 204 No Content

# Головний роутер для цього файлу, який об'єднує spezifische та загальні ендпоінти
router.include_router(group_specific_router, prefix="/{group_id}/invitations", tags=["Group Invitations (Admin Actions)"]) # Змінено тег для ясності
router.include_router(user_invitations_router, prefix="/invitations", tags=["Group Invitations (User Actions)"])


# Міркування:
# 1.  Структура роутерів: Використано два під-роутери:
#     - `group_specific_router`: для дій адміна/суперюзера над запрошеннями конкретної групи (шляхи з `/{group_id}/invitations`).
#     - `user_invitations_router`: для дій користувача з його запрошеннями (шляхи з `/invitations`).
#     Основний `router` цього файлу їх об'єднує. Теги допомагають розрізнити їх в документації.
# 2.  Схеми: `GroupInvitationCreate`, `GroupInvitationResponse`,
#     `GroupMembershipResponse` (для відповіді при прийнятті запрошення).
#     `InvitationAcceptAction` не використовується, оскільки додаткові дані для прийняття не передбачені в поточній структурі.
# 3.  Сервіс `GroupInvitationService`: Керує логікою створення, валідації, прийняття, відхилення, відкликання запрошень.
#     - Розрізняє прямі запрошення (на user_id) та загальні (коди/посилання).
#     - Обробляє термін дії запрошень, кількість використань.
#     - Створює `GroupMembership` при успішному прийнятті.
# 4.  Права доступу:
#     - Створення/список/відкликання для групи: адміни групи, суперюзери.
#     - Список "моїх" запрошень: поточний користувач.
#     - Прийняття/відхилення: поточний користувач (якщо запрошення для нього або загальне).
# 5.  `invitation_identifier`: Може бути `int` (ID) або `str` (код). Сервіс має це обробляти.
#     Використання `str` у шляху є більш гнучким. `Path(..., description="...")` додано для ясності.
# 6.  Коментарі: Українською мовою.
# 7.  Теги: Змінено тег для `group_specific_router` на "Group Invitations (Admin Actions)" для більшої чіткості.
