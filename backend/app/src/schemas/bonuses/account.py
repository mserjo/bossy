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
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# TODO: Замінити Any на конкретні схеми, коли вони будуть доступні/рефакторені.
# from backend.app.src.schemas.auth.user import UserPublicProfileSchema
# from backend.app.src.schemas.groups.group import GroupSchema # Або GroupBriefSchema
# from .transaction import AccountTransactionSchema # Для історії транзакцій

UserPublicProfileSchema = Any  # Тимчасовий заповнювач
GroupSchema = Any  # Тимчасовий заповнювач
AccountTransactionSchema = Any  # Тимчасовий заповнювач


class UserAccountBaseSchema(BaseSchema):
    """
    Базова схема для полів рахунку користувача.
    """
    user_id: int = Field(description="Ідентифікатор користувача, якому належить рахунок.")
    group_id: int = Field(description="Ідентифікатор групи, в межах якої існує цей рахунок.")
    balance: Decimal = Field(
        default=Decimal("0.00"),
        description="Поточний баланс на рахунку."
    )
    # TODO i18n: default value 'бали'
    currency: str = Field(
        default="бали",
        max_length=50,  # Збільшено з 10 до 50 для гнучкості
        description="Валюта або одиниця виміру бонусів на рахунку (наприклад, 'бали', 'очки')."
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
    balance: Optional[Decimal] = Field(None, description="Нове значення балансу для адміністративного коригування.")
    # Якщо потрібно оновлювати валюту (що малоймовірно для існуючого рахунку):
    # currency: Optional[str] = Field(None, max_length=50, description="Нова валюта рахунку.")


class UserAccountSchema(UserAccountBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про рахунок користувача у відповідях API.
    """
    # id, created_at, updated_at успадковані з міксинів.
    # user_id, group_id, balance, currency успадковані з UserAccountBaseSchema.

    # TODO: Замінити Any на відповідні схеми.
    user: Optional[UserPublicProfileSchema] = Field(None,
                                                    description="Публічний профіль користувача, власника рахунку.")
    group: Optional[GroupSchema] = Field(None, description="Коротка інформація про групу, до якої належить рахунок.")


class UserAccountTransactionHistorySchema(UserAccountSchema):
    """
    Розширена схема для представлення рахунку користувача разом з історією транзакцій.
    """
    # TODO: Замінити Any на AccountTransactionSchema.
    transactions: List[AccountTransactionSchema] = Field(default_factory=list,
                                                         description="Список транзакцій по цьому рахунку.")


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
        # "user": {"id": 1, "name": "Власник Рахунку"}, # Приклад UserPublicProfileSchema
        # "group": {"id": 10, "name": "Група Тестування"}  # Приклад GroupSchema (коротка версія)
    }
    account_response_instance = UserAccountSchema(**account_response_data)
    logger.info(account_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nUserAccountTransactionHistorySchema (приклад відповіді API з транзакціями):")
    history_response_data = {
        **account_response_data,  # Успадковує поля з UserAccountSchema
        "transactions": [  # Приклад AccountTransactionSchema
            {"id": 1001, "transaction_type": "credit", "amount": Decimal("50.00"), "description": "Бонус за завдання",
             "created_at": datetime.now()},  # TODO i18n
            {"id": 1002, "transaction_type": "debit", "amount": Decimal("10.25"), "description": "Покупка нагороди",
             "created_at": datetime.now()}  # TODO i18n
        ]
    }
    history_response_instance = UserAccountTransactionHistorySchema(**history_response_data)
    logger.info(history_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми для пов'язаних об'єктів (UserPublicProfileSchema, GroupSchema, AccountTransactionSchema)")
    logger.info("наразі є заповнювачами (Any). Їх потрібно буде імпортувати після їх рефакторингу/визначення.")
