# backend/app/src/api/v1/system/monitoring.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для моніторингу системи API v1.

Ці ендпоінти призначені для суперкористувачів та дозволяють
отримувати інформацію про стан системи, логи, метрики тощо.
"""

import asyncio # Додано для FakeSystemMonitoringService
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime # Для прикладу timestamp в логах/метриках

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator

# Залежності API (для автентифікації/авторизації)
# У реальному проекті: from app.src.api.dependencies import get_current_active_superuser
from app.src.api.dependencies import _fake_user_service # Використовуємо заглушку для тестування

# Сервіси для отримання даних моніторингу (будуть реалізовані пізніше в src/services/)
# from app.src.services.system.monitoring_service import SystemMonitoringService

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Pydantic моделі для відповідей моніторингу (приклади) ---

class LogEntrySchema(BaseModel):
    timestamp: datetime = Field(..., example=datetime.utcnow())
    level: str = Field(..., example="INFO")
    logger_name: Optional[str] = Field(None, example="app.src.services.user_service")
    message: str = Field(..., example="User 'john_doe' logged in successfully.")
    # Можуть бути додаткові поля: trace_id, user_id, exc_info (структуроване) тощо.

class PaginatedLogResponse(BaseModel):
    total_items: int = Field(..., alias="totalLogs", example=150) # Використання alias для JSON поля
    logs: List[LogEntrySchema]
    page: int = Field(..., example=1)
    size: int = Field(..., example=50)
    total_pages: Optional[int] = Field(None, alias="totalPages", example=3)

    @validator('total_pages', always=True)
    def calculate_total_pages(cls, v, values):
        if 'total_items' in values and 'size' in values and values['size'] > 0:
            return (values['total_items'] + values['size'] - 1) // values['size']
        return None


class SystemMetricSchema(BaseModel):
    name: str = Field(..., example="cpu_utilization_percent")
    value: Any = Field(..., example=75.5)
    unit: Optional[str] = Field(None, example="%")
    timestamp: Optional[datetime] = Field(None, example=datetime.utcnow())
    tags: Optional[Dict[str, str]] = Field(None, description="Додаткові теги/мітки для метрики", example={"core": "1", "type": "user_load"})


# --- Заглушка для сервісу моніторингу ---
class FakeSystemMonitoringService:
    """Імітує сервіс для отримання даних моніторингу."""
    def __init__(self):
        # Створення більшого набору логів для кращої імітації пагінації та фільтрації
        self._all_logs_stub: List[LogEntrySchema] = []
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        loggers = ["auth_service", "user_service", "task_processor", "payment_gateway", "system_events"]
        messages = [
            "User login attempt for '{}'.", "Profile updated by admin for user '{}'.",
            "Task '{}' started.", "Task '{}' completed successfully.", "Task '{}' failed due to {}.",
            "Payment transaction '{}' initiated.", "Payment for '{}' succeeded.", "Payment for '{}' failed: {}.",
            "System scheduled job '{}' executed.", "Configuration reloaded.", "High CPU usage detected: {}%",
            "Low disk space warning on /var: {}% free.", "User '{}' password reset requested.",
            "API endpoint '{}' called with params: {}"
        ]

        current_time = datetime.utcnow()
        for i in range(250): # Створюємо 250 логів
            ts = current_time - timedelta(minutes=i * 5) # Різний час
            level = levels[i % len(levels)]
            logger_name = loggers[i % len(loggers)]
            # Формування повідомлення з динамічними частинами
            msg_template = messages[i % len(messages)]
            if "{}" in msg_template:
                if msg_template.count("{}") == 1:
                    msg = msg_template.format(f"item_{i}")
                elif msg_template.count("{}") == 2:
                     msg = msg_template.format(f"item_{i}", f"detail_{i}")
                else: # Більше двох плейсхолдерів
                     msg = msg_template.format(f"item_{i}", f"detail_{i}", f"extra_{i}")
            else:
                msg = msg_template

            self._all_logs_stub.append(LogEntrySchema(timestamp=ts, level=level, logger_name=logger_name, message=msg))


    async def get_system_logs(
        self,
        page: int = 1,
        size: int = 50,
        level_filter: Optional[str] = None,
        search_query: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> PaginatedLogResponse:
        logger.debug(
            f"FakeSystemMonitoringService: Запит логів (стор: {page}, розмір: {size}, "
            f"рівень: {level_filter}, пошук: '{search_query}', час від: {start_time}, час до: {end_time})."
        )
        await asyncio.sleep(0.02) # Імітація IO

        temp_logs = self._all_logs_stub

        if level_filter:
            temp_logs = [log for log in temp_logs if log.level.lower() == level_filter.lower()]
        if search_query:
            temp_logs = [log for log in temp_logs if search_query.lower() in log.message.lower() or (log.logger_name and search_query.lower() in log.logger_name.lower())]
        if start_time:
            temp_logs = [log for log in temp_logs if log.timestamp >= start_time]
        if end_time:
            temp_logs = [log for log in temp_logs if log.timestamp <= end_time]

        total_items = len(temp_logs)
        start_index = (page - 1) * size
        end_index = start_index + size
        paginated_logs_for_page = temp_logs[start_index:end_index]

        return PaginatedLogResponse(
            totalLogs=total_items, # Використовуємо alias
            logs=paginated_logs_for_page,
            page=page,
            size=len(paginated_logs_for_page) # Реальний розмір поточної сторінки
        )

    async def get_current_system_metrics(self) -> List[SystemMetricSchema]:
        logger.debug("FakeSystemMonitoringService: Запит поточних системних метрик.")
        await asyncio.sleep(0.01)
        # Ці метрики могли б збиратися фоновим завданням (SystemMetricsCollectorTask)
        # і зберігатися в кеші або часовій БД (наприклад, Prometheus, InfluxDB) для швидкого доступу.
        ts = datetime.utcnow()
        return [
            SystemMetricSchema(name="cpu_load_avg_1min", value=round(0.1 + (ts.second % 60) * 0.01, 2), unit="load", timestamp=ts),
            SystemMetricSchema(name="cpu_load_avg_5min", value=round(0.2 + (ts.second % 60) * 0.005, 2), unit="load", timestamp=ts),
            SystemMetricSchema(name="memory_usage_mb", value= (1024 + (ts.second % 60) * 10), unit="MB", timestamp=ts),
            SystemMetricSchema(name="memory_usage_percent", value=round(40.0 + (ts.second % 60) * 0.2, 1), unit="%", timestamp=ts),
            SystemMetricSchema(name="active_db_connections", value=(10 + (ts.second % 10)), unit="connections", timestamp=ts),
            SystemMetricSchema(name="pending_background_tasks", value=(ts.second % 5), unit="tasks", timestamp=ts),
            SystemMetricSchema(name="disk_space_usage_percent", value=round(60.0 + (ts.minute%10)*0.1,1), unit="%", tags={"volume": "/app_data"}, timestamp=ts),
        ]

_fake_monitoring_service_instance = FakeSystemMonitoringService()

# --- Імітація залежності get_current_active_superuser ---
async def get_current_active_superuser_stub(token: str = "valid_superuser_token") -> Dict[str, Any]:
    """Заглушка для залежності, що перевіряє права суперкористувача."""
    user = await _fake_user_service.get_user_by_id("superuser_id") # Використовуємо заглушку з api.dependencies
    if not user or not user.get("is_active") or not user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Потрібні права суперкористувача (локальна заглушка).")
    return user

# --- Ендпоінти ---

@router.get(
    "/logs",
    response_model=PaginatedLogResponse,
    summary="Отримати системні логи з пагінацією та фільтрацією",
    response_description="Повертає список системних логів з можливістю фільтрації за рівнем, пошуку за текстом та вибору часового діапазону.",
    dependencies=[Depends(get_current_active_superuser_stub)],
    tags=["V1 System Monitoring & Logs"]
)
async def get_system_logs(
    page: int = Query(1, ge=1, description="Номер сторінки результатів."),
    size: int = Query(50, ge=1, le=200, description="Кількість записів логу на сторінці."),
    level: Optional[str] = Query(None, description="Фільтр за рівнем логування (наприклад, INFO, WARNING, ERROR). Регістронезалежний.", examples=["ERROR", "info"]),
    search: Optional[str] = Query(None, min_length=2, max_length=100, description="Пошуковий запит по тексту повідомлення логу або назві логера."),
    start_time: Optional[datetime] = Query(None, description="Початковий час для фільтрації логів (ISO формат, наприклад, 2023-10-27T00:00:00Z)."),
    end_time: Optional[datetime] = Query(None, description="Кінцевий час для фільтрації логів (ISO формат).")
    # У реальному проекті: monitoring_service: SystemMonitoringService = Depends(get_monitoring_service)
):
    """
    Дозволяє суперкористувачам переглядати системні логи.
    Підтримує пагінацію, фільтрацію за рівнем, пошук за текстом та часовим діапазоном.
    """
    logger.info(f"Запит системних логів: стор={page}, розмір={size}, рівень='{level}', пошук='{search}', від='{start_time}', до='{end_time}'.")
    # log_data = await monitoring_service.get_system_logs(page=page, size=size, level_filter=level, search_query=search, start_time=start_time, end_time=end_time)
    log_data = await _fake_monitoring_service_instance.get_system_logs(
        page=page, size=size, level_filter=level, search_query=search, start_time=start_time, end_time=end_time
    )
    return log_data

@router.get(
    "/metrics",
    response_model=List[SystemMetricSchema],
    summary="Отримати поточні системні метрики",
    response_description="Повертає список поточних ключових метрик системи.",
    dependencies=[Depends(get_current_active_superuser_stub)],
    tags=["V1 System Monitoring & Metrics"]
)
async def get_system_metrics(
    # У реальному проекті: monitoring_service: SystemMonitoringService = Depends(get_monitoring_service)
):
    """
    Дозволяє суперкористувачам переглядати поточні системні метрики.
    Метрики можуть включати завантаження CPU, використання пам'яті,
    кількість активних з'єднань з БД, розмір черг завдань тощо.
    """
    logger.info("Запит поточних системних метрик.")
    # metrics = await monitoring_service.get_current_system_metrics() # Реальний виклик
    metrics = await _fake_monitoring_service_instance.get_current_system_metrics() # Використання заглушки
    return metrics

# Коментар для розробника:
# Не забути оновити `backend/app/src/api/v1/system/__init__.py`, щоб підключити цей `router`.
# Наприклад, додати в __init__.py:
#
# from .monitoring import router as monitoring_router
# system_router.include_router(monitoring_router, prefix="/monitoring", tags=["V1 System Monitoring"])
# (Теги тут можуть бути більш специфічними, або успадковуватися/доповнюватися з system_router)

logger.info("Модуль API v1 System Monitoring (`monitoring.py`) завантажено.")
