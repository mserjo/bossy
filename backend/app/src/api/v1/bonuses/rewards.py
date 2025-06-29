# backend/app/src/api/v1/bonuses/rewards.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління нагородами та їх отримання користувачами API v1.

Цей модуль надає API для:
- Адміністраторів групи: CRUD операції з нагородами (створення, перегляд, оновлення, видалення).
- Учасників групи: Перегляд списку доступних нагород та їх "покупка" (обмін на бонуси).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Response
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.bonuses.reward import RewardSchema, RewardCreateSchema, RewardUpdateSchema
# Можливо, потрібна схема для відповіді при "покупці" нагороди
# from backend.app.src.schemas.bonuses.reward import RewardRedemptionResponseSchema
from backend.app.src.services.bonuses.reward_service import RewardService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission, group_member_permission
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти будуть мати префікс /groups/{group_id}/rewards

@router.post(
    "", # Шлях буде /groups/{group_id}/rewards
    response_model=RewardSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Bonuses", "Rewards"],
    summary="Створити нову нагороду в групі (адміністратор групи)"
)
async def create_reward_in_group(
    reward_in: RewardCreateSchema,
    group_id: int = Path(..., description="ID групи, в якій створюється нагорода"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]

    if reward_in.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID групи в тілі запиту ({reward_in.group_id}) не співпадає з ID групи у шляху ({group_id})."
        )

    logger.info(
        f"Адміністратор {current_admin.email} створює нову нагороду '{reward_in.name}' "
        f"в групі ID {group_id}."
    )
    service = RewardService(db_session)
    try:
        new_reward = await service.create_reward_in_group(
            reward_create_data=reward_in,
            group_id=group_id, # Передаємо для валідації або встановлення сервісом
            creator_id=current_admin.id
        )
        return new_reward
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка створення нагороди '{reward_in.name}' в групі {group_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


@router.get(
    "",
    response_model=List[RewardSchema],
    tags=["Bonuses", "Rewards"],
    summary="Отримати список доступних нагород у групі"
)
async def list_rewards_in_group(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission), # Учасники можуть бачити нагороди
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
    # TODO: Фільтри (активні, за вартістю, за типом)
    is_active: Optional[bool] = Query(None, description="Фільтр за активністю нагороди")
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує список нагород для групи ID {group_id}.")
    service = RewardService(db_session)
    rewards_data = await service.get_rewards_in_group(
        group_id=group_id,
        skip=(page - 1) * page_size,
        limit=page_size,
        is_active=is_active
    )
    if isinstance(rewards_data, dict):
        rewards = rewards_data.get("rewards", [])
    else:
        rewards = rewards_data
    return rewards

@router.get(
    "/{reward_id}",
    response_model=RewardSchema,
    tags=["Bonuses", "Rewards"],
    summary="Отримати деталі конкретної нагороди"
)
async def get_reward_details(
    group_id: int = Path(..., description="ID групи"),
    reward_id: int = Path(..., description="ID нагороди"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends()
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує деталі нагороди ID {reward_id} з групи {group_id}.")
    service = RewardService(db_session)
    reward = await service.get_reward_by_id_and_group_id(reward_id=reward_id, group_id=group_id)
    if not reward:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Нагороду не знайдено.")
    return reward

@router.put(
    "/{reward_id}",
    response_model=RewardSchema,
    tags=["Bonuses", "Rewards"],
    summary="Оновити нагороду (адміністратор групи)"
)
async def update_existing_reward(
    reward_in: RewardUpdateSchema,
    group_id: int = Path(..., description="ID групи"),
    reward_id: int = Path(..., description="ID нагороди для оновлення"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адміністратор {current_admin.email} оновлює нагороду ID {reward_id} в групі {group_id}.")
    service = RewardService(db_session)
    try:
        updated_reward = await service.update_reward(
            reward_id=reward_id,
            reward_update_data=reward_in,
            group_id_context=group_id,
            actor_id=current_admin.id
        )
        if not updated_reward:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Нагороду не знайдено для оновлення.")
        return updated_reward
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка оновлення нагороди ID {reward_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

@router.delete(
    "/{reward_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Bonuses", "Rewards"],
    summary="Видалити нагороду (адміністратор групи)"
)
async def delete_existing_reward(
    group_id: int = Path(..., description="ID групи"),
    reward_id: int = Path(..., description="ID нагороди для видалення"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адміністратор {current_admin.email} видаляє нагороду ID {reward_id} з групи {group_id}.")
    service = RewardService(db_session)
    try:
        success = await service.delete_reward(
            reward_id=reward_id,
            group_id_context=group_id,
            actor_id=current_admin.id
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Нагороду не знайдено або не вдалося видалити.")
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка видалення нагороди ID {reward_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post(
    "/{reward_id}/redeem",
    # response_model=RewardRedemptionResponseSchema, # Або просто TransactionSchema/UserAccountSchema
    response_model=AccountTransactionSchema, # Повернемо транзакцію списання бонусів
    tags=["Bonuses", "Rewards"],
    summary="Отримати (купити) нагороду за бонуси"
)
async def redeem_reward(
    group_id: int = Path(..., description="ID групи"),
    reward_id: int = Path(..., description="ID нагороди для отримання"),
    access_check: dict = Depends(group_member_permission), # Учасник групи може купувати
    db_session: DBSession = Depends()
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} намагається отримати нагороду ID {reward_id} в групі {group_id}.")
    service = RewardService(db_session)
    try:
        # Сервіс має перевірити доступність нагороди, баланс користувача,
        # списати бонуси та створити транзакцію, можливо, оновити кількість нагород.
        redemption_result = await service.redeem_reward(
            reward_id=reward_id,
            user_id=current_user.id,
            group_id=group_id
        )
        # redemption_result може бути транзакцією, оновленим балансом, або спеціальною схемою
        return redemption_result
    except HTTPException as e: # Сервіс може кидати помилки (недостатньо коштів, нагорода закінчилась)
        logger.warning(f"Помилка отримання нагороди ID {reward_id} користувачем {current_user.email}: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при отриманні нагороди ID {reward_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при отриманні нагороди.")


# Роутер буде підключений в backend/app/src/api/v1/bonuses/__init__.py
