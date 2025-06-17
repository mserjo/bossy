# backend/app/src/repositories/notifications/notification_template_repository.py
"""
Репозиторій для моделі "Шаблон Сповіщення" (NotificationTemplate).

Цей модуль визначає клас `NotificationTemplateRepository`, який успадковує
`BaseDictionaryRepository` та надає методи для роботи з шаблонами сповіщень.
"""

from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

from backend.app.src.models.notifications.template import NotificationTemplate
from backend.app.src.schemas.notifications.template import (
    NotificationTemplateCreateSchema,
    NotificationTemplateUpdateSchema
)
from backend.app.src.core.dicts import NotificationChannelType


class NotificationTemplateRepository(
    BaseDictionaryRepository[NotificationTemplate, NotificationTemplateCreateSchema, NotificationTemplateUpdateSchema]):
    """
    Репозиторій для управління шаблонами сповіщень (`NotificationTemplate`).

    Успадковує методи від `BaseDictionaryRepository` (включаючи `get_by_code`, `get_by_name`)
    та може містити специфічні методи для роботи з шаблонами.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `NotificationTemplate`.
        """
        super().__init__(model=NotificationTemplate)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_template_type(
            self,
            session: AsyncSession,
            template_type: NotificationChannelType,
            active_only: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[NotificationTemplate], int]:
        """
        Отримує список шаблонів сповіщень за вказаним типом/каналом з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            template_type (NotificationChannelType): Тип/канал шаблону (Enum).
            active_only (bool): Якщо True, повертає лише активні шаблони.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[NotificationTemplate], int]: Кортеж зі списком шаблонів та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання шаблонів за типом: {template_type.value}, active_only: {active_only}, "
            f"skip: {skip}, limit: {limit}"
        )
        # Модель NotificationTemplate.template_type очікує NotificationChannelType (SQLEnum),
        # тому передаємо Enum член напряму.
        filters_dict: Dict[str, Any] = {"template_type": template_type}
        if active_only:
            # Модель NotificationTemplate успадковує BaseDictionaryModel -> BaseMainModel -> StateMixin,
            # тому поле 'state' гарантовано існує.
            # TODO: [Визначення Активного Стану] Уточнити значення для активного стану ("active" або Enum.value),
            #       якщо модель буде використовувати Enum для поля 'state'.
            filters_dict["state"] = "active" # Припускаємо, що активний стан це рядок "active"

        sort_by_field = "name"
        sort_order_str = "asc"  # Сортувати за назвою

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
            logger.debug(f"Знайдено {total_count} шаблонів за типом: {template_type.value if isinstance(template_type, Enum) else template_type}") # Log enum value
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні шаблонів за типом {template_type.value if isinstance(template_type, Enum) else template_type}: {e}", exc_info=True) # Log enum value
            return [], 0


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
    logger.info("  - get_by_template_type(template_type: NotificationChannelType, active_only: bool = True, skip: int = 0, limit: int = 100)") # Оновлено тип

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    logger.info("TODO: Узгодити значення 'active' для фільтра `active_only` з можливим Enum для станів.")
