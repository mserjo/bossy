# backend/app/src/repositories/groups/group_repository.py
"""
Репозиторій для моделі "Група" (Group).

Цей модуль визначає клас `GroupRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з групами, такі як отримання груп
за власником, отримання груп для учасника та пошук груп за назвою.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func, join
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  # Для жадібного завантаження зв'язків, якщо потрібно

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделей та схем
from backend.app.src.models.groups.group import Group
from backend.app.src.models.groups.membership import GroupMembership  # Для join в get_groups_for_member
from backend.app.src.models.auth.user import User  # Необов'язково тут, якщо фільтри передаються як вирази
from backend.app.src.schemas.groups.group import GroupCreateSchema, GroupUpdateSchema


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class GroupRepository(BaseRepository[Group, GroupCreateSchema, GroupUpdateSchema]):
    """
    Репозиторій для управління записами груп (`Group`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для специфічного пошуку та отримання груп.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `Group`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=Group)

    async def get_groups_by_owner_id(self, owner_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[Group], int]:
        """
        Отримує список груп, що належать вказаному власнику, з пагінацією.

        Args:
            owner_id (int): ID власника груп.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Group], int]: Кортеж зі списком груп та їх загальною кількістю.
        """
        filters = [self.model.owner_id == owner_id]
        return await self.get_multi(skip=skip, limit=limit, filters=filters)

    async def get_groups_for_member(self, user_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[Group], int]:
        """
        Отримує список груп, до яких належить вказаний користувач (учасник), з пагінацією.

        Args:
            user_id (int): ID користувача-учасника.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Group], int]: Кортеж зі списком груп та їх загальною кількістю.
        """
        # Запит для підрахунку загальної кількості
        count_stmt = (
            select(func.count(self.model.id))
            .select_from(self.model)
            .join(GroupMembership, self.model.id == GroupMembership.group_id)
            .where(GroupMembership.user_id == user_id)
        )
        total = (await self.db_session.execute(count_stmt)).scalar_one()

        # Запит для отримання самих груп
        stmt = (
            select(self.model)
            .join(GroupMembership, self.model.id == GroupMembership.group_id)
            .where(GroupMembership.user_id == user_id)
            .offset(skip)
            .limit(limit)
            # Опціонально: додати order_by, наприклад, за назвою групи або датою створення
            .order_by(self.model.name)
            # Опціонально: жадібне завантаження пов'язаних даних, якщо потрібно уникнути N+1
            # .options(selectinload(self.model.owner), selectinload(self.model.group_type))
        )

        items_result = await self.db_session.execute(stmt)
        items = list(items_result.scalars().all())

        return items, total

    async def search_groups_by_name(self, name_query: str, skip: int = 0, limit: int = 100) -> Tuple[List[Group], int]:
        """
        Шукає групи за частковим збігом назви (без урахування регістру) з пагінацією.

        Args:
            name_query (str): Рядок для пошуку в назвах груп.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Group], int]: Кортеж зі списком знайдених груп та їх загальною кількістю.
        """
        filters = [self.model.name.ilike(f"%{name_query}%")]
        # Можна додати сортування за релевантністю або назвою
        order_by = [self.model.name]
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)


if __name__ == "__main__":
    # Демонстраційний блок для GroupRepository.
    print("--- Репозиторій Груп (GroupRepository) ---")

    print("Для тестування GroupRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {Group.__name__}.")
    print(f"  Очікує схему створення: {GroupCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {GroupUpdateSchema.__name__}")

    print("\nСпецифічні методи:")
    print("  - get_groups_by_owner_id(owner_id: int, skip: int = 0, limit: int = 100)")
    print("  - get_groups_for_member(user_id: int, skip: int = 0, limit: int = 100)")
    print("  - search_groups_by_name(name_query: str, skip: int = 0, limit: int = 100)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    # Концептуальний приклад (потребує макетів або реальної сесії):
    # async def demo_group_repo():
    #     # ... setup mock session ...
    #     # repo = GroupRepository(mock_session)
    #     # groups_owned = await repo.get_groups_by_owner_id(owner_id=1)
    #     # print(f"Групи, що належать користувачу 1: {groups_owned}")
    # import asyncio
    # asyncio.run(demo_group_repo())
