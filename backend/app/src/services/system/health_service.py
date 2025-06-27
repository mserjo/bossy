# backend/app/src/services/system/health_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `HealthService` для перевірки стану ("здоров'я") системи
та її залежностей (наприклад, база даних, Redis).
"""
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy import text # type: ignore

from backend.app.src.config.database import async_engine as db_engine # Прямий доступ до engine для ping
from backend.app.src.config.redis import get_redis_connection # Для перевірки Redis
from backend.app.src.config.settings import settings # Для отримання версії додатку
from backend.app.src.schemas.system.health import HealthCheckComponentSchema, OverallHealthStatusSchema
from backend.app.src.config.logging import logger

class HealthService:
    """
    Сервіс для перевірки стану системи та її компонентів.
    """

    async def _check_database_status(self) -> HealthCheckComponentSchema:
        """Перевіряє стан підключення до бази даних."""
        component_name = "database"
        status = "unhealthy"
        message: Optional[str] = None
        start_time = datetime.utcnow()

        if not db_engine:
            message = "Database engine not initialized."
        else:
            try:
                async with db_engine.connect() as connection:
                    await connection.execute(text("SELECT 1"))
                status = "healthy"
                message = "Successfully connected to the database."
            except Exception as e:
                message = f"Database connection failed: {str(e)}"
                logger.error(f"Database health check failed: {e}", exc_info=settings.app.DEBUG)

        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return HealthCheckComponentSchema(
            component_name=component_name,
            status=status,
            message=message
            # response_time_ms=round(response_time_ms, 2) # Можна додати
        )

    async def _check_redis_status(self) -> Optional[HealthCheckComponentSchema]:
        """Перевіряє стан підключення до Redis, якщо Redis налаштовано."""
        if not (settings.redis and settings.redis.REDIS_URL):
            return None # Redis не налаштований, не включаємо в перевірку

        component_name = "redis"
        status = "unhealthy"
        message: Optional[str] = None
        start_time = datetime.utcnow()

        redis_client = None
        try:
            redis_client = await get_redis_connection() # Отримуємо клієнт/пул
            if redis_client:
                await redis_client.ping()
                status = "healthy"
                message = "Successfully connected to Redis."
            else:
                message = "Redis client not available (not configured or connection failed at startup)."
        except Exception as e:
            message = f"Redis connection failed: {str(e)}"
            logger.error(f"Redis health check failed: {e}", exc_info=settings.app.DEBUG)
        # finally: # Закривати з'єднання з пулу тут не потрібно, якщо get_redis_connection керує цим.
        #     if redis_client and hasattr(redis_client, 'close') and not hasattr(redis_client, 'is_closed') or not redis_client.is_closed():
        #         # Якщо це було одноразове з'єднання, а не з пулу, його треба закрити.
        #         # Але get_redis_connection повертає клієнта, що керує пулом.
        #         pass

        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return HealthCheckComponentSchema(
            component_name=component_name,
            status=status,
            message=message
            # response_time_ms=round(response_time_ms, 2)
        )

    # TODO: Додати методи для перевірки інших критичних компонентів:
    # - Celery workers (наприклад, через `celery_app.control.ping()` або перевірку активних воркерів)
    # - Зовнішні API, від яких залежить система (якщо є)
    # - Файлове сховище (якщо використовується зовнішнє)

    async def get_overall_health_status(self, db: AsyncSession) -> OverallHealthStatusSchema: # db може бути не потрібен, якщо перевірки не взаємодіють з сесією
        """
        Збирає інформацію про стан всіх основних компонентів системи.
        """
        components_status: List[HealthCheckComponentSchema] = []

        # 1. Перевірка бази даних
        db_status = await self._check_database_status()
        components_status.append(db_status)

        # 2. Перевірка Redis (якщо налаштовано)
        redis_status_component = await self._check_redis_status()
        if redis_status_component:
            components_status.append(redis_status_component)

        # 3. TODO: Перевірка інших компонентів (Celery, etc.)
        # components_status.append(await self._check_celery_status())

        # Визначення загального стану системи
        overall_status = "healthy"
        for component in components_status:
            if component.status == "unhealthy":
                overall_status = "unhealthy"
                break # Якщо хоча б один нездоровий, вся система нездорова
            elif component.status == "degraded":
                overall_status = "degraded" # Деградований - гірше, ніж здоровий, але краще, ніж нездоровий

        return OverallHealthStatusSchema(
            overall_status=overall_status,
            timestamp=datetime.utcnow(),
            # version=settings.app.VERSION, # Якщо є версія в налаштуваннях
            # environment=settings.app.ENVIRONMENT, # Якщо є середовище в налаштуваннях
            components=components_status
        )

health_service = HealthService()

# Примітки:
# - Цей сервіс не успадковує `BaseService` і не має репозиторію,
#   оскільки він виконує динамічні перевірки, а не CRUD операції з моделлю "Health".
#   Якщо б результати перевірок зберігалися в `ServiceHealthStatusModel`,
#   тоді цей сервіс міг би використовувати `ServiceHealthStatusRepository`.
# - Методи перевірки (`_check_database_status`, `_check_redis_status`) є приватними.
# - `get_overall_health_status` агрегує результати.
# - Логування помилок важливе для діагностики.
# - TODO вказують на місця для розширення (перевірка Celery тощо).
# - `db: AsyncSession` в `get_overall_health_status` може бути непотрібним, якщо всі
#   перевірки використовують власні механізми підключення (як `db_engine` або `get_redis_connection`).
#   Я залишив його, якщо якась перевірка в майбутньому потребуватиме сесії.
#
# Все виглядає як хороший початок для HealthService.
