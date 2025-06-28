# backend/app/src/api/graphql/mutations/bonus.py
# -*- coding: utf-8 -*-
"""
GraphQL мутації (Mutations), пов'язані з бонусами, нагородами та рахунками.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.bonus import (
    RewardType, # Якщо адмін керує нагородами через GraphQL
    AccountTransactionType, # Для відповіді на ручне коригування або подяку
    RedeemRewardInput, ThankYouBonusInput, ManualAdjustmentInput
)
# TODO: Можливо, типи для створення/оновлення RewardDefinitionType, якщо це тут
# from backend.app.src.api.graphql.types.bonus import RewardCreateInput, RewardUpdateInput

from backend.app.src.api.graphql.types.base import Node

# TODO: Імпортувати сервіси
# from backend.app.src.services.bonus.reward_service import RewardService
# from backend.app.src.services.bonus.transaction_service import TransactionService
# from backend.app.src.core.dependencies import get_current_active_user, get_current_group_admin_for_group_id

@strawberry.type
class BonusMutations:
    """
    Клас, що групує GraphQL мутації, пов'язані з бонусною системою.
    """

    @strawberry.mutation(description="Отримати (купити) нагороду за бонуси.")
    async def redeem_reward(self, info: strawberry.Info, input: RedeemRewardInput) -> Optional[AccountTransactionType]: # Або RewardType, або спеціальний Payload
        """
        Дозволяє поточному користувачу "купити" нагороду, обмінявши її на бонуси.
        Повертає інформацію про транзакцію списання бонусів або оновлену нагороду.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова.")
        #
        # reward_db_id = Node.decode_id_to_int(input.reward_id, "RewardType")
        # reward_service = RewardService(context.db_session)
        #
        # # Сервіс має перевірити доступність нагороди, баланс користувача,
        # # списати бонуси, створити транзакцію, оновити кількість нагород (якщо потрібно).
        # # Повертає, наприклад, створену транзакцію.
        # transaction_model = await reward_service.redeem_reward_graphql(
        #     reward_id=reward_db_id,
        #     user_id=current_user.id
        #     # group_id може бути отриманий з reward_model
        # )
        # return AccountTransactionType.from_orm(transaction_model) if transaction_model else None
        raise NotImplementedError("Отримання нагороди ще не реалізовано.")

    @strawberry.mutation(description="Надіслати 'подяку' (бонуси) іншому учаснику групи.")
    async def send_thank_you_bonus(self, info: strawberry.Info, input: ThankYouBonusInput) -> Optional[AccountTransactionType]: # Або дві транзакції, або кастомний payload
        """
        Дозволяє поточному користувачу надіслати бонуси іншому учаснику групи як подяку.
        Повертає транзакцію списання бонусів з відправника.
        """
        # context = info.context
        # sender_user = context.current_user
        # if not sender_user:
        #     raise Exception("Автентифікація обов'язкова.")
        #
        # recipient_db_id = Node.decode_id_to_int(input.recipient_user_id, "UserType")
        # group_db_id = Node.decode_id_to_int(input.group_id, "GroupType")
        #
        # transaction_service = TransactionService(context.db_session)
        # # Сервіс має перевірити, чи відправник та отримувач є членами групи,
        # # чи достатньо коштів у відправника, ліміти тощо.
        # # Створює дві транзакції: списання та нарахування.
        # result_transaction_model = await transaction_service.create_thank_you_transaction_graphql(
        #     group_id=group_db_id,
        #     sender_id=sender_user.id,
        #     recipient_id=recipient_db_id,
        #     amount=input.amount,
        #     message=input.message
        # )
        # return AccountTransactionType.from_orm(result_transaction_model) if result_transaction_model else None # Повертаємо транзакцію списання
        raise NotImplementedError("Надсилання подяки ще не реалізовано.")

    @strawberry.mutation(description="Ручне коригування бонусного балансу користувача (адміністратором групи).")
    async def manual_bonus_adjustment(self, info: strawberry.Info, input: ManualAdjustmentInput) -> Optional[AccountTransactionType]:
        """
        Дозволяє адміністратору групи вручну нарахувати або списати бонуси з рахунку користувача.
        """
        # context = info.context
        # current_admin = context.current_user # Має бути адміном групи input.group_id
        # # Перевірка прав адміністратора для групи input.group_id
        #
        # user_db_id = Node.decode_id_to_int(input.user_id, "UserType")
        # group_db_id = Node.decode_id_to_int(input.group_id, "GroupType")
        #
        # transaction_service = TransactionService(context.db_session)
        # # Сервіс має перевірити, чи користувач належить до групи,
        # # створити транзакцію та оновити баланс.
        # new_transaction_model = await transaction_service.create_manual_adjustment_graphql(
        #     adjustment_data=input, # Адаптувати дані
        #     actor_id=current_admin.id,
        #     group_id=group_db_id, # Для валідації
        #     user_id_to_adjust=user_db_id
        # )
        # return AccountTransactionType.from_orm(new_transaction_model) if new_transaction_model else None
        raise NotImplementedError("Ручне коригування бонусів ще не реалізовано.")

    # TODO: Якщо CRUD операції для RewardDefinition (створення/оновлення/видалення нагород адміном групи)
    # також мають бути доступні через GraphQL, їх потрібно додати сюди.
    # Наприклад:
    # @strawberry.mutation(description="Створити нову нагороду в групі (адмін).")
    # async def create_reward_definition(self, info: strawberry.Info, input: RewardCreateInput) -> Optional[RewardType]:
    #     pass
    #
    # @strawberry.mutation(description="Оновити нагороду в групі (адмін).")
    # async def update_reward_definition(self, info: strawberry.Info, id: strawberry.ID, input: RewardUpdateInput) -> Optional[RewardType]:
    #     pass
    #
    # @strawberry.mutation(description="Видалити нагороду з групи (адмін).")
    # async def delete_reward_definition(self, info: strawberry.Info, id: strawberry.ID) -> bool:
    #     pass


# Експорт класу для агрегації в mutations/__init__.py
__all__ = [
    "BonusMutations",
]
