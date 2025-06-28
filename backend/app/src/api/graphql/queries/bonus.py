# backend/app/src/api/graphql/queries/bonus.py
# -*- coding: utf-8 -*-
"""
GraphQL запити (Queries), пов'язані з бонусами, рахунками та нагородами.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.bonus import UserAccountType, AccountTransactionType, RewardType
from backend.app.src.api.graphql.types.base import Node

# TODO: Імпортувати сервіси
# from backend.app.src.services.bonus.account_service import AccountService
# from backend.app.src.services.bonus.transaction_service import TransactionService
# from backend.app.src.services.bonus.reward_service import RewardService
# from backend.app.src.core.dependencies import get_current_active_user

@strawberry.input
class AccountTransactionsQueryArgs:
    page: Optional[int] = strawberry.field(default=1)
    page_size: Optional[int] = strawberry.field(default=20)
    # TODO: Додати фільтри для транзакцій (тип, дата тощо)

@strawberry.input
class RewardsQueryArgs:
    page: Optional[int] = strawberry.field(default=1)
    page_size: Optional[int] = strawberry.field(default=20)
    group_id: strawberry.ID # Нагороди завжди в контексті групи
    is_active: Optional[bool] = strawberry.field(default=True, description="Показувати тільки активні нагороди.")
    # TODO: Додати фільтри (за вартістю, типом доступності)

@strawberry.type
class BonusQueries:
    """
    Клас, що групує GraphQL запити, пов'язані з бонусною системою.
    """

    @strawberry.field(description="Отримати бонусний рахунок поточного користувача в конкретній групі.")
    async def my_account_in_group(self, info: strawberry.Info, group_id: strawberry.ID) -> Optional[UserAccountType]:
        """
        Повертає інформацію про бонусний рахунок поточного користувача для вказаної групи.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     return None # Або кинути помилку
        #
        # group_db_id = Node.decode_id_to_int(group_id, "GroupType")
        #
        # account_service = AccountService(context.db_session)
        # # Сервіс має перевірити членство користувача в групі
        # account_model = await account_service.get_user_account_in_group(
        #     user_id=current_user.id,
        #     group_id=group_db_id
        # )
        # return UserAccountType.from_orm(account_model) if account_model else None

        # Заглушка
        return None

    @strawberry.field(description="Отримати список транзакцій для рахунку поточного користувача в групі.")
    async def my_account_transactions_in_group(
        self, info: strawberry.Info, group_id: strawberry.ID, args: Optional[AccountTransactionsQueryArgs] = None
    ) -> List[AccountTransactionType]: # TODO: Замінити на Connection
        """
        Повертає історію транзакцій по бонусному рахунку поточного користувача в групі.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     return []
        #
        # group_db_id = Node.decode_id_to_int(group_id, "GroupType")
        # page = args.page if args else 1
        # page_size = args.page_size if args else 20
        # skip = (page - 1) * page_size
        #
        # account_service = AccountService(context.db_session)
        # user_account = await account_service.get_user_account_in_group(user_id=current_user.id, group_id=group_db_id)
        # if not user_account:
        #     return [] # Або помилка, якщо рахунок має існувати
        #
        # transaction_service = TransactionService(context.db_session)
        # transaction_models = await transaction_service.get_transactions_for_account(
        #     account_id=user_account.db_id, # Потрібен db_id з UserAccountType
        #     skip=skip,
        #     limit=page_size
        # )
        # return [AccountTransactionType.from_orm(t) for t in transaction_models.get("transactions", [])]

        # Заглушка
        return []

    @strawberry.field(description="Отримати список доступних нагород у вказаній групі.")
    async def rewards_in_group(self, info: strawberry.Info, args: RewardsQueryArgs) -> List[RewardType]: # TODO: Замінити на Connection
        """
        Повертає список нагород, доступних для отримання в групі.
        Доступно членам групи.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова")
        #
        # group_db_id = Node.decode_id_to_int(args.group_id, "GroupType")
        # page = args.page
        # page_size = args.page_size
        # skip = (page - 1) * page_size
        #
        # reward_service = RewardService(context.db_session)
        # # Сервіс має перевірити членство користувача в групі
        # reward_models = await reward_service.get_rewards_in_group(
        #     group_id=group_db_id,
        #     user_id_for_access_check=current_user.id,
        #     skip=skip,
        #     limit=page_size,
        #     is_active=args.is_active
        # )
        # return [RewardType.from_orm(r) for r in reward_models.get("rewards", [])]

        # Заглушка
        return []

    # TODO: Додати запит для отримання деталей конкретної нагороди.
    # @strawberry.field
    # async def reward_by_id(self, info: strawberry.Info, id: strawberry.ID, group_id: strawberry.ID) -> Optional[RewardType]:
    #     pass

# Експорт класу для агрегації в queries/__init__.py
__all__ = [
    "BonusQueries",
    "AccountTransactionsQueryArgs",
    "RewardsQueryArgs",
]
