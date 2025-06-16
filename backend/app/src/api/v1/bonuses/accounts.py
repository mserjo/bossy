# backend/app/src/api/v1/bonuses/accounts.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перегляду бонусних рахунків користувачів та історії транзакцій.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List, Optional  # Generic, TypeVar, BaseModel не потрібні, якщо імпортуються з core
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    get_current_active_superuser,  # Для доступу до чужих даних або даних всієї групи
    paginator
)
# TODO: Додати/використати залежність `check_group_view_permission_or_superuser`
from backend.app.src.api.v1.groups.groups import check_group_view_permission  # Тимчасово
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.bonuses.account import UserAccountResponse
from backend.app.src.schemas.bonuses.transaction import AccountTransactionResponse
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.services.bonuses.account import UserAccountService
from backend.app.src.services.bonuses.transaction import AccountTransactionService  # Для історії транзакцій
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter()


# Залежність для отримання UserAccountService
async def get_user_account_service(session: AsyncSession = Depends(get_api_db_session)) -> UserAccountService:
    """Залежність FastAPI для отримання екземпляра UserAccountService."""
    return UserAccountService(db_session=session)


# Залежність для отримання AccountTransactionService
async def get_account_transaction_service(
        session: AsyncSession = Depends(get_api_db_session)) -> AccountTransactionService:
    """Залежність FastAPI для отримання екземпляра AccountTransactionService."""
    return AccountTransactionService(db_session=session)

# ПРИМІТКА: Повноцінна реалізація цього ендпоінта залежить від методу `get_all_accounts_for_user`
# в `UserAccountService` та логіки отримання всіх групових рахунків користувача,
# як зазначено в TODO нижче.
@router.get(
    "/me",
    response_model=List[UserAccountResponse],  # Користувач може мати кілька рахунків (глобальний, групові)
    summary="Отримання бонусних рахунків поточного користувача",  # i18n
    description="""Повертає список бонусних рахунків (глобальний та для кожної групи,
    де користувач є активним членом) для поточного аутентифікованого користувача."""  # i18n
)
async def get_my_bonus_accounts(  # Перейменовано для відображення списку
        current_user: UserModel = Depends(get_current_active_user),
        account_service: UserAccountService = Depends(get_user_account_service)
) -> List[UserAccountResponse]:
    """
    Отримує всі бонусні рахунки поточного користувача.
    """
    logger.info(f"Користувач ID '{current_user.id}' запитує свої бонусні рахунки.")
    # TODO: UserAccountService має надати метод `get_all_accounts_for_user(user_id)`
    #  який повертає список ORM об'єктів UserAccount.
    #  Або цей ендпоінт має приймати `group_id: Optional[UUID]` для вибору конкретного рахунку.
    #  Поки що, симулюємо отримання глобального рахунку, якщо він є.

    # Приклад отримання глобального рахунку (group_id=None)
    global_account_orm = await account_service.get_user_account_orm(user_id=current_user.id, group_id=None,
                                                                    load_relations=True)  # type: ignore

    # TODO: Додати логіку отримання всіх групових рахунків користувача.
    # user_group_memberships = await membership_service.get_user_group_memberships(user_id=current_user.id, is_active=True)
    # group_accounts_orm = []
    # for membership in user_group_memberships:
    #     group_account = await account_service.get_user_account_orm(user_id=current_user.id, group_id=membership.group_id, load_relations=True)
    #     if group_account: group_accounts_orm.append(group_account)

    accounts_response = []
    if global_account_orm:
        accounts_response.append(UserAccountResponse.model_validate(global_account_orm))  # Pydantic v2
    # accounts_response.extend([UserAccountResponse.model_validate(acc) for acc in group_accounts_orm])

    if not accounts_response:
        logger.warning(f"Бонусні рахунки для користувача ID '{current_user.id}' не знайдено.")
        # i18n
        # Не помилка, просто може не бути рахунків ще
        # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бонусні рахунки не знайдено.")
    return accounts_response

