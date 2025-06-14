# backend/app/src/repositories/groups/membership_repository.py
"""
Репозиторій для моделі "Членство в Групі" (GroupMembership).

Цей модуль визначає клас `GroupMembershipRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з членством користувачів у групах.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func  # func для count
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.groups.membership import GroupMembership
from backend.app.src.schemas.groups.membership import GroupMembershipCreateSchema, GroupMembershipUpdateSchema
from backend.app.src.config.logging import get_logger # Стандартизований імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class GroupMembershipRepository(
    BaseRepository[GroupMembership, GroupMembershipCreateSchema, GroupMembershipUpdateSchema]):
    """
    Репозиторій для управління записами членства в групах (`GroupMembership`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання членства за парою користувач-група,
    списку учасників групи, списку груп для користувача та ID груп для користувача.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `GroupMembership`.
        """
        super().__init__(model=GroupMembership)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_user_and_group(
            self, session: AsyncSession, user_id: int, group_id: int
    ) -> Optional[GroupMembership]:
        """
        Отримує запис про членство за ID користувача та ID групи.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            group_id (int): ID групи.

        Returns:
            Optional[GroupMembership]: Екземпляр моделі `GroupMembership`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання GroupMembership для user_id {user_id}, group_id {group_id}")
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.group_id == group_id
        )
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Помилка при отриманні GroupMembership для user_id {user_id}, group_id {group_id}: {e}",
                exc_info=True
            )
            return None

    async def get_members_of_group(
            self, session: AsyncSession, group_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[GroupMembership], int]:
        """
        Отримує список членств (учасників) для вказаної групи з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            group_id (int): ID групи.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[GroupMembership], int]: Кортеж зі списком членств та їх загальною кількістю.
        """
        logger.debug(f"Отримання учасників групи group_id: {group_id}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"group_id": group_id}
        # Можна додати сортування, наприклад, за датою приєднання або роллю
        # sort_by_field = "created_at"
        # sort_order_str = "asc"
        # Або жадібне завантаження користувача:
        # options = [selectinload(self.model.user)] # Потребує імпорту selectinload
        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict
                # sort_by=sort_by_field, sort_order=sort_order_str, options=options
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} учасників для group_id: {group_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні учасників для group_id {group_id}: {e}", exc_info=True)
            return [], 0

    async def get_user_group_memberships(
            self, session: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[GroupMembership], int]:
        """
        Отримує список членств у групах для вказаного користувача з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[GroupMembership], int]: Кортеж зі списком членств та їх загальною кількістю.
        """
        logger.debug(f"Отримання членств для user_id: {user_id}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"user_id": user_id}
        # Можна додати сортування, наприклад, за назвою групи (потребує join з Group)
        # Або жадібне завантаження групи:
        # options = [selectinload(self.model.group)] # Потребує імпорту selectinload
        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict
                # options=options
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} членств для user_id: {user_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні членств для user_id {user_id}: {e}", exc_info=True)
            return [], 0

    async def get_user_group_ids(self, session: AsyncSession, user_id: int) -> List[int]:
        """
        Отримує список ID всіх груп, до яких належить вказаний користувач.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.

        Returns:
            List[int]: Список ID груп.
        """
        logger.debug(f"Отримання ID груп для user_id: {user_id}")
        stmt = select(self.model.group_id).where(self.model.user_id == user_id)
        try:
            result = await session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Помилка при отриманні ID груп для user_id {user_id}: {e}", exc_info=True)
            return []


if __name__ == "__main__":
    # Демонстраційний блок для GroupMembershipRepository.
    logger.info("--- Репозиторій Членства в Групах (GroupMembershipRepository) ---")

    logger.info("Для тестування GroupMembershipRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {GroupMembership.__name__}.")
    logger.info(f"  Очікує схему створення: {GroupMembershipCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {GroupMembershipUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_user_and_group(user_id: int, group_id: int)")
    logger.info("  - get_members_of_group(group_id: int, skip: int = 0, limit: int = 100)")
    logger.info("  - get_user_group_memberships(user_id: int, skip: int = 0, limit: int = 100)")
    logger.info("  - get_user_group_ids(user_id: int)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
