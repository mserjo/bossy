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
from backend.app.src.schemas.bonuses.transaction import (
    AccountTransactionCreateSchema,
    # AccountTransactionUpdateSchema зазвичай не потрібна, транзакції незмінні
)
from pydantic import BaseModel as PydanticBaseModel  # Для "заглушки" UpdateSchema


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

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

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `AccountTransaction`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=AccountTransaction)

    async def get_transactions_for_account(
            self,
            account_id: int,
            skip: int = 0,
            limit: int = 100,
            order_by_desc_created_at: bool = True
    ) -> Tuple[List[AccountTransaction], int]:
        """
        Отримує список транзакцій для вказаного рахунку з пагінацією та сортуванням.

        Args:
            account_id (int): ID рахунку користувача.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.
            order_by_desc_created_at (bool): Якщо True, сортує транзакції за спаданням дати створення (новіші перші).

        Returns:
            Tuple[List[AccountTransaction], int]: Кортеж зі списком транзакцій та їх загальною кількістю.
        """
        filters = [self.model.account_id == account_id]
        order_by = [self.model.created_at.desc()] if order_by_desc_created_at else [self.model.created_at.asc()]

        # Приклад жадібного завантаження пов'язаних сутностей, якщо вони часто потрібні разом з транзакцією:
        # options = [
        #     selectinload(self.model.task_completion).selectinload(TaskCompletion.task),
        #     selectinload(self.model.reward),
        #     selectinload(self.model.created_by)
        # ]
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)  # , options=options)

    async def get_transactions_by_type(
            self,
            account_id: int,
            transaction_type: str,  # Очікується значення з TransactionType Enum
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[AccountTransaction], int]:
        """
        Отримує список транзакцій для вказаного рахунку за певним типом транзакції.

        Args:
            account_id (int): ID рахунку користувача.
            transaction_type (str): Тип транзакції (значення з `core.dicts.TransactionType`).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[AccountTransaction], int]: Кортеж зі списком транзакций та їх загальною кількістю.
        """
        filters = [
            self.model.account_id == account_id,
            self.model.transaction_type == transaction_type
        ]
        order_by = [self.model.created_at.desc()]
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)


if __name__ == "__main__":
    # Демонстраційний блок для AccountTransactionRepository.
    print("--- Репозиторій Транзакцій по Рахунках (AccountTransactionRepository) ---")

    print("Для тестування AccountTransactionRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {AccountTransaction.__name__}.")
    print(f"  Очікує схему створення: {AccountTransactionCreateSchema.__name__}")
    print(
        f"  Очікує схему оновлення: {AccountTransactionUpdateSchema.__name__} (зараз порожня, транзакції зазвичай незмінні)")

    print("\nСпецифічні методи:")
    print(
        "  - get_transactions_for_account(account_id: int, skip: int = 0, limit: int = 100, order_by_desc_created_at: bool = True)")
    print("  - get_transactions_by_type(account_id: int, transaction_type: str, skip: int = 0, limit: int = 100)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
