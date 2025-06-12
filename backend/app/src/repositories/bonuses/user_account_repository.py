# backend/app/src/repositories/bonuses/user_account_repository.py
"""
Репозиторій для моделі "Рахунок Користувача" (UserAccount).

Цей модуль визначає клас `UserAccountRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з рахунками користувачів, такі як
отримання рахунку за парою користувач-група та оновлення балансу.
"""

from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal

from sqlalchemy import select, func, update as sqlalchemy_update  # update для атомарного оновлення
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.bonuses.account import UserAccount
from backend.app.src.schemas.bonuses.account import UserAccountCreateSchema, UserAccountUpdateSchema
from backend.app.src.config import logging # Імпорт logging з конфігурації
# Отримання логера для цього модуля
logger = logging.getLogger(__name__)

class UserAccountRepository(BaseRepository[UserAccount, UserAccountCreateSchema, UserAccountUpdateSchema]):
    """
    Репозиторій для управління рахунками користувачів (`UserAccount`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для роботи з рахунками.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `UserAccount`.
        """
        super().__init__(model=UserAccount)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_user_and_group(
            self, session: AsyncSession, user_id: int, group_id: int
    ) -> Optional[UserAccount]:
        """
        Отримує запис рахунку за ID користувача та ID групи.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            group_id (int): ID групи.

        Returns:
            Optional[UserAccount]: Екземпляр моделі `UserAccount`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання UserAccount для user_id: {user_id}, group_id: {group_id}")
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.group_id == group_id
        )
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Помилка при отриманні UserAccount для user_id {user_id}, group_id {group_id}: {e}",
                exc_info=True
            )
            return None

    async def get_accounts_for_user(
            self, session: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[UserAccount], int]:
        """
        Отримує список всіх рахунків для вказаного користувача з пагінацією.
        (Користувач може мати рахунки в різних групах).

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[UserAccount], int]: Кортеж зі списком рахунків та їх загальною кількістю.
        """
        logger.debug(f"Отримання рахунків для user_id: {user_id}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"user_id": user_id}
        # options = [selectinload(self.model.group)] # Жадібне завантаження групи
        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict #, options=options
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} рахунків для user_id: {user_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні рахунків для user_id {user_id}: {e}", exc_info=True)
            return [], 0

    async def get_accounts_for_group(
            self, session: AsyncSession, group_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[UserAccount], int]:
        """
        Отримує список всіх рахунків у вказаній групі з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            group_id (int): ID групи.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[UserAccount], int]: Кортеж зі списком рахунків та їх загальною кількістю.
        """
        logger.debug(f"Отримання рахунків для group_id: {group_id}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"group_id": group_id}
        # options = [selectinload(self.model.user)] # Жадібне завантаження користувача
        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict #, options=options
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} рахунків для group_id: {group_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні рахунків для group_id {group_id}: {e}", exc_info=True)
            return [], 0

    async def update_balance(
            self, session: AsyncSession, account_id: int, amount_change: Decimal
    ) -> Optional[UserAccount]:
        """
        Атомарно оновлює баланс рахунку на вказану суму (може бути позитивною або від'ємною).

        Примітка: Цей метод виконує пряме оновлення в БД. Для складніших операцій,
        що вимагають створення транзакційних записів, логіка має бути на сервісному рівні.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            account_id (int): ID рахунку для оновлення.
            amount_change (Decimal): Сума, на яку потрібно змінити баланс.
                                     Позитивна для збільшення, від'ємна для зменшення.

        Returns:
            Optional[UserAccount]: Оновлений екземпляр UserAccount, якщо операція успішна і запис знайдено,
                                   інакше None (якщо запис не знайдено або оновлення не відбулося).
        """
        logger.debug(f"Оновлення балансу для рахунку ID: {account_id} на суму: {amount_change}")
        # TODO: Розглянути можливість використання select(for_update=True) для блокування рядка,
        #       якщо очікується висока конкуренція за оновлення одного рахунку.
        #       Однак, це може бути надмірним і краще обробляється на рівні транзакцій сервісу.

        stmt = (
            sqlalchemy_update(self.model)
            .where(self.model.id == account_id)
            .values(balance=self.model.balance + amount_change)
            .returning(self.model)
            .execution_options(synchronize_session="fetch")
        )

        try:
            async with session.begin_nested() if session.in_transaction() else session.begin():
                result = await session.execute(stmt)
                # Commit керується контекстним менеджером або зовнішньою транзакцією

            updated_obj = result.scalar_one_or_none()

            if updated_obj:
                logger.info(
                    f"Баланс рахунку ID {account_id} оновлено на {amount_change}. "
                    f"Новий баланс: {updated_obj.balance}"
                )
            else:
                logger.warning(
                    f"Спроба оновити баланс для неіснуючого рахунку ID {account_id} або оновлення не відбулося."
                )
            return updated_obj
        except Exception as e:
            logger.error(f"Помилка при оновленні балансу для рахунку {account_id}: {e}", exc_info=True)
            # TODO: Розглянути підняття специфічного виключення

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
