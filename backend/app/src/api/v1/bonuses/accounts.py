# backend/app/src/api/v1/bonuses/accounts.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перегляду рахунків користувачів та їх транзакцій у групах API v1.

Цей модуль надає API для:
- Отримання поточним користувачем свого бонусного рахунку в конкретній групі.
- Отримання адміністратором групи рахунку конкретного користувача в цій групі.
- Отримання адміністратором групи списку всіх рахунків користувачів у цій групі.
- Отримання виписки (списку транзакцій) по рахунку.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.bonuses.account import UserAccountSchema
from backend.app.src.schemas.bonuses.transaction import TransactionSchema # Для виписки
from backend.app.src.services.bonuses.account_service import AccountService
from backend.app.src.services.bonuses.transaction_service import TransactionService # Для виписки
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission, group_member_permission
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти будуть мати префікс /groups/{group_id}/accounts

@router.get(
    "/me",
    response_model=UserAccountSchema,
    tags=["Bonuses", "User Accounts"],
    summary="Отримати свій бонусний рахунок у групі"
)
async def get_my_account_in_group(
    group_id: int = Path(..., description="ID групи"),
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
        logger.warning(f"Рахунок для користувача {current_user.email} в групі {group_id} не знайдено.")
        # Відповідно до ТЗ, рахунок створюється автоматично. Якщо сервіс це не обробляє,
        # то тут може бути логіка створення або повернення помилки, якщо щось пішло не так.
        # Припускаємо, що сервіс поверне рахунок або створить його.
        # Якщо ж сервіс може повернути None, і це означає помилку доступу або неіснування, то 404 доречний.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рахунок не знайдено в цій групі.")
    return account

@router.get(
    "/me/transactions",
    response_model=List[TransactionSchema], # Або схема з пагінацією
    tags=["Bonuses", "User Accounts", "Transactions"],
    summary="Отримати виписку по своєму бонусному рахунку в групі"
)
async def get_my_account_transactions_in_group(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
    # TODO: Додати фільтри для транзакцій (дата, тип тощо)
):
    current_user: UserModel = access_check["current_user"]
    logger.info(
        f"Користувач {current_user.email} запитує виписку по своєму рахунку в групі ID {group_id} "
        f"(сторінка: {page}, розмір: {page_size})."
    )
    account_service = AccountService(db_session) # Потрібен для отримання ID рахунку
    transaction_service = TransactionService(db_session)

    account = await account_service.get_user_account_in_group(user_id=current_user.id, group_id=group_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рахунок не знайдено для отримання транзакцій.")

    transactions_data = await transaction_service.get_transactions_for_account(
        account_id=account.id,
        skip=(page - 1) * page_size,
        limit=page_size
        # TODO: передати фільтри
    )
    if isinstance(transactions_data, dict): # Якщо сервіс повертає пагіновані дані
        transactions = transactions_data.get("transactions", [])
    else:
        transactions = transactions_data
    return transactions


@router.get(
    "/{user_id_for_account}",
    response_model=UserAccountSchema,
    tags=["Bonuses", "User Accounts"],
    summary="Отримати рахунок користувача в групі (адміністратор групи)"
)
async def get_user_account_in_group_by_admin(
    group_id: int = Path(..., description="ID групи"),
    user_id_for_account: int = Path(..., description="ID користувача, чий рахунок запитується"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} запитує рахунок користувача ID {user_id_for_account} "
        f"в групі ID {group_id}."
    )
    account_service = AccountService(db_session)
    account = await account_service.get_user_account_in_group(
        user_id=user_id_for_account,
        group_id=group_id
    )
    if not account:
        logger.warning(f"Рахунок для користувача ID {user_id_for_account} в групі {group_id} не знайдено.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рахунок користувача не знайдено в цій групі.")
    return account

@router.get(
    "/{user_id_for_account}/transactions",
    response_model=List[TransactionSchema], # Або схема з пагінацією
    tags=["Bonuses", "User Accounts", "Transactions"],
    summary="Отримати виписку по рахунку користувача в групі (адміністратор групи)"
)
async def get_user_account_transactions_in_group_by_admin(
    group_id: int = Path(..., description="ID групи"),
    user_id_for_account: int = Path(..., description="ID користувача, чию виписку запитують"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
    # TODO: Додати фільтри для транзакцій
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} запитує виписку по рахунку користувача ID {user_id_for_account} "
        f"в групі ID {group_id} (сторінка: {page}, розмір: {page_size})."
    )
    account_service = AccountService(db_session)
    transaction_service = TransactionService(db_session)

    account = await account_service.get_user_account_in_group(user_id=user_id_for_account, group_id=group_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рахунок користувача не знайдено для отримання транзакцій.")

    transactions_data = await transaction_service.get_transactions_for_account(
        account_id=account.id,
        skip=(page - 1) * page_size,
        limit=page_size
        # TODO: передати фільтри
    )
    if isinstance(transactions_data, dict):
        transactions = transactions_data.get("transactions", [])
    else:
        transactions = transactions_data
    return transactions


@router.get(
    "",
    response_model=List[UserAccountSchema],
    tags=["Bonuses", "User Accounts"],
    summary="Отримати список всіх рахунків у групі (адміністратор групи)"
)
async def list_all_accounts_in_group(
    group_id: int = Path(..., description="ID групи"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
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
    if isinstance(accounts_data, dict):
        accounts = accounts_data.get("accounts", [])
    else:
        accounts = accounts_data
    return accounts
