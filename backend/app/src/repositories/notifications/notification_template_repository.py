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
from backend.app.src.config import logger  # Використання спільного логера

# Абсолютний імпорт моделі та схем
from backend.app.src.models.notifications.template import NotificationTemplate
from backend.app.src.schemas.notifications.template import (
    NotificationTemplateCreateSchema,
    NotificationTemplateUpdateSchema
)


# TODO: [Enum Integration] Імпортувати Enum NotificationChannelType,
#       ймовірно з `backend.app.src.core.enums` або аналогічного місця,
#       згідно з `technical_task.txt` / `structure-claude-v2.md`,
#       для використання у `get_by_template_type`.
# from backend.app.src.core.dicts import NotificationChannelType


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
            template_type: str,  # Очікується значення з NotificationChannelType Enum
            active_only: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[NotificationTemplate], int]:
        """
        Отримує список шаблонів сповіщень за вказаним типом/каналом з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            template_type (str): Тип/канал шаблону.
                                 # TODO: [Enum Validation] Використовувати NotificationChannelType Enum.value
                                 #       згідно з `technical_task.txt` / `core.enums`.
            active_only (bool): Якщо True, повертає лише активні шаблони.
                                # TODO: [Перевірка Поля Стану] Узгодити з `technical_task.txt` / `structure-claude-v2.md`
                                #       наявність та значення поля стану (напр., `state="active"`).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[NotificationTemplate], int]: Кортеж зі списком шаблонів та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання шаблонів за типом: {template_type}, active_only: {active_only}, "
            f"skip: {skip}, limit: {limit}"
        )
        filters_dict: Dict[str, Any] = {"template_type": template_type}
        if active_only:
            # Модель NotificationTemplate успадковує BaseDictionaryModel -> BaseMainModel -> StateMixin
            # TODO: [Визначення Активного Стану] Уточнити значення для активного стану ("active", True, etc.)
            #       згідно з `technical_task.txt` / моделлю даних.
            if hasattr(self.model, "state"):
                filters_dict["state"] = "active"
            else:
                logger.warning(
                    f"Модель {self.model.__name__} не має поля 'state' для фільтрації активних шаблонів. "
                    "Фільтр active_only не буде застосовано."
                )

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
            logger.debug(f"Знайдено {total_count} шаблонів за типом: {template_type}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні шаблонів за типом {template_type}: {e}", exc_info=True)
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
    logger.info("  - get_by_template_type(template_type: str, active_only: bool = True, skip: int = 0, limit: int = 100)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    logger.info("TODO: Інтегрувати Enum 'NotificationChannelType' для аргументу `template_type`.")
    logger.info("TODO: Узгодити значення 'active' для фільтра `active_only` з можливим Enum для станів.")
