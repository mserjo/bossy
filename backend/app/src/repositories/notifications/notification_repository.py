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
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Абсолютний імпорт моделі та схем
from backend.app.src.models.notifications.notification import Notification
from backend.app.src.schemas.notifications.notification import (
    NotificationCreateSchema,
    NotificationUpdateSchema  # Для позначки як прочитане
)


# from backend.app.src.core.dicts import NotificationType as NotificationTypeEnum # Для фільтрації


class NotificationRepository(BaseRepository[Notification, NotificationCreateSchema, NotificationUpdateSchema]):
    """
    Репозиторій для управління сповіщеннями (`Notification`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    методи для отримання сповіщень для користувача, позначки їх як прочитаних.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `Notification`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=Notification)

    async def get_notifications_for_user(
            self,
            user_id: int,
            *,
            is_read: Optional[bool] = None,
            notification_type: Optional[str] = None,  # Очікується значення з NotificationTypeEnum
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[Notification], int]:
        """
        Отримує список сповіщень для вказаного користувача з пагінацією та фільтрами.

        Args:
            user_id (int): ID користувача.
            is_read (Optional[bool]): Фільтр за статусом прочитання.
            notification_type (Optional[str]): Фільтр за типом сповіщення
                                               (значення з `core.dicts.NotificationType`).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Notification], int]: Кортеж зі списком сповіщень та їх загальною кількістю.
        """
        filters = [self.model.user_id == user_id]
        if is_read is not None:
            filters.append(self.model.is_read == is_read)
        if notification_type is not None:
            # TODO: Переконатися, що notification_type передається як Enum.value або валідується
            filters.append(self.model.notification_type == notification_type)

        order_by = [self.model.created_at.desc()]  # Новіші сповіщення першими

        # options = [selectinload(self.model.template)] # Приклад жадібного завантаження
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)  # , options=options)

    async def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        """
        Позначає конкретне сповіщення як прочитане для вказаного користувача.

        Args:
            notification_id (int): ID сповіщення, яке потрібно позначити як прочитане.
            user_id (int): ID користувача, для якого позначається сповіщення (для перевірки прав).

        Returns:
            Optional[Notification]: Оновлений екземпляр сповіщення, якщо операція успішна
                                    і сповіщення належало користувачеві та не було вже прочитане.
                                    None, якщо сповіщення не знайдено, не належить користувачеві,
                                    або вже було прочитане.
        """
        db_obj = await self.get(notification_id)

        if db_obj and db_obj.user_id == user_id and not db_obj.is_read:
            update_data = {
                "is_read": True,
                "read_at": datetime.now(timezone.utc)
            }
            # Використовуємо успадкований метод update, передаючи словник
            return await super().update(db_obj=db_obj, obj_in=update_data)

        # logger.warning(f"Сповіщення ID {notification_id} не знайдено для користувача ID {user_id} або вже прочитано.")
        return None  # Або повернути db_obj, якщо він знайдений, але не оновлений

    async def mark_all_as_read_for_user(self, user_id: int) -> int:
        """
        Позначає всі непрочитані сповіщення для вказаного користувача як прочитані.

        Args:
            user_id (int): ID користувача.

        Returns:
            int: Кількість сповіщень, позначених як прочитані.
        """
        stmt = (
            sqlalchemy_update(self.model)
            .where(self.model.user_id == user_id, self.model.is_read == False)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
            # .execution_options(synchronize_session=False) # Може бути потрібно для деяких діалектів/ситуацій
        )
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        # logger.info(f"{result.rowcount} сповіщень позначено як прочитані для користувача ID {user_id}.")
        return result.rowcount


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
    logger.info("TODO: Переконатися, що `notification_type` у `get_notifications_for_user` коректно обробляється з Enum.")
