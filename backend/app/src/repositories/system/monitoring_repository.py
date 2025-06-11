# backend/app/src/repositories/system/monitoring_repository.py
"""
Репозиторії для моделей системного моніторингу (Системні Логи та Метрики Продуктивності).

Цей модуль визначає:
- `SystemLogRepository`: для роботи з записами системних логів (`SystemLog`).
- `PerformanceMetricRepository`: для роботи з метриками продуктивності (`PerformanceMetric`).
"""

from typing import List, Optional, Tuple, Any, Dict

from sqlalchemy import select, func, delete as sqlalchemy_delete  # delete для можливих операцій очищення
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel as PydanticBaseModel  # Для UpdateSchemaType-заглушок

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Абсолютний імпорт моделей та схем
from backend.app.src.models.system.monitoring import SystemLog, PerformanceMetric
from backend.app.src.schemas.system.monitoring import (
    SystemLogCreateSchema,
    PerformanceMetricCreateSchema
)


# TODO: Імпортувати Enums, наприклад, LogLevel, коли вони будуть визначені в core.dicts
# from backend.app.src.core.dicts import LogLevel as LogLevelEnum

# Системні логи та метрики зазвичай не оновлюються; вони є записами подій.
# Тому UpdateSchema може бути простою заглушкою.
class SystemLogUpdateSchema(PydanticBaseModel):
    pass


class PerformanceMetricUpdateSchema(PydanticBaseModel):
    pass


class SystemLogRepository(BaseRepository[SystemLog, SystemLogCreateSchema, SystemLogUpdateSchema]):
    """
    Репозиторій для управління записами системних логів (`SystemLog`).

    Успадковує базові CRUD-методи. Надає методи для фільтрації логів
    за рівнем, джерелом або користувачем.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session=db_session, model=SystemLog)

    async def get_logs_by_level(
            self,
            level: str,  # Очікується значення з LogLevel Enum
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[SystemLog], int]:
        """Отримує логи за вказаним рівнем."""
        # TODO: Використовувати LogLevelEnum.LEVEL.value для порівняння
        filters = [self.model.level == level]
        order_by = [self.model.timestamp.desc()]
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)

    async def get_logs_by_source(
            self,
            source: str,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[SystemLog], int]:
        """Отримує логи за вказаним джерелом."""
        filters = [self.model.source == source]
        order_by = [self.model.timestamp.desc()]
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)

    async def get_logs_for_user(
            self,
            user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[SystemLog], int]:
        """Отримує логи, пов'язані з конкретним користувачем."""
        filters = [self.model.user_id == user_id]
        order_by = [self.model.timestamp.desc()]
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)

    async def clear_old_logs(self, before_timestamp: datetime) -> int:
        """Видаляє старі записи логів до вказаної дати."""
        stmt = sqlalchemy_delete(self.model).where(self.model.timestamp < before_timestamp)
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.rowcount


