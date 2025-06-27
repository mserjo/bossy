# backend/app/src/api/v1/system/monitoring.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для моніторингу системи.

Цей модуль надає API для отримання даних моніторингу системи, таких як:
- Поточне навантаження на сервер.
- Використання пам'яті та CPU.
- Кількість активних з'єднань з БД.
- Статистика по запитах до API.
- Розмір черг завдань (Celery).
- Інші метрики, важливі для оцінки стану та продуктивності системи.

Доступ до цих ендпоінтів зазвичай має лише суперкористувач або
спеціалізовані системи моніторингу (наприклад, Prometheus).
Формат відповіді може бути адаптований для таких систем (наприклад, формат Prometheus).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import Any # Dict більше не потрібен тут, якщо є схема
# BaseModel не потрібен, якщо схема імпортується
import psutil # Для отримання системних метрик (приклад)
import time

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.system.monitoring import SystemMetricsSchema # Імпортуємо реальну схему
# TODO: Якщо є MonitoringService, його можна імпортувати
# from backend.app.src.services.system.monitoring_service import MonitoringService
from backend.app.src.api.dependencies import CurrentSuperuser # Або CurrentSuperuserOrMonitoringKey
from backend.app.src.models.auth.user import UserModel # Для type hint current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/metrics", # Скоротив шлях, бо він вже буде під /system/monitor/metrics
    response_model=SystemMetricsSchema,
    tags=["System", "Monitoring"],
    summary="Отримати базові системні метрики",
)
async def get_system_metrics(
    current_user: UserModel = Depends(CurrentSuperuser) # Або CurrentSuperuserOrMonitoringKey
):
    """
    Повертає базові метрики системи (CPU, пам'ять, диск, аптайм).
    Доступно суперкористувачам або за спеціальним ключем моніторингу.
    """
    logger.info(f"Користувач {current_user.email} запитує системні метрики.")
    # TODO: Якщо є MonitoringService, логіку збору метрик краще винести туди.
    # monitoring_service = MonitoringService()
    # metrics = await monitoring_service.get_psutil_metrics()
    # return metrics
    try:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        vm = psutil.virtual_memory()
        gb = 1024 * 1024 * 1024 # bytes in gigabyte

        metrics = SystemMetricsSchema(
            cpu_usage_percent=cpu_usage,
            memory_usage_percent=vm.percent,
            virtual_memory_total_gb=round(vm.total / gb, 2),
            virtual_memory_available_gb=round(vm.available / gb, 2),
            virtual_memory_used_gb=round(vm.used / gb, 2),
            disk_usage_percent=psutil.disk_usage('/').percent,
            disk_total_gb=round(psutil.disk_usage('/').total / gb, 2),
            disk_free_gb=round(psutil.disk_usage('/').free / gb, 2),
            disk_used_gb=round(psutil.disk_usage('/').used / gb, 2),
            uptime_seconds=time.time() - psutil.boot_time(),
            # Додайте інші поля, якщо вони є в SystemMetricsSchema
        )
        return metrics
    except Exception as e:
        logger.error(f"Помилка при отриманні системних метрик: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не вдалося отримати системні метрики: {str(e)}"
        )

@router.get(
    "/prometheus", # Скоротив шлях
    tags=["System", "Monitoring"],
    summary="Отримати метрики у форматі Prometheus",
    response_class=Response # Встановлюємо media_type напряму у Response
)
async def get_prometheus_metrics(
    current_user: UserModel = Depends(CurrentSuperuser) # Або CurrentSuperuserOrMonitoringKey
):
    """
    Повертає метрики системи у форматі, сумісному з Prometheus.
    Доступно суперкористувачам або за спеціальним ключем моніторингу.
    """
    logger.info(f"Користувач {current_user.email} запитує метрики у форматі Prometheus.")
    # TODO: Реалізувати збір та форматування метрик для Prometheus.
    # Це може включати використання клієнтської бібліотеки Prometheus (наприклад, prometheus_client)
    # та реєстрацію кастомних колекторів або метрик в MonitoringService.
    # monitoring_service = MonitoringService()
    # prometheus_data = await monitoring_service.get_prometheus_formatted_metrics()
    # return Response(content=prometheus_data, media_type="text/plain; version=0.0.4; charset=utf-8")

    # Заглушка, як і раніше, але з використанням psutil
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        prometheus_output = (
            f"# HELP system_cpu_usage_percent Використання CPU у відсотках\n"
            f"# TYPE system_cpu_usage_percent gauge\n"
            f"system_cpu_usage_percent {cpu}\n"
            f"# HELP system_memory_usage_percent Використання пам'яті у відсотках\n"
            f"# TYPE system_memory_usage_percent gauge\n"
            f"system_memory_usage_percent {mem}\n"
        )
        return Response(content=prometheus_output, media_type="text/plain; version=0.0.4; charset=utf-8")
    except Exception as e:
        logger.error(f"Помилка при генерації Prometheus метрик: {e}", exc_info=True)
        return Response(content=f"# Error generating metrics: {e}\n",
                        media_type="text/plain; version=0.0.4; charset=utf-8",
                        status_code=500)


# TODO: Додати ендпоінти для отримання специфічних даних моніторингу,
# наприклад, стан черг Celery, статистика по API запитах, логи тощо.

# Роутер буде підключений в backend/app/src/api/v1/system/__init__.py
# або безпосередньо в backend/app/src/api/v1/router.py
