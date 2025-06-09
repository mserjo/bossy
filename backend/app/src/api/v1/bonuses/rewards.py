# backend/app/src/api/v1/bonuses/rewards.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user # May need get_current_active_superuser
from app.src.models.auth import User as UserModel
# from app.src.models.bonuses import Reward as RewardModel # Потрібна модель нагороди
from app.src.schemas.bonuses.reward import ( # Схеми для нагород
    RewardCreate,
    RewardUpdate,
    RewardResponse,
    RedeemRewardRequest # Може бути порожньою або містити кількість
)
from app.src.schemas.bonuses.transaction import AccountTransactionResponse # Для відповіді при придбанні
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.bonuses.reward import RewardService # Сервіс для нагород

router = APIRouter()

@router.post(
    "/", # Шлях відносно /bonuses/rewards
    response_model=RewardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нової нагороди (Адмін/Суперюзер)",
    description="Дозволяє адміністратору групи або суперюзеру створити нову нагороду, яку користувачі зможуть придбати за бонусні бали."
)
async def create_reward(
    reward_in: RewardCreate, # Очікує name, description, points_cost, group_id (якщо специфічна для групи), quantity, тощо.
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    reward_service: RewardService = Depends()
):
    '''
    Створює нову нагороду.
    - `group_id`: ID групи, для якої доступна нагорода (None для глобальних).
    - `name`, `description`, `points_cost`, `quantity_available`.
    '''
    if not hasattr(reward_service, 'db_session') or reward_service.db_session is None:
        reward_service.db_session = db

    # Перевірка прав (чи є користувач адміном групи або суперюзером) - логіка в сервісі
    created_reward = await reward_service.create_reward(
        reward_create_schema=reward_in,
        requesting_user=current_user
    )
    # Сервіс має кидати HTTPException у разі помилок
    return RewardResponse.model_validate(created_reward)

@router.get(
    "/",
    response_model=PaginatedResponse[RewardResponse],
    summary="Отримання списку доступних нагород",
    description="""Повертає список нагород, доступних для придбання, з пагінацією.
    Може фільтруватися за групою (`group_id`) або показувати глобальні та групові нагороди, доступні користувачу."""
)
async def read_available_rewards(
    group_id: Optional[int] = Query(None, description="ID групи для фільтрації нагород"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Для визначення доступних нагород
    reward_service: RewardService = Depends()
):
    '''
    Отримує список доступних нагород.
    Доступність може залежати від групи користувача.
    '''
    if not hasattr(reward_service, 'db_session') or reward_service.db_session is None:
        reward_service.db_session = db

    total_rewards, rewards = await reward_service.get_available_rewards(
        requesting_user=current_user,
        group_id=group_id,
        skip=page_params.skip,
        limit=page_params.limit
    )

    return PaginatedResponse[RewardResponse]( # Явно вказуємо тип Generic
        total=total_rewards,
        page=page_params.page,
        size=page_params.size,
        results=[RewardResponse.model_validate(reward) for reward in rewards]
    )

@router.get(
    "/{reward_id}",
    response_model=RewardResponse,
    summary="Отримання інформації про нагороду за ID",
    description="Повертає детальну інформацію про конкретну нагороду."
)
async def read_reward_by_id(
    reward_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Для перевірки доступу, якщо нагороди обмежені
    reward_service: RewardService = Depends()
):
    '''
    Отримує інформацію про нагороду за її ID.
    Сервіс може перевіряти доступність нагороди для користувача.
    '''
    if not hasattr(reward_service, 'db_session') or reward_service.db_session is None:
        reward_service.db_session = db

    reward = await reward_service.get_reward_by_id(reward_id=reward_id, requesting_user=current_user)
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Нагорода з ID {reward_id} не знайдена або доступ заборонено."
        )
    return RewardResponse.model_validate(reward)

