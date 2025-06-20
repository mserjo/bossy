# backend/app/src/repositories/notifications/delivery_attempt_repository.py
"""
Репозиторій для моделі "Спроба Доставки Сповіщення" (NotificationDeliveryAttempt).

Цей модуль визначає клас `NotificationDeliveryAttemptRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи зі спробами доставки сповіщень.
"""

from typing import List, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.notifications.delivery import NotificationDeliveryAttempt
from backend.app.src.schemas.notifications.delivery import NotificationDeliveryAttemptCreateSchema
# NotificationDeliveryAttemptUpdateSchema зазвичай не потрібна
from pydantic import BaseModel as PydanticBaseModel  # Для "заглушки" UpdateSchema
from backend.app.src.config.logging import get_logger
from backend.app.src.core.dicts import NotificationChannelType, DeliveryStatusType
logger = get_logger(__name__)

# Enums NotificationChannelType та DeliveryStatusType імпортовано вище.


# Спроби доставки зазвичай не оновлюються, а створюються нові для кожної спроби.
class NotificationDeliveryAttemptUpdateSchema(PydanticBaseModel):
    pass


class NotificationDeliveryAttemptRepository(
    BaseRepository[
        NotificationDeliveryAttempt,
        NotificationDeliveryAttemptCreateSchema,
        NotificationDeliveryAttemptUpdateSchema
    ]
):
    """
    Репозиторій для управління записами про спроби доставки сповіщень (`NotificationDeliveryAttempt`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    методи для отримання історії спроб для конкретного сповіщення або
    невдалих спроб за певним каналом.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `NotificationDeliveryAttempt`.
        """
        super().__init__(model=NotificationDeliveryAttempt)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_attempts_for_notification(
            self,
            session: AsyncSession,
            notification_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[NotificationDeliveryAttempt], int]:
        """
        Отримує список всіх спроб доставки для вказаного сповіщення з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            notification_id (int): ID сповіщення.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[NotificationDeliveryAttempt], int]: Кортеж зі списком спроб доставки та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання спроб доставки для notification_id: {notification_id}, skip: {skip}, limit: {limit}"
        )
        filters_dict: Dict[str, Any] = {"notification_id": notification_id}
        sort_by_field = "created_at"
        sort_order_str = "desc"  # Показувати останні спроби першими

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
            logger.debug(f"Знайдено {total_count} спроб для notification_id: {notification_id}")
            return items, total_count
        except Exception as e:
            logger.error(
                f"Помилка при отриманні спроб доставки для notification_id {notification_id}: {e}",
                exc_info=True
            )
            return [], 0

    async def get_failed_attempts_by_channel(
            self,
            session: AsyncSession,
            channel: NotificationChannelType,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[NotificationDeliveryAttempt], int]:
        """
        Отримує список невдалих спроб доставки за вказаним каналом з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            channel (NotificationChannelType): Канал доставки (Enum).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[NotificationDeliveryAttempt], int]: Кортеж зі списком невдалих спроб та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання невдалих спроб для каналу: {channel.value}, skip: {skip}, limit: {limit}"
        )
        filters_dict: Dict[str, Any] = {
            "channel": channel, # Передаємо Enum член напряму
            "status": DeliveryStatusType.FAILED # Використовуємо Enum член напряму
        }
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
            logger.debug(f"Знайдено {total_count} невдалих спроб для каналу: {channel.value if isinstance(channel, Enum) else channel}") # Log enum value
            return items, total_count
        except Exception as e:
            logger.error(
                f"Помилка при отриманні невдалих спроб для каналу {channel}: {e}",
                exc_info=True
            )
            return [], 0

    async def list_retryable_attempts(
        self,
        session: AsyncSession,
        max_attempts: int,
        age_threshold: datetime, # Поріг часу (created_at >= age_threshold)
        with_relations: bool = False, # Для завантаження зв'язків Notification -> User
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[NotificationDeliveryAttempt], int]:
        """
        Отримує список спроб доставки, які можна повторити.
        Фільтрує за статусом, кількістю спроб та віком запису.
        """
        logger.debug(
            f"Отримання спроб для повтору: max_attempts < {max_attempts}, created_at >= {age_threshold}, "
            f"skip: {skip}, limit: {limit}, with_relations: {with_relations}"
        )

        conditions = [
            self.model.status.in_([DeliveryStatusType.FAILED, DeliveryStatusType.RETRY_SCHEDULED]),
            self.model.attempt_count < max_attempts,
            self.model.created_at >= age_threshold
        ]

        stmt = select(self.model).where(*conditions).order_by(self.model.created_at.asc()) # Обробляємо старіші спочатку

        if with_relations:
            from backend.app.src.models.notifications.notification import Notification # Локальний імпорт
            from backend.app.src.models.auth.user import User # Локальний імпорт
            stmt = stmt.options(
                selectinload(self.model.notification).options(
                    selectinload(Notification.user).options(selectinload(User.user_type))
                )
            )

        # Для підрахунку загальної кількості перед пагінацією
        count_stmt = select(func.count(self.model.id)).where(*conditions)

        # Застосування пагінації
        stmt = stmt.offset(skip).limit(limit)

        try:
            total_count_result = await session.execute(count_stmt)
            total_count = total_count_result.scalar_one_or_none() or 0

            items_result = await session.execute(stmt)
            items = list(items_result.scalars().all()) # unique() не потрібен, якщо with_relations правильно використовує options

            logger.debug(f"Знайдено {total_count} спроб для повтору, повернуто {len(items)}.")
            return items, total_count
        except Exception as e:
            logger.error(
                f"Помилка при отриманні спроб для повтору: {e}",
                exc_info=True
            )
            return [], 0


if __name__ == "__main__":
    # Демонстраційний блок для NotificationDeliveryAttemptRepository.
    logger.info("--- Репозиторій Спроб Доставки Сповіщень (NotificationDeliveryAttemptRepository) ---")

    logger.info(
        "Для тестування NotificationDeliveryAttemptRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {NotificationDeliveryAttempt.__name__}.")
    logger.info(f"  Очікує схему створення: {NotificationDeliveryAttemptCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {NotificationDeliveryAttemptUpdateSchema.__name__} (зараз порожня)")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_attempts_for_notification(notification_id: int, skip: int = 0, limit: int = 100)")
    logger.info("  - get_failed_attempts_by_channel(channel: NotificationChannelType, skip: int = 0, limit: int = 100)")
    logger.info("  - list_retryable_attempts(max_attempts: int, age_threshold: datetime, with_relations: bool = False, skip: int = 0, limit: int = 100)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
