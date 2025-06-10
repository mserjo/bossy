# backend/app/src/repositories/system/health_repository.py
"""
Репозиторій для моделі "Стан Здоров'я Сервісу" (ServiceHealthStatus).

Цей модуль визначає клас `ServiceHealthStatusRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи зі станами здоров'я різних сервісів.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel as PydanticBaseModel  # Для UpdateSchemaType-заглушки

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Абсолютний імпорт моделі та схем
from backend.app.src.models.system.health import ServiceHealthStatus
from backend.app.src.schemas.system.health import \
    ServiceHealthStatusCreateSchema  # Припускаємо, що така схема буде для створення/оновлення


# TODO: Імпортувати Enum HealthStatusType з core.dicts
# from backend.app.src.core.dicts import HealthStatusType

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

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `ServiceHealthStatus`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=ServiceHealthStatus)

    async def get_by_service_name(self, service_name: str) -> Optional[ServiceHealthStatus]:
        """
        Отримує запис стану здоров'я для вказаного сервісу за його унікальною назвою.

        Args:
            service_name (str): Унікальна назва сервісу.

        Returns:
            Optional[ServiceHealthStatus]: Екземпляр моделі `ServiceHealthStatus`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(self.model.service_name == service_name)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_unhealthy_services(self) -> List[ServiceHealthStatus]:
        """
        Отримує список всіх сервісів, які наразі не перебувають у стані 'healthy'.

        Returns:
            List[ServiceHealthStatus]: Список записів про стан здоров'я нездорових сервісів.
        """
        # TODO: Замінити рядок "healthy" на значення з Enum HealthStatusType.HEALTHY.value
        filters = [self.model.status != "healthy"]
        # Можна сортувати за часом останньої перевірки або за назвою сервісу
        order_by = [self.model.updated_at.desc()]

        # Отримуємо всі записи, що відповідають фільтру, без пагінації (або з великим лімітом)
        items, _ = await self.get_multi(filters=filters, order_by=order_by,
                                        limit=1000)  # Ліміт для запобігання надмірному завантаженню
        return items

    async def update_or_create_status(self, service_name: str, status: str,
                                      details: Optional[str] = None) -> ServiceHealthStatus:
        """
        Оновлює існуючий запис стану здоров'я сервісу або створює новий, якщо він не існує.

        Args:
            service_name (str): Унікальна назва сервісу.
            status (str): Новий статус сервісу (значення з HealthStatusType Enum).
            details (Optional[str]): Додаткові деталі про стан.

        Returns:
            ServiceHealthStatus: Оновлений або створений екземпляр ServiceHealthStatus.
        """
        # TODO: Переконатися, що 'status' та 'service_name' валідні згідно з Enums/правилами
        existing_status = await self.get_by_service_name(service_name)
        if existing_status:
            update_data = {"status": status, "details": details}
            # Використовуємо метод update з BaseRepository, передаючи словник
            # Важливо: schema для update може бути простішою або такою ж, як create
            # Для простоти, якщо ServiceHealthStatusUpdateSchema дозволяє ці поля:
            update_schema = ServiceHealthStatusUpdateSchema(status=status, details=details,
                                                            service_name=service_name)  # service_name для повноти схеми, хоча не оновлюється
            return await self.update(db_obj=existing_status, obj_in=update_schema)
        else:
            create_schema = ServiceHealthStatusCreateSchema(
                service_name=service_name,
                status=status,
                details=details
            )
            return await self.create(create_schema)


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
    logger.info("  - update_or_create_status(service_name: str, status: str, details: Optional[str])")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    logger.info("TODO: Інтегрувати Enum 'HealthStatusType' для аргументу `status` та у фільтрах.")

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
