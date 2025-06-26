# backend/app/src/repositories/system/health.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `ServiceHealthStatusModel`.
Надає методи для збереження та отримання історії статусів "здоров'я" компонентів системи.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.system.health import ServiceHealthStatusModel
from backend.app.src.schemas.system.health import ServiceHealthStatusCreateSchema # UpdateSchema зазвичай не потрібна
from backend.app.src.repositories.base import BaseRepository
from pydantic import BaseModel as PydanticBaseModel # Заглушка для UpdateSchemaType

class ServiceHealthStatusRepository(BaseRepository[ServiceHealthStatusModel, ServiceHealthStatusCreateSchema, PydanticBaseModel]): # UpdateSchemaType - заглушка
    """
    Репозиторій для роботи з моделлю історії статусів "здоров'я" сервісів (`ServiceHealthStatusModel`).
    """

    async def get_latest_status_for_component(
        self, db: AsyncSession, *, component_name: str
    ) -> Optional[ServiceHealthStatusModel]:
        """
        Отримує останній записаний статус для вказаного компонента.
        """
        statement = select(self.model).where(
            self.model.component_name == component_name
        ).order_by(self.model.created_at.desc()) # type: ignore # `created_at` використовується як `checked_at`
        result = await db.execute(statement)
        return result.scalars().first()

    async def get_status_history_for_component(
        self, db: AsyncSession, *, component_name: str,
        limit: int = 100, # Обмеження кількості записів історії
        time_since: Optional[datetime] = None # Історія з певного часу
    ) -> List[ServiceHealthStatusModel]:
        """
        Отримує історію статусів для вказаного компонента.
        """
        statement = select(self.model).where(self.model.component_name == component_name)
        if time_since:
            statement = statement.where(self.model.created_at >= time_since) # type: ignore

        statement = statement.order_by(self.model.created_at.desc()).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def delete_old_statuses(
        self, db: AsyncSession, *, older_than_days: int
    ) -> int:
        """
        Видаляє старі записи історії статусів, старші за вказану кількість днів.
        """
        threshold_date = datetime.utcnow() - timedelta(days=older_than_days)
        statement = delete(self.model).where(self.model.created_at < threshold_date) # type: ignore
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore

    # `create` успадкований. `ServiceHealthStatusCreateSchema` використовується.
    # Записи про стан зазвичай не оновлюються, а створюються нові.
    # Тому `update` та `delete` для окремих записів можуть не використовуватися часто.

service_health_status_repository = ServiceHealthStatusRepository(ServiceHealthStatusModel)

# TODO: Переконатися, що `ServiceHealthStatusCreateSchema` відповідає потребам.
#       (має `component_name`, `status`, `details`).
#
# Все виглядає добре. Надано методи для отримання історії та останнього статусу,
# а також для очищення старих записів.
# Це корисно, якщо Health Check API буде не тільки динамічним, але й зберігатиме
# результати періодичних перевірок для моніторингу та аналізу.
