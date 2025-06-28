# backend/app/src/services/system/monitoring_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `SystemEventLogService` для управління системними логами/подіями.
Він відповідає за запис структурованих логів в базу даних та їх отримання.
Для моніторингу метрик системи (CPU, пам'ять) див. `HealthService` або окремий сервіс метрик.
"""
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.models.system.monitoring import SystemEventLogModel
from backend.app.src.schemas.system.monitoring import SystemEventLogCreateSchema, SystemEventLogSchema
from backend.app.src.repositories.system.monitoring_repository import SystemEventLogRepository # Змінено імпорт
from backend.app.src.repositories.auth.user_repository import UserRepository # Для перевірки user_id
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, BadRequestException
from backend.app.src.config.logging import logger
from backend.app.src.schemas.base import PaginatedResponse # Для типізації відповіді

class SystemEventLogService(BaseService[SystemEventLogRepository]):
    """
    Сервіс для управління системними логами/подіями.
    """
    def __init__(self, db_session: AsyncSession):
        super().__init__(SystemEventLogRepository(db_session)) # Ініціалізуємо репозиторій з сесією
        self.user_repo = UserRepository(db_session) # Для перевірки існування користувача

    async def log_event(self, *, obj_in: SystemEventLogCreateSchema) -> SystemEventLogModel:
        """
        Записує нову подію/лог в систему.
        """
        if obj_in.user_id:
            user = await self.user_repo.get(id=obj_in.user_id)
            if not user:
                logger.warning(f"Спроба записати лог для неіснуючого користувача ID: {obj_in.user_id}. user_id буде встановлено в NULL.")
                obj_in.user_id = None

        # Встановлюємо created_at, якщо воно не передано (хоча модель має default)
        if obj_in.created_at is None:
            obj_in.created_at = datetime.now(timezone.utc)
        elif obj_in.created_at.tzinfo is None: # Переконуємося, що час aware
             obj_in.created_at = obj_in.created_at.replace(tzinfo=timezone.utc)

        new_log_entry = await self.repository.create(obj_in=obj_in)
        logger.debug(f"Записано новий системний лог ID: {new_log_entry.id}, Рівень: {new_log_entry.level}")
        return new_log_entry

    async def get_logs_paginated(
        self, *,
        page: int = 1,
        page_size: int = 100,
        level: Optional[str] = None,
        logger_name: Optional[str] = None,
        source_component: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        message_contains: Optional[str] = None,
        order_by: Optional[List[str]] = None
    ) -> PaginatedResponse[SystemEventLogSchema]:
        """
        Отримує список логів з пагінацією та фільтрацією.
        """
        if not order_by:
            order_by = ["-created_at"]

        # TODO: Доопрацювати BaseRepository або створити спеціалізований метод в SystemEventLogRepository
        #       для підтримки всіх фільтрів (__ilike, __ge, __lt) та коректного підрахунку total.
        #       Поточний get_paginated_with_filters в BaseRepository може не підтримувати все.

        # Формування фільтрів для передачі в репозиторій
        filters: Dict[str, Any] = {}
        if level: filters["level"] = level.upper()
        if logger_name: filters["logger_name__ilike"] = f"%{logger_name}%"
        if source_component: filters["source_component__ilike"] = f"%{source_component}%" # Припускаємо ilike
        if user_id: filters["user_id"] = user_id
        if date_from: filters["created_at__ge"] = date_from
        if date_to: filters["created_at__lt"] = date_to + timedelta(days=1) # До кінця дня
        if message_contains: filters["message__ilike"] = f"%{message_contains}%"

        logger.info(f"Запит системних логів: стор. {page}, розм. {page_size}, фільтри: {filters}, сортування: {order_by}")

        # Припускаємо, що репозиторій має метод, що підтримує ці фільтри та пагінацію
        # і повертає кортеж (items, total_count)
        # Або ж, якщо BaseRepository.get_paginated_with_filters це робить:
        # paginated_result = await self.repository.get_paginated_with_filters(
        #     skip=(page - 1) * page_size,
        #     limit=page_size,
        #     order_by_list=order_by,
        #     filters=filters
        # )
        # items = [SystemEventLogSchema.from_orm(item) for item in paginated_result.items]
        # total_items = paginated_result.total

        # ЗАГЛУШКА для пагінації з поточними можливостями (не зовсім точна)
        items_models = await self.repository.get_logs( # Припускаємо, get_logs підтримує ці фільтри
            level=level.upper() if level else None,
            logger_name=logger_name,
            source_component=source_component,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to + timedelta(days=1) if date_to else None, # +1 день для __lt
            message_contains=message_contains,
            skip=(page - 1) * page_size,
            limit=page_size,
            order_by=order_by
        )
        items = [SystemEventLogSchema.from_orm(item) for item in items_models]

        # TODO: Потрібен окремий запит для total_count з тими ж фільтрами
        # total_items = await self.repository.count_with_filters(filters=filters)
        # Поки що заглушка для total
        if page == 1 and len(items) < page_size:
            total_items = len(items)
        else:
            # Це неточний підрахунок, потрібен реальний count
            total_items = page * page_size + (1 if len(items) == page_size else 0)
            logger.warning("Підрахунок total_items для логів є приблизним. Потребує доопрацювання.")


        return PaginatedResponse[SystemEventLogSchema](
            total=total_items,
            page=page,
            size=len(items),
            items=items
        )

    async def clear_old_logs(self, *, older_than_days: int) -> int:
        """Видаляє старі логи. Повертає кількість видалених записів."""
        if older_than_days <= 0:
            raise BadRequestException("Кількість днів для видалення логів має бути позитивним числом.")

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        logger.info(f"Запит на видалення системних логів, старших за {older_than_days} днів (до {cutoff_date}).")

        deleted_count = await self.repository.delete_logs_older_than(cutoff_date=cutoff_date)
        logger.info(f"Видалено {deleted_count} старих записів системних логів.")
        return deleted_count

# Екземпляр сервісу не створюємо тут глобально.
