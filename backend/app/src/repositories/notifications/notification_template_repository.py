# backend/app/src/repositories/notifications/notification_template_repository.py
"""
Репозиторій для моделі "Шаблон Сповіщення" (NotificationTemplate).

Цей модуль визначає клас `NotificationTemplateRepository`, який успадковує
`BaseDictionaryRepository` та надає методи для роботи з шаблонами сповіщень.
"""

from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію для довідників
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Абсолютний імпорт моделі та схем
from backend.app.src.models.notifications.template import NotificationTemplate
from backend.app.src.schemas.notifications.template import (
    NotificationTemplateCreateSchema,
    NotificationTemplateUpdateSchema
)


# TODO: Імпортувати Enum NotificationChannelType з core.dicts, коли він буде визначений,
#       для використання у get_by_template_type.
# from backend.app.src.core.dicts import NotificationChannelType


class NotificationTemplateRepository(
    BaseDictionaryRepository[NotificationTemplate, NotificationTemplateCreateSchema, NotificationTemplateUpdateSchema]):
    """
    Репозиторій для управління шаблонами сповіщень (`NotificationTemplate`).

    Успадковує методи від `BaseDictionaryRepository` (включаючи `get_by_code`, `get_by_name`)
    та може містити специфічні методи для роботи з шаблонами.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `NotificationTemplate`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=NotificationTemplate)

    async def get_by_template_type(
            self,
            template_type: str,  # Очікується значення з NotificationChannelType Enum
            active_only: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[NotificationTemplate], int]:
        """
        Отримує список шаблонів сповіщень за вказаним типом/каналом з пагінацією.

        Args:
            template_type (str): Тип/канал шаблону (значення з NotificationChannelType Enum).
            active_only (bool): Якщо True, повертає лише активні шаблони (state='active').
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[NotificationTemplate], int]: Кортеж зі списком шаблонів та їх загальною кількістю.
        """
        filters = [self.model.template_type == template_type]
        if active_only:
            # Модель NotificationTemplate успадковує BaseDictionaryModel -> BaseMainModel -> StateMixin
            if hasattr(self.model, "state"):
                filters.append(self.model.state == "active")  # TODO: Узгодити з Enum для станів
            # else:
            # logger.warning(f"Модель {self.model.__name__} не має поля 'state' для фільтрації активних шаблонів.")

        order_by = [self.model.name.asc()]  # Сортувати за назвою
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)


if __name__ == "__main__":
    # Демонстраційний блок для NotificationTemplateRepository.
    logger.info("--- Репозиторій Шаблонів Сповіщень (NotificationTemplateRepository) ---")

    logger.info("Для тестування NotificationTemplateRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseDictionaryRepository для моделі {NotificationTemplate.__name__}.")
    logger.info(f"  Очікує схему створення: {NotificationTemplateCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {NotificationTemplateUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи успадковані з BaseDictionaryRepository:")
    logger.info("  - get_by_code(code: str)")
    logger.info("  - get_by_name(name: str)")
    logger.info("\nВласні специфічні методи:")
    logger.info("  - get_by_template_type(template_type: str, active_only: bool = True, skip: int = 0, limit: int = 100)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    logger.info("TODO: Інтегрувати Enum 'NotificationChannelType' для аргументу `template_type`.")
    logger.info("TODO: Узгодити значення 'active' для фільтра `active_only` з можливим Enum для станів.")
