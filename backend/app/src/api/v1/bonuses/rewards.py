# backend/app/src/api/v1/bonuses/rewards.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління визначеннями Нагород та їх отримання користувачами.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List, Optional  # Generic, TypeVar, BaseModel не потрібні, якщо імпортуються з core
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    get_current_active_superuser,  # Для CRUD операцій над визначеннями нагород
    paginator
)
# TODO: Створити/використати залежності для перевірки прав, наприклад:
#  `require_reward_editor_permission(reward_id: UUID = Path(...))` (перевіряє адміна групи нагороди або суперюзера)
#  `require_reward_viewer_permission(reward_id: UUID = Path(...))` (перевіряє членство в групі нагороди або суперюзера)
from backend.app.src.api.v1.groups.groups import \
    check_group_edit_permission  # Тимчасово, для створення/оновлення в групі

from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.bonuses.reward import (
    RewardCreate, RewardUpdate, RewardResponse,
    RedeemRewardRequest, UserRewardRedemptionResponse  # Додано UserRewardRedemptionResponse
)
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.services.bonuses.reward import RewardService
from backend.app.src.services.groups.group import GroupService  # Для перевірки групи при створенні
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter()


# Залежність для отримання RewardService
async def get_reward_service(session: AsyncSession = Depends(get_api_db_session)) -> RewardService:
    """Залежність FastAPI для отримання екземпляра RewardService."""
    return RewardService(db_session=session)


# Залежність для GroupService (для перевірки існування групи при створенні нагороди для групи)
async def get_group_service_dep(session: AsyncSession = Depends(get_api_db_session)) -> GroupService:
    return GroupService(db_session=session)

