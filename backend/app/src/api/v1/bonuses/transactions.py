# backend/app/src/api/v1/bonuses/transactions.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для роботи з бонусними транзакціями.

Включає отримання деталей конкретної транзакції та створення ручних транзакцій
(зазвичай для адміністративних цілей, таких як корекція балансу).
Історія транзакцій для користувача доступна через ендпоінти в `accounts.py`.
"""
from typing import Optional  # List, Generic, TypeVar, BaseModel не використовуються
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession  # Не використовується прямо, якщо сесія в сервісі

# Повні шляхи імпорту
from backend.app.src.api.dependencies import get_api_db_session, get_current_active_user, get_current_active_superuser
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.bonuses.transaction import (
    AccountTransactionResponse,
    ManualTransactionRequest  # Схема для створення ручної транзакції
)
from backend.app.src.schemas.bonuses.account import UserAccountResponse  # Для відповіді create_manual_transaction
from backend.app.src.services.bonuses.transaction import AccountTransactionService
from backend.app.src.services.bonuses.account import UserAccountService  # Для валідації рахунку при ручній транзакції
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter()


# Залежність для отримання AccountTransactionService
async def get_account_transaction_service(
        session: AsyncSession = Depends(get_api_db_session)) -> AccountTransactionService:
    """Залежність FastAPI для отримання екземпляра AccountTransactionService."""
    return AccountTransactionService(db_session=session)


# Залежність для UserAccountService (для валідації рахунку)
async def get_user_account_service_dep(session: AsyncSession = Depends(get_api_db_session)) -> UserAccountService:
    return UserAccountService(db_session=session)


# TODO: Створити залежність `require_transaction_viewer(...)`, яка перевіряє,
#  чи має поточний користувач право переглядати цю транзакцію (належить йому, або він адмін/СУ).

@router.get(
    "/{transaction_id}",
    response_model=AccountTransactionResponse,
    summary="Отримання деталей конкретної транзакції",  # i18n
    description="""Повертає детальну інформацію про вказану бонусну транзакцію.
    Доступно користувачу, якому належить транзакція (через зв'язок з рахунком),
    або адміністратору групи/суперюзеру."""  # i18n
    # dependencies=[Depends(require_transaction_viewer)] # TODO
)
async def get_transaction_details(
        transaction_id: UUID = Path(..., description="ID транзакції"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),  # Для перевірки прав
        transaction_service: AccountTransactionService = Depends(get_account_transaction_service)
) -> AccountTransactionResponse:
    """
    Отримує детальну інформацію про бонусну транзакцію.
    Сервіс має перевірити, чи має поточний користувач право бачити цю транзакцію.
    """
    logger.debug(f"Користувач ID '{current_user.id}' запитує деталі транзакції ID '{transaction_id}'.")
    # AccountTransactionService.get_transaction_by_id_for_user має перевіряти права
    # або цей ендпоінт має бути захищений більш специфічною залежністю.
    # TODO: Уточнити логіку прав доступу в сервісі або через залежність.
    transaction = await transaction_service.get_transaction_by_id_for_user(  # Потрібен такий метод
        transaction_id=transaction_id,
        requesting_user_id=current_user.id,
        is_superuser=current_user.is_superuser
    )
    if not transaction:
        logger.warning(
            f"Транзакцію з ID '{transaction_id}' не знайдено або доступ для користувача ID '{current_user.id}' заборонено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Транзакцію не знайдено або доступ заборонено.")
    return transaction


@router.post(
    "/manual",
    response_model=AccountTransactionResponse,  # Повертаємо створену транзакцію
    status_code=status.HTTP_201_CREATED,
    summary="Створення ручної бонусної транзакції (Суперюзер)",  # i18n
    description="""Дозволяє суперюзеру вручну створити бонусну транзакцію
    (наприклад, для корекції балансу, нарахування спеціального бонусу).""",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки для суперюзерів
)
async def create_manual_transaction(
        transaction_in: ManualTransactionRequest,
        # Схема включає user_id, group_id (опціонально), amount, description, type
        current_superuser: UserModel = Depends(get_current_active_superuser),  # Залежність вже перевіряє права
        transaction_service: AccountTransactionService = Depends(get_account_transaction_service),
        account_service: UserAccountService = Depends(get_user_account_service_dep)  # Для валідації існування рахунку
) -> AccountTransactionResponse:
    """
    Створює ручну бонусну транзакцію. Вимагає прав суперкористувача.

    - `user_id`: ID користувача, для чийого рахунку створюється транзакція.
    - `group_id`: ID групи, якщо транзакція стосується групового рахунку (None для глобального).
    - `amount`: Сума балів (може бути позитивною або негативною).
    - `description`: Опис/причина транзакції.
    - `transaction_type`: Тип транзакції (має бути відповідним для ручних операцій, наприклад, 'MANUAL_ADJUSTMENT', 'ADMIN_AWARD').
    """
    logger.info(
        f"Суперюзер ID '{current_superuser.id}' створює ручну транзакцію: {transaction_in.model_dump_minimal()}")

    # Перевірка існування рахунку перед створенням транзакції
    target_user_account = await account_service.get_user_account(
        user_id=transaction_in.user_id,
        group_id=transaction_in.group_id  # group_id може бути None
    )
    if not target_user_account:
        # Якщо рахунок не існує, можливо, його потрібно створити або повернути помилку,
        # залежно від логіки UserAccountService.get_or_create_user_account.
        # Для ручної транзакції, ймовірно, рахунок вже має існувати.
        msg = f"Бонусний рахунок для користувача ID '{transaction_in.user_id}' (група: {transaction_in.group_id or 'глобальний'}) не знайдено."  # i18n
        logger.warning(msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)

    try:
        # AccountTransactionService.create_transaction приймає AccountTransactionCreate,
        # тому потрібно перетворити ManualTransactionRequest.
        # Або створити спеціалізований метод в сервісі.
        # Поки що, припускаємо, що create_transaction може обробити це.
        # TODO: Переконатися, що `transaction_in.transaction_type` є валідним для ручних операцій.
        from backend.app.src.schemas.bonuses.transaction import \
            AccountTransactionCreate  # Локальний імпорт, якщо потрібно

        transaction_create_data = AccountTransactionCreate(
            user_account_id=target_user_account.id,  # ID знайденого/створеного рахунку
            transaction_type=transaction_in.transaction_type or "MANUAL_ADJUSTMENT",  # Тип за замовчуванням
            amount=transaction_in.amount,
            description=transaction_in.description,
            related_entity_id=transaction_in.related_entity_id
        )

        # `create_transaction` повертає кортеж (AccountTransactionResponse, UserAccountResponse)
        new_transaction_resp, _updated_account_resp = await transaction_service.create_transaction(
            transaction_data=transaction_create_data,
            # user_id_for_account_lookup та group_id_for_account_lookup тут не потрібні, бо ми вже маємо user_account_id
            commit_session=True  # Ця операція має бути атомарною
        )
        logger.info(
            f"Ручну транзакцію ID '{new_transaction_resp.id}' успішно створено суперюзером ID '{current_superuser.id}'.")
        return new_transaction_resp
    except ValueError as e:  # Наприклад, InsufficientFundsError з account_service, або інші помилки валідації
        logger.warning(f"Помилка створення ручної транзакції: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні ручної транзакції: {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


# TODO: Розглянути додавання ендпоінта для перегляду списку всіх транзакцій (з пагінацією та фільтрами)
#  для суперкористувачів, якщо це необхідно для адміністрування.
#  GET /?user_id=...&group_id=...&type=...

logger.info(f"Роутер для бонусних транзакцій (`{router.prefix}`) визначено.")
