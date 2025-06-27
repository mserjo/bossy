# backend/app/src/api/v1/bonuses/transactions.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перегляду транзакцій та ручного управління бонусами API v1.

Цей модуль надає API для:
- Перегляду історії транзакцій для свого рахунку в групі (поточний користувач).
- Перегляду історії транзакцій для рахунку конкретного користувача в групі (адміністратор групи).
- Можливо, для ручного нарахування/списання бонусів адміністратором групи.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.bonuses.transaction import AccountTransactionSchema, ManualTransactionCreateSchema # Прикладні назви
from backend.app.src.services.bonuses.transaction_service import TransactionService
from backend.app.src.services.bonuses.account_service import AccountService # Для перевірки існування рахунку
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission, group_member_permission
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE

logger = get_logger(__name__)
router = APIRouter()

# Префікси для цих ендпоінтів будуть встановлені в __init__.py модуля bonuses,
# наприклад:
# /groups/{group_id}/accounts/me/transactions
# /groups/{group_id}/accounts/{user_id_for_account}/transactions
# /groups/{group_id}/transactions/manual (якщо окремо)

@router.get(
    "/me/transactions", # Відносно /groups/{group_id}/accounts
    response_model=List[AccountTransactionSchema],
    tags=["Bonuses", "Account Transactions"],
    summary="Отримати історію своїх транзакцій у групі"
)
async def get_my_transactions_in_group(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission), # Перевірка членства в групі
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
    # TODO: Додати фільтри (тип транзакції, період)
):
    current_user: UserModel = access_check["current_user"]
    logger.info(
        f"Користувач {current_user.email} запитує свою історію транзакцій в групі ID {group_id} "
        f"(сторінка: {page}, розмір: {page_size})."
    )
    transaction_service = TransactionService(db_session)
    account_service = AccountService(db_session) # Для отримання account_id

    user_account = await account_service.get_user_account_in_group(user_id=current_user.id, group_id=group_id)
    if not user_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рахунок користувача в цій групі не знайдено.")

    transactions_data = await transaction_service.get_transactions_for_account(
        account_id=user_account.id,
        skip=(page - 1) * page_size,
        limit=page_size
    )
    if isinstance(transactions_data, dict):
        transactions = transactions_data.get("transactions", [])
        # total = transactions_data.get("total", 0) # TODO: Додати заголовки пагінації
    else:
        transactions = transactions_data

    return transactions

@router.get(
    "/{user_id_for_account}/transactions", # Відносно /groups/{group_id}/accounts
    response_model=List[AccountTransactionSchema],
    tags=["Bonuses", "Account Transactions"],
    summary="Отримати історію транзакцій користувача в групі (адміністратор групи)"
)
async def get_user_transactions_in_group_by_admin(
    group_id: int = Path(..., description="ID групи"),
    user_id_for_account: int = Path(..., description="ID користувача, чиї транзакції запитуються"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} запитує історію транзакцій користувача ID {user_id_for_account} "
        f"в групі ID {group_id} (сторінка: {page}, розмір: {page_size})."
    )
    transaction_service = TransactionService(db_session)
    account_service = AccountService(db_session)

    user_account = await account_service.get_user_account_in_group(user_id=user_id_for_account, group_id=group_id)
    if not user_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рахунок вказаного користувача в цій групі не знайдено.")

    transactions_data = await transaction_service.get_transactions_for_account(
        account_id=user_account.id,
        skip=(page - 1) * page_size,
        limit=page_size
    )
    if isinstance(transactions_data, dict):
        transactions = transactions_data.get("transactions", [])
    else:
        transactions = transactions_data

    return transactions

# Окремий ендпоінт для ручних операцій, якщо вони не є частиною стандартних транзакцій
# Може бути розміщений під /groups/{group_id}/transactions/manual
manual_transactions_router = APIRouter()

@manual_transactions_router.post(
    "/manual-adjustment", # Відносно префіксу, що буде заданий для manual_transactions_router
    response_model=AccountTransactionSchema, # Повертає створену транзакцію
    status_code=status.HTTP_201_CREATED,
    tags=["Bonuses", "Manual Adjustments"],
    summary="Ручне нарахування/списання бонусів (адміністратор групи)"
)
async def manual_bonus_adjustment(
    group_id: int = Path(..., description="ID групи, в якій проводиться операція"),
    adjustment_data: ManualTransactionCreateSchema, # Включає user_id, amount, description, type (credit/debit)
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    """
    Дозволяє адміністратору групи вручну нарахувати або списати бонуси з рахунку користувача.
    Потрібно вказати `user_id` користувача, `amount` (додатній для нарахування, від'ємний для списання,
    або окреме поле `type`), та опис операції.
    """
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(
        f"Адміністратор {current_admin.email} виконує ручне коригування бонусів для користувача "
        f"ID {adjustment_data.user_id} в групі ID {group_id}. Сума: {adjustment_data.amount}."
    )

    if adjustment_data.group_id != group_id:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID групи в тілі запиту ({adjustment_data.group_id}) не співпадає з ID групи у шляху ({group_id})."
        )

    transaction_service = TransactionService(db_session)
    account_service = AccountService(db_session)

    # Перевірка, чи існує рахунок користувача
    target_account = await account_service.get_user_account_in_group(
        user_id=adjustment_data.user_id,
        group_id=group_id
    )
    if not target_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рахунок цільового користувача в цій групі не знайдено.")

    try:
        # Сервіс повинен обробити створення транзакції та оновлення балансу рахунку
        new_transaction = await transaction_service.create_manual_adjustment(
            adjustment_data=adjustment_data,
            actor_id=current_admin.id, # ID адміністратора, що виконав дію
            # group_id=group_id # group_id вже є в adjustment_data
        )
        logger.info(
            f"Ручне коригування бонусів для користувача ID {adjustment_data.user_id} "
            f"в групі ID {group_id} успішно виконано адміністратором {current_admin.email}."
        )
        return new_transaction
    except HTTPException as e:
        raise e
    except ValueError as ve: # Наприклад, якщо сума некоректна або недостатньо коштів для списання
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"Помилка ручного коригування бонусів: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

# Роутери будуть підключені в backend/app/src/api/v1/bonuses/__init__.py
