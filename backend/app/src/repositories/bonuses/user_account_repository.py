# backend/app/src/repositories/bonuses/user_account_repository.py
"""
Репозиторій для моделі "Рахунок Користувача" (UserAccount).

Цей модуль визначає клас `UserAccountRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з рахунками користувачів, такі як
отримання рахунку за парою користувач-група та оновлення балансу.
"""

from typing import List, Optional, Tuple, Any
from decimal import Decimal

from sqlalchemy import select, func, update as sqlalchemy_update  # update для атомарного оновлення
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.bonuses.account import UserAccount
from backend.app.src.schemas.bonuses.account import UserAccountCreateSchema, UserAccountUpdateSchema
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class UserAccountRepository(BaseRepository[UserAccount, UserAccountCreateSchema, UserAccountUpdateSchema]):
    """
    Репозиторій для управління рахунками користувачів (`UserAccount`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для роботи з рахунками.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `UserAccount`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=UserAccount)

    async def get_by_user_and_group(self, user_id: int, group_id: int) -> Optional[UserAccount]:
        """
        Отримує запис рахунку за ID користувача та ID групи.

        Args:
            user_id (int): ID користувача.
            group_id (int): ID групи.

        Returns:
            Optional[UserAccount]: Екземпляр моделі `UserAccount`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.group_id == group_id
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_accounts_for_user(self, user_id: int, skip: int = 0, limit: int = 100) -> Tuple[
        List[UserAccount], int]:
        """
        Отримує список всіх рахунків для вказаного користувача з пагінацією.
        (Користувач може мати рахунки в різних групах).

        Args:
            user_id (int): ID користувача.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[UserAccount], int]: Кортеж зі списком рахунків та їх загальною кількістю.
        """
        filters = [self.model.user_id == user_id]
        # options = [selectinload(self.model.group)] # Жадібне завантаження групи
        return await self.get_multi(skip=skip, limit=limit, filters=filters)  # , options=options)

    async def get_accounts_for_group(self, group_id: int, skip: int = 0, limit: int = 100) -> Tuple[
        List[UserAccount], int]:
        """
        Отримує список всіх рахунків у вказаній групі з пагінацією.

        Args:
            group_id (int): ID групи.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[UserAccount], int]: Кортеж зі списком рахунків та їх загальною кількістю.
        """
        filters = [self.model.group_id == group_id]
        # options = [selectinload(self.model.user)] # Жадібне завантаження користувача
        return await self.get_multi(skip=skip, limit=limit, filters=filters)  # , options=options)

    async def update_balance(self, account_id: int, amount_change: Decimal) -> Optional[UserAccount]:
        """
        Атомарно оновлює баланс рахунку на вказану суму (може бути позитивною або від'ємною).

        Примітка: Цей метод виконує пряме оновлення в БД. Для складніших операцій,
        що вимагають створення транзакційних записів, логіка має бути на сервісному рівні.

        Args:
            account_id (int): ID рахунку для оновлення.
            amount_change (Decimal): Сума, на яку потрібно змінити баланс.
                                     Позитивна для збільшення, від'ємна для зменшення.

        Returns:
            Optional[UserAccount]: Оновлений екземпляр UserAccount, якщо операція успішна і запис знайдено,
                                   інакше None (якщо запис не знайдено або оновлення не відбулося).
        """
        # TODO: Розглянути можливість використання select(for_update=True) для блокування рядка,
        #       якщо очікується висока конкуренція за оновлення одного рахунку.
        #       Однак, це може бути надмірним і краще обробляється на рівні транзакцій сервісу.

        stmt = (
            sqlalchemy_update(self.model)
            .where(self.model.id == account_id)
            .values(balance=self.model.balance + amount_change)
            .returning(self.model)  # Повертає оновлений запис
            .execution_options(synchronize_session="fetch")  # Або "evaluate", або False з подальшим refresh
        )

        result = await self.db_session.execute(stmt)
        await self.db_session.commit()  # Потрібен commit для persist змін від update

        updated_obj = result.scalar_one_or_none()

        if updated_obj:
            # Якщо потрібно оновити екземпляр в поточній сесії (наприклад, якщо він вже завантажений)
            # await self.db_session.refresh(updated_obj) # Не завжди потрібно, якщо synchronize_session="fetch"
            # logger.info(f"Баланс рахунку ID {account_id} оновлено на {amount_change}. Новий баланс: {updated_obj.balance}")
            pass
        # else:
        # logger.warning(f"Спроба оновити баланс для неіснуючого рахунку ID {account_id}")

        return updated_obj


if __name__ == "__main__":
    # Демонстраційний блок для UserAccountRepository.
    logger.info("--- Репозиторій Рахунків Користувачів (UserAccountRepository) ---")

    logger.info("Для тестування UserAccountRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {UserAccount.__name__}.")
    # UserAccountUpdateSchema зараз дозволяє оновлювати лише баланс.
    logger.info(f"  Очікує схему створення: {UserAccountCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {UserAccountUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_user_and_group(user_id: int, group_id: int)")
    logger.info("  - get_accounts_for_user(user_id: int, skip: int = 0, limit: int = 100)")
    logger.info("  - get_accounts_for_group(group_id: int, skip: int = 0, limit: int = 100)")
    logger.info("  - update_balance(account_id: int, amount_change: Decimal)")

    logger.info("\nПримітка: Метод `update_balance` виконує атомарне оновлення. Створення запису AccountTransaction")
    logger.info("має відбуватися на сервісному рівні для забезпечення цілісності даних.")