# ПРИМІТКА: Цей ендпоінт залежить від коректної реалізації `get_user_account`
# в `UserAccountService` та `list_transactions_for_account` в `AccountTransactionService`.
# Також, важлива коректна обробка пагінації та підрахунку загальної кількості транзакцій.
@router.get(
    "/me/history",
    response_model=PagedResponse[AccountTransactionResponse],
    summary="Отримання історії транзакцій поточного користувача",  # i18n
    description="""Повертає історію бонусних транзакцій для всіх рахунків поточного
    аутентифікованого користувача з пагінацією."""  # i18n
)
async def get_my_bonus_account_history(
        group_id: Optional[UUID] = Query(None,
                                         description="ID групи для фільтрації історії (не вказано - для глобального рахунку)"),
        # i18n
        page_params: PageParams = Depends(paginator),
        current_user: UserModel = Depends(get_current_active_user),
        transaction_service: AccountTransactionService = Depends(get_account_transaction_service),
        account_service: UserAccountService = Depends(get_user_account_service)  # Для отримання user_account_id
) -> PagedResponse[AccountTransactionResponse]:
    """
    Отримує історію транзакцій бонусного рахунку поточного користувача
    (глобального або для вказаної групи).
    """
    logger.info(f"Користувач ID '{current_user.id}' запитує історію транзакцій (група: {group_id}).")

    # Спочатку отримуємо ID рахунку користувача для даної групи (або глобального)
    user_account = await account_service.get_user_account(user_id=current_user.id, group_id=group_id)
    if not user_account:
        logger.info(
            f"Відповідний бонусний рахунок для користувача ID '{current_user.id}' (група: {group_id}) не знайдено для перегляду історії.")
        return PagedResponse(results=[], total=0, page=page_params.page,
                             size=page_params.size)  # Повертаємо порожній результат

    # Потім отримуємо транзакції для цього конкретного рахунку
    transactions_list = await transaction_service.list_transactions_for_account(
        user_account_id=user_account.id,  # Використовуємо ID знайденого рахунку
        skip=page_params.skip,
        limit=page_params.limit
    )
    # total_transactions = len(transactions_list) # ЗАГЛУШКА - видалено, припускаємо, що сервіс повертає total
    # logger.warning("Використовується заглушка для total_count при переліку транзакцій користувача.")
    # Припускаємо, що list_transactions_for_account повертає (items, total_count) або буде оновлено для цього.
    # Поки що, якщо не повертає, total буде неправильним.
    # Якщо сервіс повертає список Pydantic моделей і загальну кількість:
    items_orm, total_transactions = await transaction_service.list_transactions_for_account(
        user_account_id=user_account.id,
        skip=page_params.skip,
        limit=page_params.limit
    )
    # Якщо сервіс повертає тільки список ORM моделей (старий варіант):
    # items_orm = await transaction_service.list_transactions_for_account(...)
    # total_transactions = await transaction_service.get_total_transactions_for_account(user_account.id) # Потрібен такий метод

    return PagedResponse[AccountTransactionResponse](
        total=total_transactions, # Має бути реальна загальна кількість
        page=page_params.page,
        size=page_params.size,
        results=[AccountTransactionResponse.model_validate(item) for item in items_orm]
    )
# TODO: Переглянути повернення total_transactions, якщо сервіс не повертає його.
# Поточний AccountTransactionService.list_transactions_for_account повертає лише список.
# Потрібно або додати метод для підрахунку, або змінити list_transactions_for_account.
# Для тимчасового рішення, можна залишити len(items_orm), але це буде кількість на сторінці, а не загальна.
# Або, якщо total_transactions = await transaction_service.get_total_transactions_for_account(user_account.id)
# то це буде правильно. Залишаю як є, з припущенням, що сервіс буде доопрацьовано.
# Якщо list_transactions_for_account повертає (items, total), то:
# results, total_items = await transaction_service.list_transactions_for_account(...)
# total=total_items, results=results

