# backend/app/src/repositories/groups/group_repository.py
"""
Репозиторій для моделі "Група" (Group).

Цей модуль визначає клас `GroupRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з групами, такі як отримання груп
за власником, отримання груп для учасника та пошук груп за назвою.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func # join видалено, selectinload видалено
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделей та схем
from backend.app.src.models.groups.group import Group
from backend.app.src.models.groups.membership import GroupMembership  # Для join в get_groups_for_member
from backend.app.src.schemas.groups.group import GroupCreateSchema, GroupUpdateSchema
from backend.app.src.config.logging import get_logger # Стандартизований імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class GroupRepository(BaseRepository[Group, GroupCreateSchema, GroupUpdateSchema]):
    """
    Репозиторій для управління записами груп (`Group`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для специфічного пошуку та отримання груп.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `Group`.
        """
        super().__init__(model=Group)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_groups_by_owner_id(
            self, session: AsyncSession, owner_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Group], int]:
        """
        Отримує список груп, що належать вказаному власнику, з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            owner_id (int): ID власника груп.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Group], int]: Кортеж зі списком груп та їх загальною кількістю.
        """
        logger.debug(f"Отримання груп для owner_id: {owner_id}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"owner_id": owner_id}
        # TODO: Визначити поля сортування за замовчуванням, якщо потрібно, наприклад, "name" або "created_at"
        # sort_by_field = "name"
        # sort_order_str = "asc"
        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict
                # sort_by=sort_by_field, sort_order=sort_order_str
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} груп для owner_id: {owner_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні груп для owner_id {owner_id}: {e}", exc_info=True)
            return [], 0

    async def get_groups_for_member(
            self, session: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Group], int]:
        """
        Отримує список груп, до яких належить вказаний користувач (учасник), з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача-учасника.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Group], int]: Кортеж зі списком груп та їх загальною кількістю.
        """
        logger.debug(f"Отримання груп для учасника user_id: {user_id}, skip: {skip}, limit: {limit}")
        try:
            # Запит для підрахунку загальної кількості
            count_stmt = (
                select(func.count(self.model.id))
                .select_from(self.model)
                .join(GroupMembership, self.model.id == GroupMembership.group_id)
                .where(GroupMembership.user_id == user_id)
            )
            total_result = await session.execute(count_stmt)
            total = total_result.scalar_one()

            # Запит для отримання самих груп
            stmt = (
                select(self.model)
                .join(GroupMembership, self.model.id == GroupMembership.group_id)
                .where(GroupMembership.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .order_by(self.model.name) # Сортування за назвою групи
                # .options(selectinload(self.model.owner), selectinload(self.model.group_type)) # Якщо потрібно
            )
            items_result = await session.execute(stmt)
            items = list(items_result.scalars().all())

            logger.debug(f"Знайдено {total} груп для учасника user_id: {user_id}, повернуто {len(items)}")
            return items, total
        except Exception as e:
            logger.error(f"Помилка при отриманні груп для учасника user_id {user_id}: {e}", exc_info=True)
            return [], 0

    async def search_groups_by_name(
            self, session: AsyncSession, name_query: str, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Group], int]:
        """
        Шукає групи за частковим збігом назви (без урахування регістру) з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            name_query (str): Рядок для пошуку в назвах груп.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Group], int]: Кортеж зі списком знайдених груп та їх загальною кількістю.
        """
        logger.debug(f"Пошук груп за назвою: '{name_query}', skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"name__ilike": f"%{name_query}%"}
        sort_by_field = "name"
        sort_order_str = "asc"
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
            logger.debug(f"Знайдено {total_count} груп за запитом '{name_query}'")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при пошуку груп за назвою '{name_query}': {e}", exc_info=True)
            return [], 0


if __name__ == "__main__":
    # Демонстраційний блок для GroupRepository.
    logger.info("--- Репозиторій Груп (GroupRepository) ---")

    logger.info("Для тестування GroupRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {Group.__name__}.")
    logger.info(f"  Очікує схему створення: {GroupCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {GroupUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_groups_by_owner_id(owner_id: int, skip: int = 0, limit: int = 100)")
    logger.info("  - get_groups_for_member(user_id: int, skip: int = 0, limit: int = 100)")
    logger.info("  - search_groups_by_name(name_query: str, skip: int = 0, limit: int = 100)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    # Концептуальний приклад (потребує макетів або реальної сесії):
    # async def demo_group_repo():
    #     # ... setup mock session ...
    #     # repo = GroupRepository(mock_session)
    #     # groups_owned = await repo.get_groups_by_owner_id(owner_id=1)
    #     # logger.info(f"Групи, що належать користувачу 1: {groups_owned}")
    # import asyncio
    # asyncio.run(demo_group_repo())