# ПРИМІТКА: Логіка перевірки прав доступу для створення нагороди (адміністратор групи
# або суперюзер) потребує завершення, зокрема через реалізацію методу
# `is_user_group_admin` в `GroupService` або використання спеціалізованих залежностей.
@router.post(
    "/",
    response_model=RewardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нової нагороди (Адмін/Суперюзер)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру створити нову нагороду."  # i18n
)
async def create_reward(
        reward_in: RewardCreate,  # Схема містить group_id (опціонально)
        current_user: UserModel = Depends(get_current_active_user),  # Поточний користувач для перевірки прав
        reward_service: RewardService = Depends(get_reward_service),
        group_service: GroupService = Depends(get_group_service_dep)  # Для перевірки прав на групу
):
    """
    Створює нову нагороду.
    Якщо `reward_in.group_id` вказано, користувач має бути адміном цієї групи або суперюзером.
    Якщо `reward_in.group_id` не вказано (глобальна нагорода), тільки суперюзер може її створити.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' намагається створити нагороду '{reward_in.name}'. Група: {reward_in.group_id or 'Глобальна'}.")

    # Перевірка прав
    if reward_in.group_id:
        # TODO: Використати більш гранульовану залежність check_group_edit_permission(group_id=reward_in.group_id)
        # Наразі, імітуємо перевірку тут, якщо є простий доступ.
        if not current_user.is_superuser:
            # Ця перевірка має бути частиною залежності або більш складного механізму прав
            is_admin = await group_service.is_user_group_admin(user_id=current_user.id,
                                                               group_id=reward_in.group_id)  # Потрібен такий метод в GroupService
            if not is_admin:
                # i18n
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Ви не є адміністратором вказаної групи для створення нагороди.")
    elif not current_user.is_superuser:  # Глобальну нагороду може створити тільки суперюзер
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Тільки суперкористувачі можуть створювати глобальні нагороди.")

    try:
        created_reward = await reward_service.create_reward(
            reward_data=reward_in,
            creator_user_id=current_user.id
        )
        return created_reward
    except ValueError as e:
        logger.warning(f"Помилка створення нагороди '{reward_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні нагороди '{reward_in.name}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/",
    response_model=PagedResponse[RewardResponse],
    summary="Отримання списку доступних нагород",  # i18n
    description="""Повертає список нагород, доступних для придбання.
    Фільтрується за групою (`group_id`). Якщо група не вказана, показує глобальні нагороди
    та нагороди для груп, членом яких є користувач (TODO: уточнити цю логіку)."""  # i18n
)
async def read_available_rewards(
        group_id: Optional[UUID] = Query(None,
                                         description="ID групи для фільтрації нагород (показує нагороди цієї групи та глобальні)"),
        # i18n
        page_params: PageParams = Depends(paginator),
        current_user: UserModel = Depends(get_current_active_user),  # Для визначення доступних нагород
        reward_service: RewardService = Depends(get_reward_service)
) -> PagedResponse[RewardResponse]:
    """
    Отримує список доступних нагород.
    Доступність може залежати від групи користувача та налаштувань нагороди.
    """
    logger.debug(
        f"Користувач ID '{current_user.id}' запитує список нагород. Група: {group_id}, сторінка: {page_params.page}.")
    # TODO: RewardService.list_available_rewards_paginated має враховувати членство користувача в групах,
    #  якщо group_id не вказано, для показу "моїх" групових нагород + глобальних.
    #  Також має повертати (items, total_count).
    rewards_orm, total_rewards = await reward_service.list_available_rewards_paginated(
        requesting_user_id=current_user.id,
        group_id_filter=group_id,  # Якщо None, сервіс має повернути глобальні + доступні групові
        skip=page_params.skip,
        limit=page_params.limit,
        is_active_filter=True  # За замовчуванням тільки активні нагороди
    )
    return PagedResponse[RewardResponse](
        total=total_rewards,
        page=page_params.page,
        size=page_params.size,
        results=[RewardResponse.model_validate(r) for r in rewards_orm]  # Pydantic v2
    )

# ПРИМІТКА: Цей ендпоінт залежить від реалізації методу `list_available_rewards_paginated`
# в `RewardService`, який має коректно фільтрувати нагороди за доступністю
# для поточного користувача та групи. TODO щодо прав доступу також актуальний.
# TODO: Створити залежність `check_reward_access_permission(reward_id: UUID, current_user: UserModel, ...)`
#  яка перевіряє, чи може користувач бачити/редагувати цю нагороду (глобальна, або з його групи, або він адмін/СУ)

# ПРИМІТКА: Доступ до конкретної нагороди має перевірятися. Поточна реалізація
# покладається на метод `get_reward_by_id_for_user` в `RewardService`, який має
# інкапсулювати цю логіку перевірки прав.
@router.get(
    "/{reward_id}",
    response_model=RewardResponse,
    summary="Отримання інформації про нагороду за ID",  # i18n
    description="Повертає детальну інформацію про конкретну нагороду. Доступно, якщо нагорода глобальна або користувач є членом групи нагороди."
    # i18n
    # dependencies=[Depends(check_reward_access_permission)] # TODO
)
async def read_reward_by_id(
        reward_id: UUID,
        current_user: UserModel = Depends(get_current_active_user),  # Для перевірки доступу
        reward_service: RewardService = Depends(get_reward_service)
) -> RewardResponse:
    """
    Отримує інформацію про нагороду за її ID.
    Сервіс має перевіряти доступність нагороди для користувача.
    """
    logger.debug(f"Користувач ID '{current_user.id}' запитує нагороду ID '{reward_id}'.")
    # RewardService.get_reward_by_id має враховувати права доступу або group_id нагороди
    reward = await reward_service.get_reward_by_id_for_user(  # Потрібен такий метод в сервісі
        reward_id=reward_id,
        requesting_user_id=current_user.id
    )
    if not reward:
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Нагороду з ID {reward_id} не знайдено або доступ заборонено.")
    return reward

# ПРИМІТКА: Оновлення нагороди потребує ретельної перевірки прав (адміністратор групи
# нагороди або суперюзер). Ця логіка має бути реалізована або в сервісі,
# або через спеціалізовану залежність (див. TODO).
@router.put(
    "/{reward_id}",
    response_model=RewardResponse,
    summary="Оновлення інформації про нагороду (Адмін/Суперюзер)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру оновити існуючу нагороду.",  # i18n
    # dependencies=[Depends(check_reward_editor_permission)] # TODO
)
async def update_reward(
        reward_id: UUID,
        reward_in: RewardUpdate,
        current_user: UserModel = Depends(get_current_active_superuser),  # Тимчасово, потрібна гранульована перевірка
        reward_service: RewardService = Depends(get_reward_service)
) -> RewardResponse:
    """Оновлює дані нагороди. Перевірка прав (адмін групи нагороди / суперюзер) в сервісі або залежності."""
    logger.info(f"Користувач ID '{current_user.id}' намагається оновити нагороду ID '{reward_id}'.")
    try:
        updated_reward = await reward_service.update_reward(
            reward_id=reward_id,
            reward_data=reward_in,  # Змінено з reward_update_schema
            updater_user_id=current_user.id
        )
        if not updated_reward:  # Сервіс може повернути None, якщо не знайдено
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Нагороду не знайдено для оновлення.")
        return updated_reward
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка: {e}", exc_info=global_settings.DEBUG)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера.")  # i18n


@router.delete(
    "/{reward_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення нагороди (Адмін/Суперюзер)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру видалити нагороду.",  # i18n
    # dependencies=[Depends(check_reward_editor_permission)] # TODO
)
async def delete_reward(
        reward_id: UUID,
        current_user: UserModel = Depends(get_current_active_superuser),  # Тимчасово
        reward_service: RewardService = Depends(get_reward_service)
):
    """Видаляє нагороду. Перевірка прав в сервісі або залежності."""
    logger.info(f"Користувач ID '{current_user.id}' намагається видалити нагороду ID '{reward_id}'.")
    try:
        success = await reward_service.delete_reward(
            reward_id=reward_id,
            deleter_user_id=current_user.id
        )
        if not success:
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Не вдалося видалити нагороду. Можливо, її не існує.")
    except ValueError as e:  # Наприклад, якщо нагорода використовується
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n

    return None

# ПРИМІТКА: Видалення нагороди також потребує ретельної перевірки прав,
# аналогічно до оновлення.
# ПРИМІТКА: Отримання нагороди користувачем (`redeem_reward_endpoint`) є ключовою функцією.
# Вона залежить від коректної реалізації `redeem_reward` в `RewardService`,
# що включає перевірку балансу, доступності нагороди, списання балів та оновлення запасів.
# Важливим є визначення `group_id_context`.
@router.post(
    "/{reward_id}/redeem",
    response_model=UserRewardRedemptionResponse,  # Повертаємо запис про отримання нагороди
    summary="Придбання нагороди користувачем",  # i18n
    description="Дозволяє поточному користувачу придбати (отримати) нагороду за бонусні бали."  # i18n
)
async def redeem_reward_endpoint(  # Перейменовано
        reward_id: UUID = Path(..., description="ID нагороди, яку користувач хоче придбати"),  # i18n
        redeem_request: RedeemRewardRequest,  # Може містити кількість, якщо нагорода дозволяє >1
        current_user: UserModel = Depends(get_current_active_user),
        reward_service: RewardService = Depends(get_reward_service)
) -> UserRewardRedemptionResponse:
    """
    Поточний користувач придбає нагороду.
    Сервіс перевіряє доступність нагороди, наявність балів, списує бали, оновлює запаси.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' намагається отримати нагороду ID '{reward_id}'. Кількість: {redeem_request.quantity}")
    try:
        # RewardService.redeem_reward має приймати group_id_context, якщо рахунки користувача розділені по групах
        # TODO: Визначити, звідки брати group_id_context (можливо, з профілю користувача або активної групи)
        #  або якщо нагорода глобальна, то group_id_context = None
        reward_orm = await reward_service.get_reward_orm_by_id(reward_id)  # Потрібен ORM для group_id
        if not reward_orm:
            raise ValueError("Нагорода не знайдена.")  # i18n

        redemption_record = await reward_service.redeem_reward(
            user_id=current_user.id,
            reward_id=reward_id,
            redeem_data=redeem_request,
            group_id_context=reward_orm.group_id  # Контекст групи беремо з самої нагороди
        )
        return redemption_record  # Сервіс вже повертає UserRewardRedemptionResponse
    except ValueError as e:  # Наприклад, недостатньо балів, немає в наявності, не для цієї групи
        logger.warning(f"Помилка отримання нагороди ID '{reward_id}' користувачем ID '{current_user.id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:  # Якщо є додаткові перевірки прав у сервісі
        logger.warning(f"Заборона отримання нагороди ID '{reward_id}' користувачем ID '{current_user.id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при отриманні нагороди ID '{reward_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


logger.info(f"Роутер для нагород (`{router.prefix}`) визначено.")