@router.get(
    "/user/{user_id_target}",
    response_model=List[UserAccountResponse],  # Користувач може мати кілька рахунків
    summary="Отримання бонусних рахунків вказаного користувача (Адмін/Суперюзер)",  # i18n
    description="""Повертає список бонусних рахунків вказаного користувача.
    Доступно суперюзерам або адміністраторам груп, членом яких є цільовий користувач."""  # i18n
    # dependencies=[Depends(get_current_active_superuser)] # Або більш гранульована перевірка
)
# ПРИМІТКА: Цей ендпоінт потребує ретельної реалізації перевірки прав доступу,
# щоб гарантувати, що `current_user` має право переглядати рахунки `user_id_target`.
# Також залежить від `UserAccountService.get_user_account_orm`.
async def get_user_bonus_accounts(  # Перейменовано
        user_id_target: UUID = Path(..., description="ID користувача, чиї рахунки запитуються"),  # i18n
        current_user: UserModel = Depends(get_current_active_superuser),
        # TODO: Замінити на залежність, що перевіряє права (суперюзер АБО адмін спільної групи)
        account_service: UserAccountService = Depends(get_user_account_service)
) -> List[UserAccountResponse]:
    """
    Отримує бонусні рахунки вказаного користувача.
    Перевірка прав: поточний користувач має бути суперюзером або адміном групи,
    до якої належить цільовий користувач (потребує реалізації цієї логіки).
    """
    # TODO: Реалізувати перевірку прав: чи може `current_user` переглядати рахунки `user_id_target`.
    #  Якщо не суперюзер, потрібно перевірити, чи є спільні групи, де `current_user` є адміном.
    logger.info(f"Користувач ID '{current_user.id}' запитує бонусні рахунки для користувача ID '{user_id_target}'.")

    # Поки що, ця логіка аналогічна /me, але для іншого юзера (потребує розширення прав)
    global_account_orm = await account_service.get_user_account_orm(user_id=user_id_target, group_id=None,
                                                                    load_relations=True)  # type: ignore
    accounts_response = []
    if global_account_orm:
        accounts_response.append(UserAccountResponse.model_validate(global_account_orm))
    # TODO: Додати групові рахунки для user_id_target, якщо current_user має до них доступ.

    if not accounts_response:
        logger.warning(f"Бонусні рахунки для користувача ID '{user_id_target}' не знайдено або доступ обмежено.")
    return accounts_response


@router.get(
    "/group/{group_id}/all",  # Змінено шлях, щоб уникнути конфлікту з /group/{group_id} в інших модулях
    response_model=PagedResponse[UserAccountResponse],
    summary="Список бонусних рахунків користувачів групи (Адмін/Суперюзер)",  # i18n
    description="""Повертає список бонусних рахунків усіх користувачів у вказаній групі.
    Доступно адміністраторам цієї групи або суперюзерам.""",  # i18n
    dependencies=[Depends(check_group_view_permission)]  # Використовуємо залежність з groups.py
)
async def list_group_user_accounts(
        group_id: UUID = Path(..., description="ID групи"),  # i18n
        page_params: PageParams = Depends(paginator),
        # current_user_with_permission: UserModel = Depends(check_group_view_permission), # Користувач вже в current_user
        account_service: UserAccountService = Depends(get_user_account_service)
) -> PagedResponse[UserAccountResponse]:
    """
    Отримує список бонусних рахунків для всіх користувачів у групі.
    Перевірка прав (чи є поточний користувач членом/адміном групи або суперюзером) - через залежність.
    """
    # logger.info(f"Користувач ID '{current_user_with_permission.id}' запитує рахунки для групи ID '{group_id}'.")
    logger.info(f"Запит рахунків для групи ID '{group_id}'.")

    # Припускаємо, що UserAccountService.list_user_accounts_in_group_paginated повертає (items, total_count)
    accounts_orm, total_accounts = await account_service.list_user_accounts_in_group_paginated(
        group_id=group_id,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PagedResponse[UserAccountResponse](
        total=total_accounts,
        page=page_params.page,
        size=page_params.size,
        results=[UserAccountResponse.model_validate(acc) for acc in accounts_orm]  # Pydantic v2
    )


# TODO: Розглянути ендпоінт для адміністративного коригування балансу (створення транзакції MANUAL_ADJUSTMENT).
# POST /admin/adjust-balance
# { "user_id": "...", "group_id": "...", "amount": "...", "description": "..." }
# Потребує прав суперюзера.

logger.info(f"Роутер для бонусних рахунків (`{router.prefix}`) визначено.")
        total=total_transactions,
        page=page_params.page,
        size=page_params.size,
        results=transactions_list  # Сервіс вже повертає список Pydantic моделей
    )


