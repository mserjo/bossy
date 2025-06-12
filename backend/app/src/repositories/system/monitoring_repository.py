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
from backend.app.src.config import logger  # Використання спільного логера

# Абсолютний імпорт моделей та схем
from backend.app.src.models.system.monitoring import SystemLog, PerformanceMetric
from backend.app.src.schemas.system.monitoring import (
    SystemLogCreateSchema,
    PerformanceMetricCreateSchema
)


# TODO: [Enum Integration] Імпортувати Enums, наприклад, LogLevel,
#       ймовірно з `backend.app.src.core.enums` або аналогічного місця,
#       згідно з `technical_task.txt` / `structure-claude-v2.md`.
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

    def __init__(self):
        super().__init__(model=SystemLog)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_logs_by_level(
            self,
            session: AsyncSession,
            level: str,  # Очікується значення з LogLevel Enum
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[SystemLog], int]:
        """
        Отримує логи за вказаним рівнем.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            level (str): Рівень логу.
                         # TODO: [Enum Validation] Використовувати LogLevelEnum.LEVEL.value для порівняння.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[SystemLog], int]: Кортеж зі списком логів та їх загальною кількістю.
        """
        logger.debug(f"Отримання логів за рівнем: {level}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"level": level}
        sort_by_field = "timestamp"
        sort_order_str = "desc"
        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict,
                sort_by=sort_by_field, sort_order=sort_order_str
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} логів за рівнем: {level}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні логів за рівнем {level}: {e}", exc_info=True)
            return [], 0

    async def get_logs_by_source(
            self,
            session: AsyncSession,
            source: str,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[SystemLog], int]:
        """
        Отримує логи за вказаним джерелом.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            source (str): Джерело логу.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[SystemLog], int]: Кортеж зі списком логів та їх загальною кількістю.
        """
        logger.debug(f"Отримання логів за джерелом: {source}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"source": source}
        sort_by_field = "timestamp"
        sort_order_str = "desc"
        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict,
                sort_by=sort_by_field, sort_order=sort_order_str
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} логів за джерелом: {source}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні логів за джерелом {source}: {e}", exc_info=True)
            return [], 0

    async def get_logs_for_user(
            self,
            session: AsyncSession,
            user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[SystemLog], int]:
        """
        Отримує логи, пов'язані з конкретним користувачем.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[SystemLog], int]: Кортеж зі списком логів та їх загальною кількістю.
        """
        logger.debug(f"Отримання логів для user_id: {user_id}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"user_id": user_id}
        sort_by_field = "timestamp"
        sort_order_str = "desc"
        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict,
                sort_by=sort_by_field, sort_order=sort_order_str
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} логів для user_id: {user_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні логів для user_id {user_id}: {e}", exc_info=True)
            return [], 0

    async def clear_old_logs(self, session: AsyncSession, before_timestamp: datetime) -> int:
        """
        Видаляє старі записи логів до вказаної дати.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            before_timestamp (datetime): Часова мітка, до якої потрібно видалити логи.

        Returns:
            int: Кількість видалених записів.
        """
        logger.info(f"Видалення старих логів до {before_timestamp}")
        stmt = sqlalchemy_delete(self.model).where(self.model.timestamp < before_timestamp)
        try:
            async with session.begin_nested() if session.in_transaction() else session.begin():
                result = await session.execute(stmt)
            rowcount = result.rowcount
            logger.info(f"Видалено {rowcount} старих записів логів.")
            return rowcount
        except Exception as e:
            logger.error(f"Помилка при видаленні старих логів: {e}", exc_info=True)
            return 0


class PerformanceMetricRepository(
    BaseRepository[PerformanceMetric, PerformanceMetricCreateSchema, PerformanceMetricUpdateSchema]):
    """
    Репозиторій для управління метриками продуктивності (`PerformanceMetric`).

    Успадковує базові CRUD-методи. Надає методи для фільтрації метрик
    за назвою або тегами.
    """

    def __init__(self):
        super().__init__(model=PerformanceMetric)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_metrics_by_name(
            self,
            session: AsyncSession,
            metric_name: str,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[PerformanceMetric], int]:
        """
        Отримує метрики за вказаною назвою.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            metric_name (str): Назва метрики.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[PerformanceMetric], int]: Кортеж зі списком метрик та їх загальною кількістю.
        """
        logger.debug(f"Отримання метрик за назвою: {metric_name}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"metric_name": metric_name}
        sort_by_field = "timestamp"
        sort_order_str = "desc"
        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict,
                sort_by=sort_by_field, sort_order=sort_order_str
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} метрик за назвою: {metric_name}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні метрик за назвою {metric_name}: {e}", exc_info=True)
            return [], 0

    async def get_metrics_by_tag(
            self,
            session: AsyncSession,
            tag_key: str,
            tag_value: str,
            skip: int = 0,
            limit: int = 100
    # ) -> Tuple[List[PerformanceMetric], int]: # Повернемо List, оскільки count буде неточним без SQL-фільтра
    ) -> List[PerformanceMetric]: # Або Tuple, якщо буде реалізовано точний count
        """
        Отримує метрики, що містять вказаний тег (ключ-значення).
        Потребує підтримки JSON операторів на рівні БД (наприклад, PostgreSQL JSONB).
        Поточна реалізація є заглушкою і потребує доопрацювання.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            tag_key (str): Ключ тегу.
            tag_value (str): Значення тегу.
            skip (int): Кількість записів для пропуску (застосовується після фільтрації в Python, якщо така є).
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            List[PerformanceMetric]: Список метрик.
        """
        logger.debug(f"Отримання метрик за тегом: {tag_key}={tag_value}, skip: {skip}, limit: {limit}")
        # TODO: [DB Specific JSON Query] Адаптувати запит для конкретного діалекту БД та типу JSON поля.
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
        logger.warning(
            "Метод get_metrics_by_tag викликано, але він потребує специфічної для БД реалізації JSON-запиту. "
            "Наразі він не виконує фільтрацію за тегами належним чином."
        )

        # Повертаємо помилку, що метод не реалізовано належним чином для SQL-фільтрації.
        # Альтернативно, можна було б завантажити всі метрики і фільтрувати в Python,
        # але це було б дуже неефективно і не рекомендовано для великих обсягів даних.
        # Для прикладу, як це могло б виглядати (НЕ ДЛЯ ПРОДАкШЕНУ без SQL фільтра):
        # if True: # Заглушка, щоб код був валідним
        #     all_metrics_tuple = await super().get_multi(session=session, skip=0, limit=100000) # Дуже погано
        #     all_metrics = all_metrics_tuple[0] # get_multi повертає List, не Tuple
        #     filtered_items = [
        #         item for item in all_metrics
        #         if isinstance(item.tags, dict) and item.tags.get(tag_key) == tag_value
        #     ]
        #     # paginated_items = filtered_items[skip : skip + limit]
        #     # return paginated_items, len(filtered_items) # Якщо повертати Tuple
        #     return filtered_items[skip : skip + limit]

        raise NotImplementedError(
            "Пошук за тегами в JSON потребує специфічної для БД реалізації або іншої стратегії зберігання тегів."
        )

    async def clear_old_metrics(self, session: AsyncSession, before_timestamp: datetime) -> int:
        """
        Видаляє старі записи метрик до вказаної дати.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            before_timestamp (datetime): Часова мітка, до якої потрібно видалити метрики.

        Returns:
            int: Кількість видалених записів.
        """
        logger.info(f"Видалення старих метрик до {before_timestamp}")
        stmt = sqlalchemy_delete(self.model).where(self.model.timestamp < before_timestamp)
        try:
            async with session.begin_nested() if session.in_transaction() else session.begin():
                result = await session.execute(stmt)
            rowcount = result.rowcount
            logger.info(f"Видалено {rowcount} старих записів метрик.")
            return rowcount
        except Exception as e:
            logger.error(f"Помилка при видаленні старих метрик: {e}", exc_info=True)
            return 0
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
