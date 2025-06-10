# backend/app/src/repositories/groups/invitation_repository.py
"""
Репозиторій для моделі "Запрошення до Групи" (GroupInvitation).

Цей модуль визначає клас `GroupInvitationRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи із запрошеннями до груп.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload # Для жадібного завантаження

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.groups.invitation import GroupInvitation
from backend.app.src.schemas.groups.invitation import GroupInvitationCreateSchema, GroupInvitationUpdateSchema


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class GroupInvitationRepository(
    BaseRepository[GroupInvitation, GroupInvitationCreateSchema, GroupInvitationUpdateSchema]):
    """
    Репозиторій для управління запрошеннями до груп (`GroupInvitation`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання запрошень за кодом, ID групи,
    або парою email-група.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `GroupInvitation`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=GroupInvitation)

    async def get_by_code(self, code: str) -> Optional[GroupInvitation]:
        """
        Отримує запис запрошення за його унікальним кодом.

        Args:
            code (str): Унікальний код запрошення.

        Returns:
            Optional[GroupInvitation]: Екземпляр моделі `GroupInvitation`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(self.model.invitation_code == code)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_group_id(self, group_id: int, skip: int = 0, limit: int = 100) -> Tuple[
        List[GroupInvitation], int]:
        """
        Отримує список запрошень для вказаної групи з пагінацією.

        Args:
            group_id (int): ID групи.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[GroupInvitation], int]: Кортеж зі списком запрошень та їх загальною кількістю.
        """
        filters = [self.model.group_id == group_id]
        # Можна додати сортування, наприклад, за датою створення або терміном дії
        order_by = [self.model.created_at.desc()]
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)

    async def get_by_email_and_group(self, email: str, group_id: int) -> Optional[GroupInvitation]:
        """
        Отримує активне запрошення для конкретного email в конкретній групі.
        Може бути кілька запрошень на один email в різні групи, або навіть в одну, якщо старі не видалені/скасовані.
        Цей метод може потребувати уточнення логіки (наприклад, повертати лише активне/непрострочене).

        Args:
            email (str): Електронна пошта запрошеного.
            group_id (int): ID групи.

        Returns:
            Optional[GroupInvitation]: Екземпляр моделі `GroupInvitation`, якщо знайдено активне запрошення.
        """
        # TODO: Додати фільтр по статусу та expires_at для отримання лише дійсних запрошень.
        # Наприклад:
        # from backend.app.src.core.dicts import InvitationStatus # Потрібен Enum
        # from datetime import datetime, timezone
        # stmt = select(self.model).where(
        #     self.model.email == email,
        #     self.model.group_id == group_id,
        #     self.model.status == InvitationStatus.PENDING.value, # Або відповідний рядок
        #     self.model.expires_at > datetime.now(timezone.utc)
        # )
        stmt = select(self.model).where(
            self.model.email == email,
            self.model.group_id == group_id
        )
        result = await self.db_session.execute(stmt)
        # Якщо може бути кілька, використовуйте .scalars().all() або .first()
        return result.scalar_one_or_none()

        # При створенні (успадкований метод create), GroupInvitationCreateSchema має містити group_id.
    # created_by_user_id, invitation_code, expires_at, status - зазвичай встановлюються сервісом.


if __name__ == "__main__":
    # Демонстраційний блок для GroupInvitationRepository.
    print("--- Репозиторій Запрошень до Груп (GroupInvitationRepository) ---")

    print("Для тестування GroupInvitationRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {GroupInvitation.__name__}.")
    print(f"  Очікує схему створення: {GroupInvitationCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {GroupInvitationUpdateSchema.__name__}")

    print("\nСпецифічні методи:")
    print("  - get_by_code(code: str)")
    print("  - get_by_group_id(group_id: int, skip: int = 0, limit: int = 100)")
    print("  - get_by_email_and_group(email: str, group_id: int)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    print("TODO: Метод get_by_email_and_group може потребувати доопрацювання для фільтрації за статусом/терміном дії.")
