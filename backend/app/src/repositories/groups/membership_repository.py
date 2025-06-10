# backend/app/src/repositories/groups/membership_repository.py
"""
Репозиторій для моделі "Членство в Групі" (GroupMembership).

Цей модуль визначає клас `GroupMembershipRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з членством користувачів у групах.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func  # func для count
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload # Якщо потрібно жадібне завантаження user або group

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.groups.membership import GroupMembership
from backend.app.src.schemas.groups.membership import GroupMembershipCreateSchema, GroupMembershipUpdateSchema


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class GroupMembershipRepository(
    BaseRepository[GroupMembership, GroupMembershipCreateSchema, GroupMembershipUpdateSchema]):
    """
    Репозиторій для управління записами членства в групах (`GroupMembership`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання членства за парою користувач-група,
    списку учасників групи, списку груп для користувача та ID груп для користувача.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `GroupMembership`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=GroupMembership)

    async def get_by_user_and_group(self, user_id: int, group_id: int) -> Optional[GroupMembership]:
        """
        Отримує запис про членство за ID користувача та ID групи.

        Args:
            user_id (int): ID користувача.
            group_id (int): ID групи.

        Returns:
            Optional[GroupMembership]: Екземпляр моделі `GroupMembership`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.group_id == group_id
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_members_of_group(self, group_id: int, skip: int = 0, limit: int = 100) -> Tuple[
        List[GroupMembership], int]:
        """
        Отримує список членств (учасників) для вказаної групи з пагінацією.

        Args:
            group_id (int): ID групи.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[GroupMembership], int]: Кортеж зі списком членств та їх загальною кількістю.
        """
        filters = [self.model.group_id == group_id]
        # Можна додати сортування, наприклад, за датою приєднання або роллю
        # order_by = [self.model.created_at.asc()]
        # Або жадібне завантаження користувача:
        # options = [selectinload(self.model.user)]
        return await self.get_multi(skip=skip, limit=limit, filters=filters)  # , order_by=order_by, options=options)

    async def get_user_group_memberships(self, user_id: int, skip: int = 0, limit: int = 100) -> Tuple[
        List[GroupMembership], int]:
        """
        Отримує список членств у групах для вказаного користувача з пагінацією.

        Args:
            user_id (int): ID користувача.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[GroupMembership], int]: Кортеж зі списком членств та їх загальною кількістю.
        """
        filters = [self.model.user_id == user_id]
        # Можна додати сортування, наприклад, за назвою групи (потребує join з Group)
        # Або жадібне завантаження групи:
        # options = [selectinload(self.model.group)]
        return await self.get_multi(skip=skip, limit=limit, filters=filters)  # , options=options)

    async def get_user_group_ids(self, user_id: int) -> List[int]:
        """
        Отримує список ID всіх груп, до яких належить вказаний користувач.

        Args:
            user_id (int): ID користувача.

        Returns:
            List[int]: Список ID груп.
        """
        stmt = select(self.model.group_id).where(self.model.user_id == user_id)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())


if __name__ == "__main__":
    # Демонстраційний блок для GroupMembershipRepository.
    print("--- Репозиторій Членства в Групах (GroupMembershipRepository) ---")

    print("Для тестування GroupMembershipRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {GroupMembership.__name__}.")
    print(f"  Очікує схему створення: {GroupMembershipCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {GroupMembershipUpdateSchema.__name__}")

    print("\nСпецифічні методи:")
    print("  - get_by_user_and_group(user_id: int, group_id: int)")
    print("  - get_members_of_group(group_id: int, skip: int = 0, limit: int = 100)")
    print("  - get_user_group_memberships(user_id: int, skip: int = 0, limit: int = 100)")
    print("  - get_user_group_ids(user_id: int)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
