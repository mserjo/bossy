# backend/app/src/repositories/bonuses/account_transaction_repository.py
"""
Репозиторій для моделі "Транзакція по Рахунку" (AccountTransaction).

Цей модуль визначає клас `AccountTransactionRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з транзакціями по рахунках користувачів.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.bonuses.transaction import AccountTransaction
from backend.app.src.schemas.bonuses.transaction import AccountTransactionCreateSchema
from backend.app.src.core.dicts import TransactionType # Імпорт TransactionType Enum
# AccountTransactionUpdateSchema зазвичай не потрібна, транзакції незмінні
from pydantic import BaseModel as PydanticBaseModel  # Для "заглушки" UpdateSchema
from backend.app.src.config.logging import get_logger # Стандартизований імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Транзакції зазвичай не оновлюються, а створюються нові (наприклад, коригуюча транзакція).
# Тому UpdateSchema може бути простою заглушкою.
class AccountTransactionUpdateSchema(PydanticBaseModel):
    pass


class AccountTransactionRepository(
    BaseRepository[AccountTransaction, AccountTransactionCreateSchema, AccountTransactionUpdateSchema]):
    """
    Репозиторій для управління транзакціями по рахунках (`AccountTransaction`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    методи для отримання транзакцій для конкретного рахунку або за типом.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `AccountTransaction`.
        """
        super().__init__(model=AccountTransaction)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_transactions_for_account(
            self,
            session: AsyncSession,
            account_id: int,
            skip: int = 0,
            limit: int = 100,
            order_by_desc_created_at: bool = True
    ) -> Tuple[List[AccountTransaction], int]:
        """
        Отримує список транзакцій для вказаного рахунку з пагінацією та сортуванням.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            account_id (int): ID рахунку користувача.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.
            order_by_desc_created_at (bool): Якщо True, сортує транзакції за спаданням дати створення (новіші перші).

        Returns:
            Tuple[List[AccountTransaction], int]: Кортеж зі списком транзакцій та їх загальною кількістю.
        """
        logger.debug(f"Отримання транзакцій для рахунку ID: {account_id}, skip: {skip}, limit: {limit}")
        filters_dict = {"account_id": account_id}
        sort_by_field = "created_at"
        sort_order_str = "desc" if order_by_desc_created_at else "asc"

        try:
            # Приклад жадібного завантаження не використовується тут, але залишений як коментар у BaseRepository
            # Якщо потрібно, його можна передати в get_multi як параметр options.
            items = await super().get_multi(
                session=session,
                skip=skip,
                limit=limit,
                filters=filters_dict,
                sort_by=sort_by_field,
                sort_order=sort_order_str
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} транзакцій для рахунку ID: {account_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні транзакцій для рахунку {account_id}: {e}", exc_info=True)
            return [], 0


    async def get_transactions_by_type(
            self,
            session: AsyncSession,
            account_id: int,
            transaction_type: TransactionType,  # Змінено на TransactionType Enum
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[AccountTransaction], int]:
        """
        Отримує список транзакцій для вказаного рахунку за певним типом транзакції.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            account_id (int): ID рахунку користувача.
            transaction_type (TransactionType): Тип транзакції (Enum `TransactionType`).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[AccountTransaction], int]: Кортеж зі списком транзакций та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання транзакцій типу '{transaction_type.value if isinstance(transaction_type, TransactionType) else transaction_type}' для рахунку ID: {account_id}, skip: {skip}, limit: {limit}"
        )
        filters_dict = {
            "account_id": account_id,
            "transaction_type": transaction_type # BaseRepository.get_multi має обробляти Enum
        }
        sort_by_field = "created_at" # Зазвичай транзакції сортують за датою
        sort_order_str = "desc"      # Новіші перші

        try:
            items = await super().get_multi(
                session=session,
                skip=skip,
                limit=limit,
                filters=filters_dict,
                sort_by=sort_by_field,
                sort_order=sort_order_str
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} транзакцій типу '{transaction_type}' для рахунку ID: {account_id}")
            return items, total_count
        except Exception as e:
            logger.error(
                f"Помилка при отриманні транзакцій типу '{transaction_type}' для рахунку {account_id}: {e}",
                exc_info=True
            )
            return [], 0


if __name__ == "__main__":
    # Демонстраційний блок для AccountTransactionRepository.
    logger.info("--- Репозиторій Транзакцій по Рахунках (AccountTransactionRepository) ---")

    logger.info("Для тестування AccountTransactionRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {AccountTransaction.__name__}.")
    logger.info(f"  Очікує схему створення: {AccountTransactionCreateSchema.__name__}")
    logger.info(
        f"  Очікує схему оновлення: {AccountTransactionUpdateSchema.__name__} (зараз порожня, транзакції зазвичай незмінні)")

    logger.info("\nСпецифічні методи:")
    logger.info(
        "  - get_transactions_for_account(account_id: int, skip: int = 0, limit: int = 100, order_by_desc_created_at: bool = True)")
    logger.info("  - get_transactions_by_type(account_id: int, transaction_type: TransactionType, skip: int = 0, limit: int = 100)") # Оновлено тип

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