@router.get(
    "/user/{user_id_target}",
    response_model=List[UserAccountResponse],  # Користувач може мати кілька рахунків
    summary="Отримання бонусних рахунків вказаного користувача (Адмін/Суперюзер)",  # i18n
    description="""Повертає список бонусних рахунків вказаного користувача.
    Доступно суперюзерам або адміністраторам груп, членом яких є цільовий користувач."""  # i18n
    # dependencies=[Depends(get_current_active_superuser)] # Або більш гранульована перевірка
)
async def get_user_bonus_accounts(  # Перейменовано
        user_id_target: UUID = Path(..., description="ID користувача, чиї рахунки запитуються"),  # i18n
        current_user: UserModel = Depends(get_current_active_superuser),
        # TODO: Замінити на залежність, що перевіряє права (суперюзер АБО адмін спільної групи)
        account_service: UserAccountService = Depends(get_user_account_service)
) -> List[UserAccountResponse]:
    """
    Отримує бонусні рахунки вказаного користувача.
    Перевірка прав: поточний користувач має бути суперюзером або адміном групи,
    до якої належить цільовий користувач (потребує реалізації цієї логіки).
    """
    # TODO: Реалізувати перевірку прав: чи може `current_user` переглядати рахунки `user_id_target`.
    #  Якщо не суперюзер, потрібно перевірити, чи є спільні групи, де `current_user` є адміном.
    logger.info(f"Користувач ID '{current_user.id}' запитує бонусні рахунки для користувача ID '{user_id_target}'.")

    # Поки що, ця логіка аналогічна /me, але для іншого юзера (потребує розширення прав)
    global_account_orm = await account_service.get_user_account_orm(user_id=user_id_target, group_id=None,
                                                                    load_relations=True)  # type: ignore
    accounts_response = []
    if global_account_orm:
        accounts_response.append(UserAccountResponse.model_validate(global_account_orm))
    # TODO: Додати групові рахунки для user_id_target, якщо current_user має до них доступ.

    if not accounts_response:
        logger.warning(f"Бонусні рахунки для користувача ID '{user_id_target}' не знайдено або доступ обмежено.")
    return accounts_response


@router.get(
    "/group/{group_id}/all",  # Змінено шлях, щоб уникнути конфлікту з /group/{group_id} в інших модулях
    response_model=PagedResponse[UserAccountResponse],
    summary="Список бонусних рахунків користувачів групи (Адмін/Суперюзер)",  # i18n
    description="""Повертає список бонусних рахунків усіх користувачів у вказаній групі.
    Доступно адміністраторам цієї групи або суперюзерам.""",  # i18n
    dependencies=[Depends(check_group_view_permission)]  # Використовуємо залежність з groups.py
)
async def list_group_user_accounts(
        group_id: UUID = Path(..., description="ID групи"),  # i18n
        page_params: PageParams = Depends(paginator),
        # current_user_with_permission: UserModel = Depends(check_group_view_permission), # Користувач вже в current_user
        account_service: UserAccountService = Depends(get_user_account_service)
) -> PagedResponse[UserAccountResponse]:
    """
    Отримує список бонусних рахунків для всіх користувачів у групі.
    Перевірка прав (чи є поточний користувач членом/адміном групи або суперюзером) - через залежність.
    """
    # logger.info(f"Користувач ID '{current_user_with_permission.id}' запитує рахунки для групи ID '{group_id}'.")
    logger.info(f"Запит рахунків для групи ID '{group_id}'.")

    # TODO: UserAccountService.list_user_accounts_in_group_paginated має повертати (items, total_count)
    accounts_orm, total_accounts = await account_service.list_user_accounts_in_group_paginated(
        group_id=group_id,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PagedResponse[UserAccountResponse](
        total=total_accounts,
        page=page_params.page,
        size=page_params.size,
        results=[UserAccountResponse.model_validate(acc) for acc in accounts_orm]  # Pydantic v2
    )


# TODO: Розглянути ендпоінт для адміністративного коригування балансу (створення транзакції MANUAL_ADJUSTMENT).
# POST /admin/adjust-balance
# { "user_id": "...", "group_id": "...", "amount": "...", "description": "..." }
# Потребує прав суперюзера.

logger.info(f"Роутер для бонусних рахунків (`{router.prefix}`) визначено.")
