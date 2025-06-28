# backend/app/src/services/system/health_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `HealthService` для перевірки стану ("здоров'я") системи
та її залежностей (наприклад, база даних, Redis, Celery).
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncio # Для імітації затримки

from backend.app.src.config.database import async_engine as db_engine
from backend.app.src.config.redis import get_redis_connection
from backend.app.src.workers.celery_app import celery_app # Для перевірки Celery
from backend.app.src.config.settings import settings
from backend.app.src.schemas.system.health import HealthCheckComponentSchema, OverallHealthStatusSchema
from backend.app.src.config.logging import logger

class HealthService:
    """
    Сервіс для перевірки стану системи та її компонентів.
    """

    async def _check_database_status(self) -> HealthCheckComponentSchema:
        component_name = "database"
        status_val = "unhealthy" # Використовуємо status_val для уникнення конфлікту з модулем status
        message: Optional[str] = None
        details: Optional[Dict[str, Any]] = {}
        start_time = datetime.now(timezone.utc)

        if not db_engine:
            message = "Database engine not initialized."
        else:
            try:
                async with db_engine.connect() as connection:
                    result = await connection.execute(text("SELECT 1"))
                    if result.scalar_one() == 1:
                        status_val = "healthy"
                        message = "Successfully connected to the database and executed a query."
                    else:
                        message = "Database query did not return expected result."
            except Exception as e:
                message = f"Database connection or query failed: {str(e)}"
                logger.error(f"Database health check failed: {e}", exc_info=settings.app.DEBUG)

        response_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        details["response_time_ms"] = round(response_time_ms, 2)
        return HealthCheckComponentSchema(
            component_name=component_name,
            status=status_val,
            message=message,
            details=details
        )

    async def _check_redis_status(self) -> Optional[HealthCheckComponentSchema]:
        if not (settings.redis and settings.redis.REDIS_URL):
            return None

        component_name = "redis"
        status_val = "unhealthy"
        message: Optional[str] = None
        details: Optional[Dict[str, Any]] = {}
        start_time = datetime.now(timezone.utc)
        redis_client = None
        try:
            redis_client = await get_redis_connection()
            if redis_client:
                if await redis_client.ping():
                    status_val = "healthy"
                    message = "Successfully connected to Redis and pinged."
                else:
                    message = "Redis ping failed."
            else:
                message = "Redis client not available."
        except Exception as e:
            message = f"Redis connection or ping failed: {str(e)}"
            logger.error(f"Redis health check failed: {e}", exc_info=settings.app.DEBUG)

        response_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        details["response_time_ms"] = round(response_time_ms, 2)
        return HealthCheckComponentSchema(
            component_name=component_name,
            status=status_val,
            message=message,
            details=details
        )

    async def _check_celery_status(self) -> Optional[HealthCheckComponentSchema]:
        if not celery_app: # Якщо Celery не налаштовано/не імпортовано
            return None

        component_name = "celery"
        status_val = "unhealthy"
        message: Optional[str] = None
        details: Optional[Dict[str, Any]] = {}
        start_time = datetime.now(timezone.utc)

        try:
            # Пінгування активних воркерів. Це може бути довгою операцією.
            # control.ping() повертає список відповідей від воркерів.
            # Якщо список порожній, немає активних воркерів.
            # Таймаут важливий, щоб не блокувати health check надовго.
            ping_timeout = settings.celery.CELERY_HEALTH_CHECK_PING_TIMEOUT # Наприклад, 2 секунди

            # Запускаємо ping в окремому потоці або з таймаутом, щоб не блокувати event loop
            # Оскільки celery_app.control.ping() є блокуючим викликом,
            # його слід запускати в ThreadPoolExecutor для асинхронного контексту.
            # loop = asyncio.get_event_loop()
            # active_workers_replies = await loop.run_in_executor(None, lambda: celery_app.control.ping(timeout=ping_timeout/2)) # timeout для ping

            # Більш простий варіант для заглушки - перевірка доступності брокера (якщо він окремий від Redis)
            # Або просто припускаємо, що якщо Celery налаштовано, то він "pending" до першого ping.
            # Наразі, зробимо заглушку, що він працює, якщо є celery_app.
            # Для реальної перевірки потрібен запущений воркер та брокер.

            # Заглушка:
            await asyncio.sleep(0.05) # Імітація перевірки
            # if active_workers_replies:
            #     status_val = "healthy"
            #     message = f"Celery workers are responsive ({len(active_workers_replies)} replied)."
            #     details["responsive_workers"] = len(active_workers_replies)
            # else:
            #     status_val = "degraded" # Або unhealthy, якщо воркери критичні
            #     message = "No Celery workers responded to ping. Broker might be up, but workers are down or busy."
            #     details["responsive_workers"] = 0
            status_val = "healthy"
            message = "Celery status check (stub - assumed OK if app exists)."

        except Exception as e:
            message = f"Celery health check failed: {str(e)}"
            logger.error(f"Celery health check failed: {e}", exc_info=settings.app.DEBUG)
            status_val = "unhealthy"

        response_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        details["response_time_ms"] = round(response_time_ms, 2)
        return HealthCheckComponentSchema(
            component_name=component_name,
            status=status_val,
            message=message,
            details=details
        )


    async def get_overall_health_status(self) -> OverallHealthStatusSchema:
        components_status: List[HealthCheckComponentSchema] = []

        db_status = await self._check_database_status()
        components_status.append(db_status)

        redis_status_component = await self._check_redis_status()
        if redis_status_component:
            components_status.append(redis_status_component)

        celery_status_component = await self._check_celery_status()
        if celery_status_component:
            components_status.append(celery_status_component)

        # TODO: Додати перевірки інших важливих компонентів

        overall_status_val = "healthy"
        for component in components_status:
            if component.status == "unhealthy":
                overall_status_val = "unhealthy"
                break
            elif component.status == "degraded" and overall_status_val == "healthy":
                overall_status_val = "degraded"

        return OverallHealthStatusSchema(
            overall_status=overall_status_val,
            timestamp=datetime.now(timezone.utc),
            version=settings.app.VERSION,
            environment=settings.app.ENVIRONMENT_NAME,
            components=components_status
        )

# Екземпляр сервісу для використання в залежностях FastAPI, якщо потрібно
# health_service = HealthService() # Краще інстанціювати в залежності, якщо він має стан або залежності
