# backend/app/src/api/v1/bonuses/accounts.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user # May need get_current_active_superuser
from app.src.models.auth import User as UserModel
# from app.src.models.bonuses import UserAccount as UserAccountModel # Потрібна модель рахунку
# from app.src.models.bonuses import AccountTransaction as AccountTransactionModel # Потрібна модель транзакції
from app.src.schemas.bonuses.account import UserAccountResponse # Схема для відповіді по рахунку
from app.src.schemas.bonuses.transaction import AccountTransactionResponse # Схема для відповіді по транзакції
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.bonuses.account import UserAccountService # Сервіс для рахунків

router = APIRouter()

@router.get(
    "/me", # Шлях відносно /bonuses/accounts
    response_model=UserAccountResponse,
    summary="Отримання бонусного рахунку поточного користувача",
    description="Повертає деталі бонусного рахунку та поточний баланс для аутентифікованого користувача."
)
async def get_my_bonus_account(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    account_service: UserAccountService = Depends()
):
    '''
    Отримує бонусний рахунок поточного користувача.
    '''
    if not hasattr(account_service, 'db_session') or account_service.db_session is None:
        account_service.db_session = db

    account = await account_service.get_user_account(user_id=current_user.id, requesting_user=current_user)
    if not account: # Рахунок має створюватися автоматично при реєстрації користувача
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бонусний рахунок не знайдено.")
    return UserAccountResponse.model_validate(account)

@router.get(
    "/me/history",
    response_model=PaginatedResponse[AccountTransactionResponse],
    summary="Отримання історії транзакцій поточного користувача",
    description="Повертає історію бонусних транзакцій для аутентифікованого користувача з пагінацією."
)
async def get_my_bonus_account_history(
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    account_service: UserAccountService = Depends()
):
    '''
    Отримує історію транзакцій бонусного рахунку поточного користувача.
    '''
    if not hasattr(account_service, 'db_session') or account_service.db_session is None:
        account_service.db_session = db

    # Сервіс має перевірити, чи існує рахунок перед тим, як запитувати історію
    total_transactions, transactions = await account_service.get_user_account_history(
        user_id=current_user.id,
        requesting_user=current_user,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PaginatedResponse[AccountTransactionResponse]( # Явно вказуємо тип Generic
        total=total_transactions,
        page=page_params.page,
        size=page_params.size,
        results=[AccountTransactionResponse.model_validate(trans) for trans in transactions]
    )

@router.get(
    "/user/{user_id}",
    response_model=UserAccountResponse,
    summary="Отримання бонусного рахунку вказаного користувача (Адмін/Суперюзер)",
    description="Повертає деталі бонусного рахунку вказаного користувача. Доступно адміністраторам груп або суперюзерам."
)
async def get_user_bonus_account(
    user_id: int = Path(..., description="ID користувача, чий рахунок запитується"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    account_service: UserAccountService = Depends()
):
    '''
    Отримує бонусний рахунок вказаного користувача.
    Перевірка прав (чи має `current_user` доступ до інформації `user_id`) - у сервісі.
    '''
    if not hasattr(account_service, 'db_session') or account_service.db_session is None:
        account_service.db_session = db

    account = await account_service.get_user_account(user_id=user_id, requesting_user=current_user)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Бонусний рахунок для користувача ID {user_id} не знайдено або доступ заборонено.")
    return UserAccountResponse.model_validate(account)

@router.get(
    "/user/{user_id}/history",
    response_model=PaginatedResponse[AccountTransactionResponse],
    summary="Отримання історії транзакцій вказаного користувача (Адмін/Суперюзер)",
    description="Повертає історію бонусних транзакцій вказаного користувача. Доступно адміністраторам груп або суперюзерам."
)
async def get_user_bonus_account_history(
    user_id: int = Path(..., description="ID користувача, чию історію транзакцій запитують"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    account_service: UserAccountService = Depends()
):
    '''
    Отримує історію транзакцій бонусного рахунку вказаного користувача.
    Перевірка прав - у сервісі.
    '''
    if not hasattr(account_service, 'db_session') or account_service.db_session is None:
        account_service.db_session = db

    total_transactions, transactions = await account_service.get_user_account_history(
        user_id=user_id,
        requesting_user=current_user,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PaginatedResponse[AccountTransactionResponse]( # Явно вказуємо тип Generic
        total=total_transactions,
        page=page_params.page,
        size=page_params.size,
        results=[AccountTransactionResponse.model_validate(trans) for trans in transactions]
    )

@router.get(
    "/group/{group_id}",
    response_model=PaginatedResponse[UserAccountResponse], # Список рахунків користувачів групи
    summary="Список бонусних рахунків користувачів групи (Адмін/Суперюзер)",
    description="Повертає список бонусних рахунків усіх користувачів у вказаній групі. Доступно адміністраторам цієї групи або суперюзерам."
)
async def list_group_user_accounts(
    group_id: int = Path(..., description="ID групи"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    account_service: UserAccountService = Depends()
):
    '''
    Отримує список бонусних рахунків для всіх користувачів у групі.
    Перевірка прав (чи є `current_user` адміном `group_id` або суперюзером) - у сервісі.
    '''
    if not hasattr(account_service, 'db_session') or account_service.db_session is None:
        account_service.db_session = db

    total_accounts, accounts = await account_service.get_user_accounts_in_group(
        group_id=group_id,
        requesting_user=current_user,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PaginatedResponse[UserAccountResponse]( # Явно вказуємо тип Generic
        total=total_accounts,
        page=page_params.page,
        size=page_params.size,
        results=[UserAccountResponse.model_validate(acc) for acc in accounts]
    )

# Міркування:
# 1.  Схеми: `UserAccountResponse` (з `app.src.schemas.bonuses.account`),
#     `AccountTransactionResponse` (з `app.src.schemas.bonuses.transaction`).
# 2.  Сервіс `UserAccountService`: Керує логікою доступу до рахунків та історії транзакцій.
#     - Забезпечує, що користувачі бачать тільки свою інформацію, а адміни/суперюзери - в межах своїх прав.
#     - Рахунки користувачів мають створюватися автоматично при реєстрації.
# 3.  Права доступу: Чітко розділені для звичайних користувачів (тільки свої дані) та адміністраторів/суперюзерів.
# 4.  Пагінація: Для історії транзакцій та списку рахунків у групі.
# 5.  URL-и: Цей роутер буде підключений до `bonuses_router` з префіксом `/accounts`.
#     Шляхи будуть `/api/v1/bonuses/accounts/me`, `/api/v1/bonuses/accounts/user/{user_id}` тощо.
# 6.  Коментарі: Українською мовою.