class PerformanceMetricRepository(
    BaseRepository[PerformanceMetric, PerformanceMetricCreateSchema, PerformanceMetricUpdateSchema]):
    """
    Репозиторій для управління метриками продуктивності (`PerformanceMetric`).

    Успадковує базові CRUD-методи. Надає методи для фільтрації метрик
    за назвою або тегами.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session=db_session, model=PerformanceMetric)

    async def get_metrics_by_name(
            self,
            metric_name: str,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[PerformanceMetric], int]:
        """Отримує метрики за вказаною назвою."""
        filters = [self.model.metric_name == metric_name]
        order_by = [self.model.timestamp.desc()]
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)

    async def get_metrics_by_tag(
            self,
            tag_key: str,
            tag_value: str,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[PerformanceMetric], int]:
        """
        Отримує метрики, що містять вказаний тег (ключ-значення).
        Потребує підтримки JSON операторів на рівні БД (наприклад, PostgreSQL JSONB).
        """
        # TODO: Адаптувати запит для конкретного діалекту БД та типу JSON поля.
        #       Наведений приклад є концептуальним для PostgreSQL JSONB.
        #       Для інших БД може знадобитися інший синтаксис або підхід.
        #       Наприклад, self.model.tags[tag_key].astext == tag_value (для PostgreSQL)
        #       Або self.model.tags.op('->>')(tag_key) == tag_value
        #       Якщо використовується SQLite з JSON1 розширенням: json_extract(self.model.tags, '$.tag_key') == tag_value

        # Простий варіант, якщо теги неглибокі і можна шукати по частині рядка (менш точно):
        # filters = [self.model.tags.cast(String).ilike(f'%"{tag_key}": "{tag_value}"%')]

        # Більш точний варіант для PostgreSQL (якщо поле tags є JSONB):
        # filters = [self.model.tags[tag_key].as_string() == tag_value] # SQLAlchemy 2.0+
        # Або для старіших версій / інших діалектів:
        # from sqlalchemy.dialects.postgresql import JSONB
        # filters = [self.model.tags.cast(JSONB)[tag_key].astext == tag_value]

        # Наразі, без конкретизації діалекту, залишимо це як TODO для реалізації
        # або спростимо до пошуку, якщо це можливо без складних JSON операторів.
        # Для демонстрації, повернемо порожній результат, вказуючи на потребу реалізації.
        # logger.warning("Метод get_metrics_by_tag потребує реалізації специфічного для БД JSON-запиту.")

        # Приклад фільтрації, якщо теги зберігаються як рядок JSON (неефективно):
        # filters = [self.model.tags.isnot(None), self.model.tags.cast(String).contains(f'"{tag_key}":"{tag_value}"')]

        # Якщо припустити, що ми не можемо зробити ефективний SQL запит по JSON зараз:
        # Повернемо всі і фільтруватимемо в Python (дуже неефективно для великих датасетів!)
        # all_items, total = await self.get_multi(skip=0, limit=1_000_000) # Отримати все (погано)
        # filtered_items = [item for item in all_items if item.tags and item.tags.get(tag_key) == tag_value]
        # paginated_items = filtered_items[skip : skip + limit]
        # return paginated_items, len(filtered_items)

        # Поки що повертаємо помилку, що метод не реалізовано належним чином
        raise NotImplementedError(
            "Пошук за тегами в JSON потребує специфічної для БД реалізації або іншої стратегії зберігання тегів.")

    async def clear_old_metrics(self, before_timestamp: datetime) -> int:
        """Видаляє старі записи метрик до вказаної дати."""
        stmt = sqlalchemy_delete(self.model).where(self.model.timestamp < before_timestamp)
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.rowcount


if __name__ == "__main__":
    # Демонстраційний блок для репозиторіїв моніторингу.
    logger.info("--- Репозиторії Системного Моніторингу ---")

    logger.info(f"\n--- Репозиторій Системних Логів ({SystemLogRepository.__name__}) ---")
    logger.info(f"Модель: {SystemLog.__name__}, Схема створення: {SystemLogCreateSchema.__name__}")
    logger.info("Специфічні методи:")
    logger.info("  - get_logs_by_level(level: str, ...)")
    logger.info("  - get_logs_by_source(source: str, ...)")
    logger.info("  - get_logs_for_user(user_id: int, ...)")
    logger.info("  - clear_old_logs(before_timestamp: datetime)")
    logger.info("TODO: Інтегрувати Enum 'LogLevel' для аргументу `level`.")

    logger.info(f"\n--- Репозиторій Метрик Продуктивності ({PerformanceMetricRepository.__name__}) ---")
    logger.info(f"Модель: {PerformanceMetric.__name__}, Схема створення: {PerformanceMetricCreateSchema.__name__}")
    logger.info("Специфічні методи:")
    logger.info("  - get_metrics_by_name(metric_name: str, ...)")
    logger.info("  - get_metrics_by_tag(tag_key: str, tag_value: str, ...)")
    logger.info("  - clear_old_metrics(before_timestamp: datetime)")
    logger.info("TODO: Реалізувати `get_metrics_by_tag` з урахуванням діалекту БД для JSON запитів.")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    from datetime import datetime  # Необхідно для clear_old_metrics
