# backend/app/src/repositories/notifications/notification_repository.py
"""
Репозиторій для моделі "Сповіщення" (Notification).

Цей модуль визначає клас `NotificationRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи зі сповіщеннями користувачів.
"""

from typing import List, Optional, Tuple, Any
from datetime import datetime, timezone

from sqlalchemy import select, func, update as sqlalchemy_update
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Абсолютний імпорт моделі та схем
from backend.app.src.models.notifications.notification import Notification
from backend.app.src.schemas.notifications.notification import (
    NotificationCreateSchema,
    NotificationUpdateSchema  # Для позначки як прочитане
)
from backend.app.src.core.dicts import NotificationType # Імпортовано Enum


class NotificationRepository(BaseRepository[Notification, NotificationCreateSchema, NotificationUpdateSchema]):
    """
    Репозиторій для управління сповіщеннями (`Notification`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    методи для отримання сповіщень для користувача, позначки їх як прочитаних.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `Notification`.
        """
        super().__init__(model=Notification)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_notifications_for_user(
            self,
            session: AsyncSession,
            user_id: int,
            *,
            is_read: Optional[bool] = None,
            notification_type: Optional[NotificationType] = None,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[Notification], int]:
        """
        Отримує список сповіщень для вказаного користувача з пагінацією та фільтрами.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            is_read (Optional[bool]): Фільтр за статусом прочитання.
            notification_type (Optional[NotificationType]): Фільтр за типом сповіщення (Enum).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Notification], int]: Кортеж зі списком сповіщень та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання сповіщень для user_id {user_id}, is_read: {is_read}, type: {notification_type}, "
            f"skip: {skip}, limit: {limit}"
        )
        filters_dict: Dict[str, Any] = {"user_id": user_id}
        if is_read is not None:
            filters_dict["is_read"] = is_read
        if notification_type is not None:
            filters_dict["notification_type"] = notification_type

        sort_by_field = "created_at"
        sort_order_str = "desc"  # Новіші сповіщення першими

        # options = [selectinload(self.model.template)] # Приклад жадібного завантаження
        try:
            items = await super().get_multi(
                session=session,
                skip=skip,
                limit=limit,
                filters=filters_dict,
                sort_by=sort_by_field,
                sort_order=sort_order_str
                # options=options
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} сповіщень для user_id {user_id} з фільтрами.")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні сповіщень для user_id {user_id}: {e}", exc_info=True)
            return [], 0

    async def mark_as_read(self, session: AsyncSession, notification_id: int, user_id: int) -> Optional[Notification]:
        """
        Позначає конкретне сповіщення як прочитане для вказаного користувача.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            notification_id (int): ID сповіщення, яке потрібно позначити як прочитане.
            user_id (int): ID користувача, для якого позначається сповіщення (для перевірки прав).

        Returns:
            Optional[Notification]: Оновлений екземпляр сповіщення, якщо операція успішна
                                    і сповіщення належало користувачеві та не було вже прочитане.
                                    None, якщо сповіщення не знайдено, не належить користувачеві,
                                    або вже було прочитане, або у разі помилки.
        """
        logger.debug(f"Позначення сповіщення ID {notification_id} як прочитаного для user_id {user_id}")
        try:
            db_obj = await super().get(session, notification_id)

            if db_obj and db_obj.user_id == user_id and not db_obj.is_read:
                update_data = {
                    "is_read": True,
                    "read_at": datetime.now(timezone.utc)
                }
                updated_notification = await super().update(session, db_obj=db_obj, obj_in=update_data)
                logger.info(f"Сповіщення ID {notification_id} позначено як прочитане для user_id {user_id}.")
                return updated_notification
            elif db_obj:
                logger.warning(
                    f"Сповіщення ID {notification_id} для user_id {user_id} не оновлено: "
                    f"is_owner={db_obj.user_id == user_id}, is_unread={not db_obj.is_read}"
                )
            else:
                logger.warning(f"Сповіщення ID {notification_id} не знайдено для user_id {user_id}.")
            return None
        except Exception as e:
            logger.error(
                f"Помилка при позначенні сповіщення ID {notification_id} як прочитаного: {e}",
                exc_info=True
            )
            return None

    async def mark_all_as_read_for_user(self, session: AsyncSession, user_id: int) -> int:
        """
        Позначає всі непрочитані сповіщення для вказаного користувача як прочитані.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.

        Returns:
            int: Кількість сповіщень, позначених як прочитані.
        """
        logger.debug(f"Позначення всіх сповіщень як прочитаних для user_id {user_id}")
        stmt = (
            sqlalchemy_update(self.model)
            .where(self.model.user_id == user_id, self.model.is_read == False)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        try:
            async with session.begin_nested() if session.in_transaction() else session.begin():
                result = await session.execute(stmt)
                # await session.commit() # Commit керується контекстним менеджером або зовнішньою транзакцією
            rowcount = result.rowcount
            logger.info(f"{rowcount} сповіщень позначено як прочитані для користувача ID {user_id}.")
            return rowcount
        except Exception as e:
            logger.error(
                f"Помилка при позначенні всіх сповіщень як прочитаних для user_id {user_id}: {e}",
                exc_info=True
            )
            return 0
        # return result.rowcount # Цей рядок недосяжний


if __name__ == "__main__":
    # Демонстраційний блок для NotificationRepository.
    logger.info("--- Репозиторій Сповіщень (NotificationRepository) ---")

    logger.info("Для тестування NotificationRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {Notification.__name__}.")
    logger.info(f"  Очікує схему створення: {NotificationCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {NotificationUpdateSchema.__name__} (для is_read)")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_notifications_for_user(user_id, is_read, notification_type, skip, limit)")
    logger.info("  - mark_as_read(notification_id, user_id)")
    logger.info("  - mark_all_as_read_for_user(user_id)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
