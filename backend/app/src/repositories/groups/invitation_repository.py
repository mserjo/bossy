# backend/app/src/repositories/groups/invitation_repository.py
"""
Репозиторій для моделі "Запрошення до Групи" (GroupInvitation).

Цей модуль визначає клас `GroupInvitationRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи із запрошеннями до груп.
"""

from typing import List, Optional, Tuple, Any
from datetime import datetime, timezone # Додано datetime, timezone

from sqlalchemy import select, func, update as sqlalchemy_update # Додано update
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.groups.invitation import GroupInvitation
from backend.app.src.schemas.groups.invitation import GroupInvitationCreateSchema, GroupInvitationUpdateSchema
from backend.app.src.core.dicts import InvitationStatus # Імпорт Enum
from backend.app.src.config.logging import get_logger # Стандартизований імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class GroupInvitationRepository(
    BaseRepository[GroupInvitation, GroupInvitationCreateSchema, GroupInvitationUpdateSchema]):
    """
    Репозиторій для управління запрошеннями до груп (`GroupInvitation`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання запрошень за кодом, ID групи,
    або парою email-група.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `GroupInvitation`.
        """
        super().__init__(model=GroupInvitation)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_code(self, session: AsyncSession, code: str) -> Optional[GroupInvitation]:
        """
        Отримує запис запрошення за його унікальним кодом.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            code (str): Унікальний код запрошення.

        Returns:
            Optional[GroupInvitation]: Екземпляр моделі `GroupInvitation`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання GroupInvitation за кодом: {code}")
        stmt = select(self.model).where(self.model.invitation_code == code)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні GroupInvitation за кодом {code}: {e}", exc_info=True)
            return None

    async def get_by_group_id(
            self, session: AsyncSession, group_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[GroupInvitation], int]:
        """
        Отримує список запрошень для вказаної групи з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            group_id (int): ID групи.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[GroupInvitation], int]: Кортеж зі списком запрошень та їх загальною кількістю.
        """
        logger.debug(f"Отримання запрошень для group_id: {group_id}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"group_id": group_id}
        sort_by_field = "created_at"
        sort_order_str = "desc" # Можна додати сортування, наприклад, за датою створення або терміном дії

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
            logger.debug(f"Знайдено {total_count} запрошень для group_id: {group_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні запрошень для group_id {group_id}: {e}", exc_info=True)
            return [], 0

    async def get_by_email_and_group(
            self, session: AsyncSession, email: str, group_id: int
    ) -> Optional[GroupInvitation]:
        """
        Отримує активне запрошення для конкретного email в конкретній групі.
        Може бути кілька запрошень на один email в різні групи, або навіть в одну, якщо старі не видалені/скасовані.
        Цей метод може потребувати уточнення логіки (наприклад, повертати лише активне/непрострочене).

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            email (str): Електронна пошта запрошеного.
            group_id (int): ID групи.

        Returns:
            Optional[GroupInvitation]: Екземпляр моделі `GroupInvitation`, якщо знайдено активне запрошення.
        """
        logger.debug(f"Отримання GroupInvitation для email {email} та group_id {group_id}")
        """
        logger.debug(f"Отримання GroupInvitation для email {email} та group_id {group_id}")
        conditions = [
            self.model.email == email.lower(), # Нормалізація email
            self.model.group_id == group_id,
            self.model.status == InvitationStatus.PENDING,
            self.model.expires_at > datetime.now(timezone.utc)
        ]
        stmt = select(self.model).where(*conditions)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Помилка при отриманні активного GroupInvitation для email {email}, group_id {group_id}: {e}",
                exc_info=True
            )
            return None

    async def get_by_user_and_group_active_pending(
            self, session: AsyncSession, user_id: int, group_id: int
    ) -> Optional[GroupInvitation]:
        """
        Отримує активне та очікуюче запрошення для конкретного user_id в конкретній групі.
        """
        logger.debug(f"Отримання активного/очікуючого GroupInvitation для user_id {user_id} та group_id {group_id}")
        conditions = [
            self.model.invited_user_id == user_id,
            self.model.group_id == group_id,
            self.model.status == InvitationStatus.PENDING,
            self.model.expires_at > datetime.now(timezone.utc)
        ]
        stmt = select(self.model).where(*conditions)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Помилка при отриманні активного/очікуючого GroupInvitation для user_id {user_id}, group_id {group_id}: {e}",
                exc_info=True
            )
            return None

    async def list_pending_by_group(
            self, session: AsyncSession, group_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[GroupInvitation], int]:
        """
        Перелічує активні (pending, не прострочені) запрошення для вказаної групи.
        """
        logger.debug(f"Перелік активних запрошень для group_id: {group_id}, skip: {skip}, limit: {limit}")

        filters_dict: Dict[str, Any] = {
            "group_id": group_id,
            "status": InvitationStatus.PENDING,
            "expires_at__gt": datetime.now(timezone.utc) # Умова "більше ніж"
        }
        # BaseRepository.get_multi має підтримувати __gt, __lt тощо.
        # Якщо ні, то цей метод потребуватиме прямого запиту select().
        # Припускаємо, що BaseRepository це обробляє.

        sort_by_field = "created_at"
        sort_order_str = "desc"

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
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні активних запрошень для group_id {group_id}: {e}", exc_info=True)
            return [],0

    async def update_status_for_expired(self, session: AsyncSession) -> int:
        """
        Оновлює статус прострочених 'pending' запрошень на 'expired'.
        Повертає кількість оновлених записів.
        """
        logger.info("Оновлення статусу прострочених запрошень на 'expired'")
        now = datetime.now(timezone.utc)
        stmt = (
            sqlalchemy_update(self.model)
            .where(
                self.model.status == InvitationStatus.PENDING,
                self.model.expires_at < now
            )
            .values(status=InvitationStatus.EXPIRED, responded_at=now)
            .execution_options(synchronize_session=False) # Важливо для SQLAlchemy < 2.0
        )
        try:
            result = await session.execute(stmt)
            # Немає потреби в self.commit() тут, це має робитися на рівні сервісу або Unit of Work
            logger.info(f"Оновлено {result.rowcount} запрошень на статус 'expired'.")
            return result.rowcount
        except Exception as e:
            logger.error(f"Помилка при оновленні статусу прострочених запрошень: {e}", exc_info=True)
            return 0


if __name__ == "__main__":
    # Демонстраційний блок для GroupInvitationRepository.
    logger.info("--- Репозиторій Запрошень до Груп (GroupInvitationRepository) ---")

    logger.info("Для тестування GroupInvitationRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {GroupInvitation.__name__}.")
    logger.info(f"  Очікує схему створення: {GroupInvitationCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {GroupInvitationUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_code(code: str)")
    logger.info("  - get_by_group_id(group_id: int, skip: int = 0, limit: int = 100)")
    logger.info("  - get_by_email_and_group(email: str, group_id: int) -> Optional[GroupInvitation] (тепер фільтрує активні)")
    logger.info("  - get_by_user_and_group_active_pending(user_id: int, group_id: int) -> Optional[GroupInvitation]")
    logger.info("  - list_pending_by_group(group_id: int, skip: int = 0, limit: int = 100)")
    logger.info("  - update_status_for_expired() -> int")


    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    # logger.info("TODO: Метод get_by_email_and_group може потребувати доопрацювання для фільтрації за статусом/терміном дії.") # Вирішено
