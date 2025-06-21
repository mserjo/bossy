# backend/app/src/schemas/bonuses/account.py
"""
Pydantic схеми для сутності "Рахунок Користувача" (UserAccount).

Цей модуль визначає схеми для:
- Базового представлення рахунку користувача (`UserAccountBaseSchema`).
- Створення нового рахунку (зазвичай виконується сервісом) (`UserAccountCreateSchema`).
- Оновлення балансу рахунку (для адміністративних коригувань) (`UserAccountUpdateSchema`).
- Представлення даних про рахунок у відповідях API (`UserAccountSchema`).
- Представлення рахунку разом з історією транзакцій (`UserAccountTransactionHistorySchema`).
"""
from datetime import datetime
from typing import Optional, List, Any  # Any для тимчасових полів
from decimal import Decimal

from pydantic import Field

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _
logger = get_logger(__name__)

# Імпорти для конкретних схем
from backend.app.src.schemas.auth.user import UserPublicProfileSchema
from backend.app.src.schemas.groups.group import GroupSchema
from .transaction import AccountTransactionResponseSchema # Відносний імпорт


# Placeholder assignments removed
# UserPublicProfileSchema = Any
# GroupSchema = Any
# AccountTransactionSchema = Any


class UserAccountBaseSchema(BaseSchema):
    """
    Базова схема для полів рахунку користувача.
    """
    user_id: int = Field(description=_("account.fields.user_id.description"))
    group_id: int = Field(description=_("account.fields.group_id.description"))
    balance: Decimal = Field(
        default=Decimal("0.00"),
        description=_("account.fields.balance.description")
    )
    currency: str = Field(
        default="бали", # Default value itself is not translated by `_` here
        max_length=10,
        description=_("account.fields.currency.description")
    )
    # model_config успадковується з BaseSchema (from_attributes=True)


class UserAccountCreateSchema(UserAccountBaseSchema):
    """
    Схема для створення нового рахунку користувача.
    Зазвичай рахунки створюються автоматично сервісом при додаванні користувача до групи
    або при першій бонусній операції.
    """
    # Успадковує user_id, group_id, balance (з default=0), currency (з default='бали').
    # Можна додати поля, специфічні для створення, якщо такі є.
    pass


class UserAccountUpdateSchema(BaseSchema):
    """
    Схема для оновлення балансу рахунку (наприклад, для адміністративних коригувань).
    Дозволяє оновлювати лише баланс. Інші поля (user_id, group_id, currency) зазвичай незмінні.
    """
    balance: Optional[Decimal] = Field(None, description=_("account.update.fields.balance.description"))
    # Якщо потрібно оновлювати валюту (що малоймовірно для існуючого рахунку):
    # currency: Optional[str] = Field(None, max_length=50, description="Нова валюта рахунку.")


class UserAccountResponseSchema(UserAccountBaseSchema, IDSchemaMixin, TimestampedSchemaMixin): # Renamed
    """
    Схема для представлення даних про рахунок користувача у відповідях API.
    """
    # id, created_at, updated_at успадковані з міксинів.
    # user_id, group_id, balance, currency успадковані з UserAccountBaseSchema.

    user: Optional[UserPublicProfileSchema] = Field(None,
                                                    description=_("account.response.fields.user.description"))
    group: Optional[GroupSchema] = Field(None, description=_("account.response.fields.group.description"))


class UserAccountTransactionHistorySchema(UserAccountResponseSchema):
    """
    Розширена схема для представлення рахунку користувача разом з історією транзакцій.
    """
    transactions: List[AccountTransactionResponseSchema] = Field(default_factory=list,
                                                                  description=_("account.history_response.fields.transactions.description"))


if __name__ == "__main__":
    # Демонстраційний блок для схем рахунків користувачів.
    logger.info("--- Pydantic Схеми для Рахунків Користувачів (UserAccount) ---")

    logger.info("\nUserAccountBaseSchema (приклад):")
    base_account_data = {
        "user_id": 1,
        "group_id": 10,
        "balance": Decimal("125.50"),
        "currency": "кредити"  # TODO i18n
    }
    base_account_instance = UserAccountBaseSchema(**base_account_data)
    logger.info(base_account_instance.model_dump_json(indent=2))

    logger.info("\nUserAccountCreateSchema (приклад для створення):")
    create_account_data = {
        "user_id": 2,
        "group_id": 10
        # balance та currency візьмуться за замовчуванням
    }
    create_account_instance = UserAccountCreateSchema(**create_account_data)
    logger.info(create_account_instance.model_dump_json(indent=2))

    logger.info("\nUserAccountUpdateSchema (приклад для оновлення балансу):")
    update_account_data = {"balance": Decimal("200.00")}
    update_account_instance = UserAccountUpdateSchema(**update_account_data)
    logger.info(update_account_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nUserAccountSchema (приклад відповіді API):")
    account_response_data = {
        "id": 1,
        "user_id": 1,
        "group_id": 10,
        "balance": Decimal("150.75"),
        "currency": "бали",  # TODO i18n
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        # Приклади для пов'язаних об'єктів (закоментовано, бо потребують повних даних схем)
        # "user": {"id": 1, "username": "owner", "name": "Власник Рахунку"},
        # "group": {"id": 10, "name": "Група Тестування", "group_type_code": "TEAM",
        #           "created_at": str(datetime.now()), "updated_at": str(datetime.now())}
    }
    account_response_instance = UserAccountResponseSchema(**account_response_data)
    logger.info(account_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nUserAccountTransactionHistorySchema (приклад відповіді API з транзакціями):")
    # Приклад даних для транзакцій (потребує відповідності до AccountTransactionResponseSchema)
    example_transaction_1 = {
        "id": 1001, "account_id": 1, "transaction_type_code": "CREDIT", "amount": Decimal("50.00"),
        "description": "Бонус за завдання", "bonus_rule_id": 5, "created_at": datetime.now(), "updated_at": datetime.now()
        # "transaction_type": {"id":1, "code": "CREDIT", "name": "Credit"}, # Приклад якщо transaction_type є об'єктом
        # "bonus_rule": {"id":5, "name":"Rule Name"} # Приклад якщо bonus_rule є об'єктом
    }
    example_transaction_2 = {
        "id": 1002, "account_id": 1, "transaction_type_code": "DEBIT", "amount": Decimal("10.25"),
        "description": "Покупка нагороди", "created_at": datetime.now(), "updated_at": datetime.now()
    }

    history_response_data = {
        **account_response_data,
        "transactions": [example_transaction_1, example_transaction_2]
    }
    history_response_instance = UserAccountTransactionHistorySchema(**history_response_data)
    logger.info(history_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми для пов'язаних об'єктів тепер імпортовані.")
    logger.info("Приклади даних для цих полів у `account_response_data` та `history_response_data` можуть потребувати коригування")
    logger.info("для повної відповідності структурам `UserPublicProfileSchema`, `GroupSchema`, та `AccountTransactionResponseSchema`.")
