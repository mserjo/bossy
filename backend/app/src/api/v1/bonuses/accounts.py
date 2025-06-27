# backend/app/src/api/v1/bonuses/accounts.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перегляду рахунків користувачів у групах API v1.

Цей модуль надає API для:
- Отримання поточним користувачем свого бонусного рахунку в конкретній групі.
- Отримання адміністратором групи рахунку конкретного користувача в цій групі.
- Отримання адміністратором групи списку всіх рахунків користувачів у цій групі.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.bonuses.account import UserAccountSchema # Схема для представлення рахунку
from backend.app.src.services.bonuses.account_service import AccountService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission, group_member_permission # Для перевірки прав
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти будуть мати префікс /groups/{group_id}/accounts

@router.get(
    "/me", # Шлях буде /groups/{group_id}/accounts/me
    response_model=UserAccountSchema,
    tags=["Bonuses", "User Accounts"],
    summary="Отримати свій бонусний рахунок у групі"
)
async def get_my_account_in_group(
    group_id: int = Path(..., description="ID групи"),
    # Перевірка, що користувач є учасником групи
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends()
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує свій рахунок в групі ID {group_id}.")
    account_service = AccountService(db_session)

    account = await account_service.get_user_account_in_group(
        user_id=current_user.id,
        group_id=group_id
    )
    if not account:
        # Сервіс може автоматично створювати рахунок при першому запиті або при вступі в групу.
        # Якщо рахунок не знайдено і не створено, це може бути помилкою.
        logger.warning(f"Рахунок для користувача {current_user.email} в групі {group_id} не знайдено.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рахунок не знайдено в цій групі.")
    return account

@router.get(
    "/{user_id_for_account}", # Шлях буде /groups/{group_id}/accounts/{user_id_for_account}
    response_model=UserAccountSchema,
    tags=["Bonuses", "User Accounts"],
    summary="Отримати рахунок користувача в групі (адміністратор групи)"
)
async def get_user_account_in_group_by_admin(
    group_id: int = Path(..., description="ID групи"),
    user_id_for_account: int = Path(..., description="ID користувача, чий рахунок запитується"),
    group_with_admin_rights: dict = Depends(group_admin_permission), # Перевірка прав адміна
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} запитує рахунок користувача ID {user_id_for_account} "
        f"в групі ID {group_id}."
    )
    account_service = AccountService(db_session)

    # Перевірка, чи user_id_for_account є членом групи group_id (можливо, це робить сервіс)
    # Hoặc AccountService.is_user_member_of_group(user_id_for_account, group_id)

    account = await account_service.get_user_account_in_group(
        user_id=user_id_for_account,
        group_id=group_id
    )
    if not account:
        logger.warning(f"Рахунок для користувача ID {user_id_for_account} в групі {group_id} не знайдено.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рахунок користувача не знайдено в цій групі.")
    return account

@router.get(
    "", # Шлях буде /groups/{group_id}/accounts
    response_model=List[UserAccountSchema], # Або схема з пагінацією
    tags=["Bonuses", "User Accounts"],
    summary="Отримати список всіх рахунків у групі (адміністратор групи)"
)
async def list_all_accounts_in_group(
    group_id: int = Path(..., description="ID групи"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
    # TODO: Додати фільтри (наприклад, за балансом, за активністю користувача)
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} запитує список всіх рахунків в групі ID {group_id} "
        f"(сторінка: {page}, розмір: {page_size})."
    )
    account_service = AccountService(db_session)

    accounts_data = await account_service.get_all_accounts_in_group(
        group_id=group_id,
        skip=(page - 1) * page_size,
        limit=page_size
    )
    # Припускаємо, що сервіс повертає {"accounts": [], "total": 0} або просто список
    if isinstance(accounts_data, dict):
        accounts = accounts_data.get("accounts", [])
        # total_accounts = accounts_data.get("total", 0)
        # TODO: Додати заголовки пагінації
    else:
        accounts = accounts_data

    return accounts

# Роутер буде підключений в backend/app/src/api/v1/bonuses/__init__.py
# з префіксом /groups/{group_id}/accounts
