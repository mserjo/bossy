# backend/app/src/api/v1/bonuses/transactions.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user, get_current_active_superuser
from app.src.models.auth import User as UserModel
# from app.src.models.bonuses import AccountTransaction as AccountTransactionModel # Потрібна модель транзакції
from app.src.schemas.bonuses.transaction import ( # Схеми для транзакцій
    AccountTransactionResponse,
    ManualTransactionRequest
)
from app.src.services.bonuses.transaction import AccountTransactionService # Сервіс для транзакцій

router = APIRouter()

@router.get(
    "/{transaction_id}", # Шлях відносно /bonuses/transactions
    response_model=AccountTransactionResponse,
    summary="Отримання деталей конкретної транзакції",
    description="Повертає детальну інформацію про вказану бонусну транзакцію. Доступ залежить від прав користувача на перегляд рахунку, до якого належить транзакція."
)
async def get_transaction_details(
    transaction_id: int = Path(..., description="ID транзакції"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Для перевірки прав доступу
    transaction_service: AccountTransactionService = Depends()
):
    '''
    Отримує детальну інформацію про бонусну транзакцію.
    Сервіс має перевірити, чи має поточний користувач право бачити цю транзакцію
    (наприклад, чи це його транзакція, або він адмін/суперюзер з доступом до рахунку).
    '''
    if not hasattr(transaction_service, 'db_session') or transaction_service.db_session is None:
        transaction_service.db_session = db

    transaction = await transaction_service.get_transaction_by_id(
        transaction_id=transaction_id,
        requesting_user=current_user
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Транзакція з ID {transaction_id} не знайдена або доступ заборонено."
        )
    return AccountTransactionResponse.model_validate(transaction)

@router.post(
    "/manual",
    response_model=AccountTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення ручної бонусної транзакції (Суперюзер)",
    description="Дозволяє суперюзеру вручну створити бонусну транзакцію (наприклад, для корекції балансу, нарахування спеціального бонусу).",
    dependencies=[Depends(get_current_active_superuser)] # Тільки для суперюзерів
)
async def create_manual_transaction(
    transaction_in: ManualTransactionRequest, # Включає user_id, points, description, type
    db: AsyncSession = Depends(get_db_session),
    current_superuser: UserModel = Depends(get_current_active_superuser), # Залежність вже перевіряє права
    transaction_service: AccountTransactionService = Depends()
):
    '''
    Створює ручну бонусну транзакцію.
    - `user_id`: ID користувача, для якого створюється транзакція.
    - `points`: Кількість балів (може бути позитивною або негативною).
    - `description`: Опис/причина транзакції.
    - `transaction_type`: Тип транзакції (наприклад, 'manual_award', 'correction').
    '''
    if not hasattr(transaction_service, 'db_session') or transaction_service.db_session is None:
        transaction_service.db_session = db

    # `current_superuser` вже передається неявно через `Depends` на рівні ендпоінта
    new_transaction = await transaction_service.create_manual_transaction(
        manual_transaction_schema=transaction_in,
        admin_user=current_superuser # Явно передаємо, хоча можна було б і не передавати, якщо сервіс не потребує
    )
    # Сервіс має кидати HTTPException у разі помилок (наприклад, користувач не знайдений)
    return AccountTransactionResponse.model_validate(new_transaction)

# Міркування:
# 1.  Схеми: `AccountTransactionResponse`, `ManualTransactionRequest` з `app.src.schemas.bonuses.transaction`.
# 2.  Сервіс `AccountTransactionService`: Керує логікою отримання деталей транзакцій та створенням ручних транзакцій.
#     - `get_transaction_by_id`: Перевіряє права доступу користувача до перегляду транзакції.
#     - `create_manual_transaction`: Виконується тільки суперюзером, валідує дані, оновлює баланс користувача.
# 3.  Права доступу:
#     - Перегляд транзакції: залежить від доступу до рахунку.
#     - Створення ручної транзакції: тільки суперюзер.
# 4.  URL-и: Цей роутер буде підключений до `bonuses_router` з префіксом `/transactions`.
#     Шляхи будуть `/api/v1/bonuses/transactions/{transaction_id}` та `/api/v1/bonuses/transactions/manual`.
# 5.  Коментарі: Українською мовою.
