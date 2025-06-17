# backend/app/src/schemas/bonuses/transaction.py
"""
Pydantic схеми для сутності "Транзакція по Рахунку" (AccountTransaction).

Цей модуль визначає схеми для:
- Базового представлення транзакції (`AccountTransactionBaseSchema`).
- Створення нової транзакції (`AccountTransactionCreateSchema`).
- Представлення даних про транзакцію у відповідях API (`AccountTransactionSchema`).
"""
from datetime import datetime
from typing import Optional, Any  # Any для тимчасових полів
from decimal import Decimal

from pydantic import Field, field_validator

# Абсолютний імпорт базових схем та Enum
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.core.dicts import TransactionType  # Enum для типів транзакцій
from backend.app.src.config.logging import get_logger 
logger = get_logger(__name__)

# Імпорт для конкретної схеми
from backend.app.src.schemas.auth.user import UserPublicProfileSchema


# Placeholder assignment removed
# UserPublicProfileSchema = Any


class AccountTransactionBaseSchema(BaseSchema):
    """
    Базова схема для полів транзакції по рахунку.
    """
    account_id: Optional[int] = Field(None, description="Ідентифікатор рахунку користувача. Якщо None, буде визначений через user_id_for_account_lookup.")
    transaction_type: TransactionType = Field(
        description="Тип транзакції."
    )
    amount: Decimal = Field(
        description="Сума транзакції. Для списань може бути від'ємною, або завжди позитивною, а напрямок визначається типом.")
    description: Optional[str] = Field(None, description="Опис або призначення транзакції.",
                                       examples=["Нарахування за завдання 'X'", "Витрата на нагороду 'Y'"])

    related_task_completion_id: Optional[int] = Field(None,
                                                      description="ID пов'язаного виконання завдання (якщо транзакція є результатом завдання).")
    related_reward_id: Optional[int] = Field(None,
                                             description="ID пов'язаної отриманої нагороди (якщо транзакція є покупкою нагороди).")

    # created_by_user_id встановлюється сервісом, не передається клієнтом при створенні звичайної транзакції
    # (може передаватися для ручних адмінських транзакцій)

    # model_config успадковується з BaseSchema (from_attributes=True)

    # Валідатор validate_transaction_type більше не потрібен, Pydantic v2 обробляє Enum автоматично


class AccountTransactionCreateSchema(AccountTransactionBaseSchema):
    """
    Схема для створення нової транзакції по рахунку.
    `account_id` може бути отриманий з контексту або переданий явно.
    `created_by_user_id` зазвичай встановлюється сервісом (поточний користувач для ручних операцій, або системний).
    """
    # Успадковує всі поля від AccountTransactionBaseSchema.
    # Поле created_by_user_id може бути додано сюди, якщо клієнт може його вказувати (наприклад, для адмін. операцій)
    created_by_user_id: Optional[int] = Field(None,
                                              description="ID користувача (адміністратора), який ініціював ручну транзакцію (необов'язково).")


class AccountTransactionResponseSchema(AccountTransactionBaseSchema, IDSchemaMixin, TimestampedSchemaMixin): # Renamed
    """
    Схема для представлення даних про транзакцію у відповідях API.
    `created_at` з TimestampedSchemaMixin позначає час проведення транзакції.
    """
    # id, created_at, updated_at успадковані.
    # transaction_type, amount, description, related_task_completion_id, related_reward_id успадковані.
    account_id: int = Field(description="Ідентифікатор рахунку користувача.") # Перевизначено як non-optional

    created_by_user_id: Optional[int] = Field(None, description="ID користувача, який створив транзакцію (якщо є).")
    created_by: Optional[UserPublicProfileSchema] = Field(None,
                                                          description="Інформація про користувача, який створив транзакцію (якщо є).")

    # Можна додати деталізовані пов'язані об'єкти, якщо потрібно:
    # task_completion: Optional[TaskCompletionSchema] = None # Потребує TaskCompletionSchema
    # reward: Optional[RewardSchema] = None # Потребує RewardSchema


if __name__ == "__main__":
    # Демонстраційний блок для схем транзакцій.
    logger.info("--- Pydantic Схеми для Транзакцій по Рахунку (AccountTransaction) ---")

    logger.info("\nAccountTransactionBaseSchema (приклад):")
    base_tx_data = {
        "account_id": 1,
        "transaction_type": TransactionType.CREDIT.value,
        "amount": Decimal("50.25"),
        "description": "Нарахування за участь у заході."  # TODO i18n
    }
    base_tx_instance = AccountTransactionBaseSchema(**base_tx_data)
    logger.info(base_tx_instance.model_dump_json(indent=2))
    try:
        AccountTransactionBaseSchema(account_id=1, transaction_type="INVALID_TYPE", amount=10)
    except Exception as e:
        logger.info(f"Помилка валідації AccountTransactionBaseSchema (очікувано): {e}")

    logger.info("\nAccountTransactionCreateSchema (приклад для створення):")
    create_tx_data = {
        "account_id": 2,
        "transaction_type": TransactionType.DEBIT.value,
        "amount": Decimal("15.00"),
        "description": "Списання за використання сервісу 'X'.",  # TODO i18n
        "related_reward_id": 5
    }
    create_tx_instance = AccountTransactionCreateSchema(**create_tx_data)
    logger.info(create_tx_instance.model_dump_json(indent=2))

    logger.info("\nAccountTransactionSchema (приклад відповіді API):")
    tx_response_data = {
        "id": 1001,
        "account_id": 1,
        "transaction_type": TransactionType.CREDIT.value,
        "amount": Decimal("75.00"),
        "description": "Щомісячний бонус лояльності.",  # TODO i18n
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "created_by_user_id": 1,
        "created_by": { # Приклад UserPublicProfileSchema
            "id": 1,
            "username": "admin_user",
            "name": "Адміністратор Системи", # TODO i18n
            "avatar_url": "https://example.com/avatars/admin.png"
        }
    }
    tx_response_instance = AccountTransactionResponseSchema(**tx_response_data)
    logger.info(tx_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схема `UserPublicProfileSchema` тепер імпортована та використовується в `AccountTransactionResponseSchema`.")
    logger.info(
        f"Використовується TransactionType Enum для поля 'transaction_type', наприклад: TransactionType.REFUND = '{TransactionType.REFUND.value}'")
