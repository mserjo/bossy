# backend/app/src/api/v1/bonuses/transactions.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перегляду транзакцій, ручного управління бонусами та системи "подяки" API v1.

Цей модуль надає API для:
- Перегляду історії транзакцій для свого рахунку в групі (поточний користувач).
- Перегляду історії транзакцій для рахунку конкретного користувача в групі (адміністратор групи).
- Ручного нарахування/списання бонусів адміністратором групи.
- Відправки "подяки" (бонусів) іншому учаснику групи.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.bonuses.transaction import (
    AccountTransactionSchema,
    ManualTransactionCreateSchema,
    ThankYouBonusCreateSchema, # Нова схема
    ThankYouBonusResponseSchema # Нова схема
)
from backend.app.src.services.bonuses.transaction_service import TransactionService
from backend.app.src.services.bonuses.account_service import AccountService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission, group_member_permission
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE

logger = get_logger(__name__)

# Роутер для операцій, пов'язаних з переглядом транзакцій конкретних рахунків
# Буде підключений з префіксом /groups/{group_id}/accounts
account_related_transactions_router = APIRouter()

# Роутер для загальних операцій з транзакціями в групі (подяки, можливо ручні коригування)
# Буде підключений з префіксом /groups/{group_id}/transactions
group_transactions_router = APIRouter()


@account_related_transactions_router.get(
    "/me/transactions",
    response_model=List[AccountTransactionSchema],
    tags=["Bonuses", "Account Transactions"],
    summary="Отримати історію своїх транзакцій у групі"
)
async def get_my_transactions_in_group(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
):
    current_user: UserModel = access_check["current_user"]
    logger.info(
        f"Користувач {current_user.email} запитує свою історію транзакцій в групі ID {group_id} "
        f"(сторінка: {page}, розмір: {page_size})."
    )
    transaction_service = TransactionService(db_session)
    account_service = AccountService(db_session)

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
    else:
        transactions = transactions_data
    return transactions

@account_related_transactions_router.get(
    "/{user_id_for_account}/transactions",
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

@group_transactions_router.post(
    "/adjustments", # Шлях буде /groups/{group_id}/transactions/adjustments
    response_model=AccountTransactionSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Bonuses", "Manual Adjustments"],
    summary="Ручне нарахування/списання бонусів (адміністратор групи)"
)
async def manual_bonus_adjustment(
    group_id: int = Path(..., description="ID групи, в якій проводиться операція"),
    adjustment_data: ManualTransactionCreateSchema,
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
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

    target_account = await account_service.get_user_account_in_group(
        user_id=adjustment_data.user_id,
        group_id=group_id
    )
    if not target_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рахунок цільового користувача в цій групі не знайдено.")

    try:
        new_transaction = await transaction_service.create_manual_adjustment(
            adjustment_data=adjustment_data,
            actor_id=current_admin.id,
        )
        logger.info(
            f"Ручне коригування бонусів для користувача ID {adjustment_data.user_id} "
            f"в групі ID {group_id} успішно виконано адміністратором {current_admin.email}."
        )
        return new_transaction
    except HTTPException as e:
        raise e
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"Помилка ручного коригування бонусів: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


@group_transactions_router.post(
    "/thank-you", # Шлях буде /groups/{group_id}/transactions/thank-you
    response_model=ThankYouBonusResponseSchema, # Або список з двох транзакцій
    status_code=status.HTTP_201_CREATED,
    tags=["Bonuses", "Thank You Bonus"],
    summary="Надіслати 'подяку' (бонуси) іншому учаснику групи"
)
async def send_thank_you_bonus(
    group_id: int = Path(..., description="ID групи, в якій відбувається подяка"),
    thank_you_data: ThankYouBonusCreateSchema,
    access_check: dict = Depends(group_member_permission), # Відправник має бути членом групи
    db_session: DBSession = Depends()
):
    """
    Дозволяє поточному користувачу надіслати невелику кількість бонусів
    іншому учаснику групи як "подяку".
    """
    sender_user: UserModel = access_check["current_user"]
    logger.info(
        f"Користувач {sender_user.email} (ID: {sender_user.id}) надсилає подяку "
        f"користувачу ID {thank_you_data.recipient_user_id} в групі ID {group_id} "
        f"на суму {thank_you_data.amount} бонусів."
    )

    if sender_user.id == thank_you_data.recipient_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неможливо надіслати подяку самому собі."
        )

    transaction_service = TransactionService(db_session)
    try:
        # Сервіс має перевірити, чи отримувач є членом групи,
        # чи достатньо коштів у відправника,
        # чи не перевищено ліміти на подяки (якщо є).
        result = await transaction_service.create_thank_you_transaction(
            group_id=group_id,
            sender_id=sender_user.id,
            recipient_id=thank_you_data.recipient_user_id,
            amount=thank_you_data.amount,
            message=thank_you_data.message
        )
        logger.info(
            f"Подяку від {sender_user.email} до користувача ID {thank_you_data.recipient_user_id} "
            f"в групі ID {group_id} успішно оброблено."
        )
        # Повертаємо, наприклад, деталі транзакції або просто успішний статус
        return ThankYouBonusResponseSchema(
            message="Подяку успішно надіслано.",
            sender_transaction_id=result.get("sender_transaction_id"), # Припускаємо, що сервіс повертає ID
            recipient_transaction_id=result.get("recipient_transaction_id")
            )
    except HTTPException as e:
        logger.warning(
            f"Помилка надсилання подяки від {sender_user.email} до {thank_you_data.recipient_user_id} "
            f"в групі {group_id}: {e.detail}"
        )
        raise e
    except ValueError as ve: # Наприклад, недостатньо коштів, отримувач не в групі
        logger.warning(
            f"Помилка значення при надсиланні подяки від {sender_user.email} до {thank_you_data.recipient_user_id} "
            f"в групі {group_id}: {str(ve)}"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при надсиланні подяки: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при надсиланні подяки.")

# Роутери (account_related_transactions_router та group_transactions_router)
# будуть підключені в backend/app/src/api/v1/bonuses/__init__.py
# з відповідними префіксами.
