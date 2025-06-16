# backend/app/src/repositories/system/health_repository.py
"""
Репозиторій для моделі "Стан Здоров'я Сервісу" (ServiceHealthStatus).

Цей модуль визначає клас `ServiceHealthStatusRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи зі станами здоров'я різних сервісів.
"""

from typing import List, Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.config.logging import get_logger  # Стандартизований імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Абсолютний імпорт моделі та схем
from backend.app.src.models.system.health import ServiceHealthStatus
from backend.app.src.schemas.system.health import ServiceHealthStatusCreateSchema
from backend.app.src.core.dicts import HealthStatusType # Імпортовано Enum


# Записи про стан здоров'я зазвичай створюються або оновлюються повністю,
# тому UpdateSchema може бути такою ж, як CreateSchema, або простою заглушкою,
# якщо оновлення йде через повний об'єкт.
class ServiceHealthStatusUpdateSchema(
    ServiceHealthStatusCreateSchema):  # Або PydanticBaseModel, якщо оновлення не передбачено
    pass


class ServiceHealthStatusRepository(
    BaseRepository[ServiceHealthStatus, ServiceHealthStatusCreateSchema, ServiceHealthStatusUpdateSchema]
):
    """
    Репозиторій для управління записами стану здоров'я сервісів (`ServiceHealthStatus`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    методи для отримання стану за назвою сервісу та списку нездорових сервісів.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `ServiceHealthStatus`.
        """
        super().__init__(model=ServiceHealthStatus)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_service_name(
            self, session: AsyncSession, service_name: str
    ) -> Optional[ServiceHealthStatus]:
        """
        Отримує запис стану здоров'я для вказаного сервісу за його унікальною назвою.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            service_name (str): Унікальна назва сервісу.

        Returns:
            Optional[ServiceHealthStatus]: Екземпляр моделі `ServiceHealthStatus`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання ServiceHealthStatus за service_name: {service_name}")
        stmt = select(self.model).where(self.model.service_name == service_name)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Помилка при отриманні ServiceHealthStatus за service_name {service_name}: {e}",
                exc_info=True
            )
            return None

    async def get_unhealthy_services(self, session: AsyncSession) -> List[ServiceHealthStatus]:
        """
        Отримує список всіх сервісів, які наразі не перебувають у стані 'healthy'.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.

        Returns:
            List[ServiceHealthStatus]: Список записів про стан здоров'я нездорових сервісів.
        """
        logger.debug("Отримання списку нездорових сервісів")
        # Модель ServiceHealthStatus.status використовує HealthStatusType (SQLEnum),
        # тому передаємо Enum член напряму для порівняння.
        filters_dict: Dict[str, Any] = {"status__ne": HealthStatusType.HEALTHY}

        sort_by_field = "updated_at"
        sort_order_str = "desc" # Можна сортувати за часом останньої перевірки або за назвою сервісу

        try:
            # Отримуємо всі записи, що відповідають фільтру, без пагінації (або з великим лімітом)
            items = await super().get_multi(
                session=session,
                filters=filters_dict,
                sort_by=sort_by_field,
                sort_order=sort_order_str,
                limit=1000 # Ліміт для запобігання надмірному завантаженню
            )
            logger.debug(f"Знайдено {len(items)} нездорових сервісів.")
            return items
        except Exception as e:
            logger.error(f"Помилка при отриманні списку нездорових сервісів: {e}", exc_info=True)
            return []

    async def update_or_create_status(
            self, session: AsyncSession, service_name: str, status: HealthStatusType, details: Optional[str] = None
    ) -> Optional[ServiceHealthStatus]:
        """
        Оновлює існуючий запис стану здоров'я сервісу або створює новий, якщо він не існує.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            service_name (str): Унікальна назва сервісу.
            status (HealthStatusType): Новий статус сервісу (Enum).
            details (Optional[str]): Додаткові деталі про стан.

        Returns:
            Optional[ServiceHealthStatus]: Оновлений або створений екземпляр ServiceHealthStatus, або None у разі помилки.
        """
        logger.debug(f"Оновлення або створення статусу для сервісу '{service_name}': status={status}")
        # TODO: [Validation] Переконатися, що 'status' та 'service_name' валідні згідно з Enums/правилами.
        try:
            async with session.begin_nested() if session.in_transaction() else session.begin():
                existing_status = await self.get_by_service_name(session, service_name)

                if existing_status:
                    # Для простоти, якщо ServiceHealthStatusUpdateSchema дозволяє ці поля:
                    # Або, якщо схема оновлення порожня, оновлюємо атрибути напряму:
                    # existing_status.status = status
                    # existing_status.details = details
                    # existing_status.updated_at = datetime.now(timezone.utc) # Якщо TimestampedMixin не спрацює
                    # session.add(existing_status)
                    # db_obj = existing_status
                    update_schema = ServiceHealthStatusUpdateSchema(
                        service_name=service_name, # service_name тут для повноти схеми, хоча воно не оновлюється
                        status=status,
                        details=details
                    )
                    db_obj = await super().update(session, db_obj=existing_status, obj_in=update_schema)
                    logger.info(f"Статус сервісу '{service_name}' оновлено.")
                else:
                    create_schema = ServiceHealthStatusCreateSchema(
                        service_name=service_name,
                        status=status,
                        details=details
                    )
                    db_obj = await super().create(session, obj_in=create_schema)
                    logger.info(f"Створено запис статусу для сервісу '{service_name}'.")

                if db_obj: # Refresh може бути потрібен, якщо create/update не роблять його
                    await session.refresh(db_obj)
                return db_obj
        except Exception as e:
            logger.error(
                f"Помилка при оновленні/створенні статусу для сервісу '{service_name}': {e}",
                exc_info=True
            )
            return None


if __name__ == "__main__":
    # Демонстраційний блок для ServiceHealthStatusRepository.
    logger.info("--- Репозиторій Стану Здоров'я Сервісів (ServiceHealthStatusRepository) ---")

    # Припускаємо, що ServiceHealthStatusCreateSchema визначена в schemas.system.health
    # і приймає service_name, status, details.
    # ServiceHealthStatusUpdateSchema може бути такою ж або дозволяти лише status і details.
    if not hasattr(ServiceHealthStatusCreateSchema, 'model_fields') or \
            not {'service_name', 'status'}.issubset(ServiceHealthStatusCreateSchema.model_fields.keys()):
        logger.info(
            "!!! УВАГА: ServiceHealthStatusCreateSchema не визначена або не має необхідних полів ('service_name', 'status') для демонстрації !!!")

    logger.info(f"Репозиторій працює з моделлю: {ServiceHealthStatus.__name__}.")
    logger.info(f"  Очікує схему створення: backend.app.src.schemas.system.health.ServiceHealthStatusCreateSchema")
    logger.info(f"  Очікує схему оновлення: backend.app.src.schemas.system.health.ServiceHealthStatusUpdateSchema")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_service_name(service_name: str)")
    logger.info("  - get_unhealthy_services()")
    logger.info("  - update_or_create_status(service_name: str, status: HealthStatusType, details: Optional[str])") # Оновлено тип

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    # logger.info("TODO: Інтегрувати Enum 'HealthStatusType' для аргументу `status` та у фільтрах.") # Вирішено

    # Приклад концептуального використання update_or_create_status
    # async def demo_health_repo():
    #     # ... setup mock session ...
    #     # repo = ServiceHealthStatusRepository(mock_session)
    #     # status_db = await repo.update_or_create_status("database", HealthStatusType.HEALTHY.value, "Connection successful")
    #     # logger.info(f"Статус БД: {status_db}")
    #     #
    #     # unhealthy = await repo.get_unhealthy_services()
    #     # logger.info(f"Нездорові сервіси: {unhealthy}")
    # import asyncio
    # asyncio.run(demo_health_repo())
