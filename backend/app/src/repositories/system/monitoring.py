# backend/app/src/repositories/system/monitoring.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `SystemEventLogModel`.
Надає методи для збереження та отримання системних логів/подій.
"""

from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.system.monitoring import SystemEventLogModel
from backend.app.src.schemas.system.monitoring import SystemEventLogCreateSchema
from backend.app.src.repositories.base import BaseRepository
from pydantic import BaseModel as PydanticBaseModel # Заглушка для UpdateSchemaType

class SystemEventLogRepository(BaseRepository[SystemEventLogModel, SystemEventLogCreateSchema, PydanticBaseModel]): # UpdateSchemaType - заглушка
    """
    Репозиторій для роботи з моделлю системних логів/подій (`SystemEventLogModel`).
    Логи зазвичай лише створюються і не оновлюються.
    """

    async def get_logs(
        self, db: AsyncSession, *,
        level: Optional[str] = None,
        logger_name: Optional[str] = None,
        source_component: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        message_contains: Optional[str] = None,
        skip: int = 0, limit: int = 1000 # Більший ліміт для логів за замовчуванням
    ) -> List[SystemEventLogModel]:
        """
        Отримує список логів з можливістю фільтрації.
        """
        statement = select(self.model)
        conditions = []
        if level:
            conditions.append(self.model.level == level.upper())
        if logger_name:
            conditions.append(self.model.logger_name.ilike(f"%{logger_name}%")) # type: ignore
        if source_component:
            conditions.append(self.model.source_component == source_component)
        if user_id:
            conditions.append(self.model.user_id == user_id)
        if date_from:
            conditions.append(self.model.created_at >= date_from) # type: ignore
        if date_to:
            conditions.append(self.model.created_at < (date_to + timedelta(days=1))) # type: ignore
        if message_contains:
            conditions.append(self.model.message.ilike(f"%{message_contains}%")) # type: ignore

        if conditions:
            statement = statement.where(and_(*conditions))

        statement = statement.order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        # Не завантажуємо зв'язки за замовчуванням для швидкості

        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def delete_old_logs(
        self, db: AsyncSession, *, older_than_days: int
    ) -> int:
        """
        Видаляє старі записи логів, старші за вказану кількість днів.
        """
        threshold_date = datetime.utcnow() - timedelta(days=older_than_days)
        statement = delete(self.model).where(self.model.created_at < threshold_date) # type: ignore
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore

    # `create` успадкований. `SystemEventLogCreateSchema` використовується.
    # `update` та `delete` для окремих логів зазвичай не потрібні.

system_event_log_repository = SystemEventLogRepository(SystemEventLogModel)

# TODO: Переконатися, що `SystemEventLogCreateSchema` відповідає потребам.
#       (має `level`, `message` та опціональні `logger_name`, `source_component` тощо).
#
# TODO: Розглянути можливість використання `textual_sql` для більш складних пошукових запитів
#       по полю `details` (JSONB), якщо це буде потрібно.
#
# Все виглядає добре. Надано методи для отримання логів з фільтрацією та для очищення старих записів.
# Це важливо для підтримки та моніторингу системи.