@router.put(
    "/{reward_id}",
    response_model=RewardResponse,
    summary="Оновлення інформації про нагороду (Адмін/Суперюзер)",
    description="Дозволяє адміністратору групи або суперюзеру оновити існуючу нагороду."
)
async def update_reward(
    reward_id: int,
    reward_in: RewardUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    reward_service: RewardService = Depends()
):
    '''
    Оновлює дані нагороди.
    Перевірка прав - у сервісі.
    '''
    if not hasattr(reward_service, 'db_session') or reward_service.db_session is None:
        reward_service.db_session = db

    updated_reward = await reward_service.update_reward(
        reward_id=reward_id,
        reward_update_schema=reward_in,
        requesting_user=current_user
    )
    # Сервіс має кидати HTTPException у разі помилок
    return RewardResponse.model_validate(updated_reward)

@router.delete(
    "/{reward_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення нагороди (Адмін/Суперюзер)",
    description="Дозволяє адміністратору групи або суперюзеру видалити нагороду."
)
async def delete_reward(
    reward_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    reward_service: RewardService = Depends()
):
    '''
    Видаляє нагороду.
    Перевірка прав - у сервісі.
    '''
    if not hasattr(reward_service, 'db_session') or reward_service.db_session is None:
        reward_service.db_session = db

    success = await reward_service.delete_reward(reward_id=reward_id, requesting_user=current_user)
    if not success: # Сервіс має кидати HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Або 403
            detail=f"Не вдалося видалити нагороду з ID {reward_id}. Можливо, її не існує або у вас немає прав."
        )
    # HTTP 204 No Content

@router.post(
    "/{reward_id}/redeem",
    response_model=AccountTransactionResponse, # Успішне придбання створює транзакцію списання
    summary="Придбання нагороди користувачем",
    description="Дозволяє поточному користувачу придбати нагороду за бонусні бали."
)
async def redeem_reward(
    reward_id: int = Path(..., description="ID нагороди, яку користувач хоче придбати"),
    redeem_request: Optional[RedeemRewardRequest] = None, # Може містити кількість, якщо нагорода дозволяє >1
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    reward_service: RewardService = Depends()
):
    '''
    Поточний користувач придбає нагороду.
    Сервіс перевіряє:
    - Чи існує нагорода та чи доступна вона (кількість, активність).
    - Чи достатньо балів у користувача.
    - Списує бали та створює транзакцію.
    - Зменшує кількість доступних нагород, якщо обмежена.
    '''
    if not hasattr(reward_service, 'db_session') or reward_service.db_session is None:
        reward_service.db_session = db

    request_data = redeem_request if redeem_request is not None else RedeemRewardRequest()

    transaction = await reward_service.redeem_reward(
        reward_id=reward_id,
        requesting_user=current_user,
        redeem_request_schema=request_data
    )
    # Сервіс має кидати HTTPException у разі помилок (недостатньо балів, нагорода недоступна тощо)
    return AccountTransactionResponse.model_validate(transaction)

# Міркування:
# 1.  Схеми: `RewardCreate`, `RewardUpdate`, `RewardResponse`, `RedeemRewardRequest` з `app.src.schemas.bonuses.reward`.
#     `AccountTransactionResponse` для результату придбання.
# 2.  Сервіс `RewardService`: Керує логікою CRUD нагород та процесом їх придбання.
#     - Перевіряє права на управління нагородами.
#     - Обробляє логіку придбання: перевірка балансу, списання балів, оновлення кількості нагород.
# 3.  Права доступу:
#     - CRUD нагород: Адміністратори груп (для групових нагород), суперюзери.
#     - Перегляд списку/деталей: Всі користувачі (з фільтрацією за доступністю).
#     - Придбання: Будь-який аутентифікований користувач.
# 4.  Пагінація: Для списку доступних нагород.
# 5.  URL-и: Цей роутер буде підключений до `bonuses_router` з префіксом `/rewards`.
# 6.  Коментарі: Українською мовою.
