# backend/app/src/api/v1/system/health.py
# -*- coding: utf-8 -*-
"""
API ендпоінти для перевірки "здоров'я" системи та її компонентів.

Надає більш детальну інформацію про стан системи, ніж простий "ping".
Може включати перевірку доступності бази даних, кешу, зовнішніх сервісів тощо.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

# import logging # Видалено, оскільки використовується централізований логер
from typing import List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Response, status, Depends
from pydantic import BaseModel, Field, ConfigDict

# Сервіс для виконання перевірок стану
from backend.app.src.services.system.health_check_service import HealthCheckService, ComponentHealthReport as ServiceComponentHealthReport, OverallHealthReport
# Логер з конфігурації
from backend.app.src.config.logging import logger # Використовуємо централізований логер

router = APIRouter()

# --- Pydantic схеми для відповіді ---

class HealthStatusEnum(str, Enum):
    """
    Можливі статуси стану компонента або системи загалом.
    """
    OK = "OK"  # Все гаразд
    WARNING = "WARNING"  # Є попередження, але система працює
    ERROR = "ERROR"  # Критична помилка, компонент або система не працює


class ComponentHealthResponse(BaseModel):
    """
    Схема для представлення стану окремого компонента системи.
    """
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Назва компонента, що перевіряється.") # i18n
    status: HealthStatusEnum = Field(..., description="Статус компонента.")
    details: Optional[str] = Field(None, description="Додаткова інформація про стан або помилку.") # i18n
    checked_at: datetime = Field(..., description="Час перевірки у форматі ISO UTC.")


class DetailedHealthResponse(BaseModel):
    """
    Схема для детальної відповіді про стан системи та її компонентів.
    """
    model_config = ConfigDict(from_attributes=True)

    overall_status: HealthStatusEnum = Field(..., description="Загальний агрегований статус системи.")
    timestamp: datetime = Field(..., description="Час генерації звіту у форматі ISO UTC.")
    components: List[ComponentHealthResponse] = Field(..., description="Список звітів про стан окремих компонентів.")


# --- Ендпоінт ---

@router.get(
    "/verbose",
    response_model=DetailedHealthResponse,
    summary="Детальна перевірка стану системи та її ключових компонентів", # i18n
    description="""Виконує перевірку стану основних залежностей системи, таких як база даних, кеш,
та критичні зовнішні сервіси. Повертає загальний статус системи та статус кожного компонента.
- **200 OK**: Система функціонує нормально, або є некритичні попередження (статус `WARNING`).
- **503 Service Unavailable**: Один або декілька критичних компонентів системи не працюють (статус `ERROR`).
""", # i18n
    tags=["V1 System Health"]
)
async def get_detailed_health_check(
    response: Response, # Використовуємо Response для динамічного встановлення статус-коду
    health_service: HealthCheckService = Depends() # Впровадження залежності HealthCheckService
) -> DetailedHealthResponse:
    """
    Отримує детальний звіт про стан системи.

    Звертається до `HealthCheckService` для виконання всіх необхідних перевірок
    та форматує результат відповідно до схеми `DetailedHealthResponse`.
    Динамічно встановлює HTTP статус-код: 200, якщо `overall_status` ОК або WARNING,
    та 503, якщо `overall_status` ERROR.
    """
    logger.info("Запит на детальну перевірку стану системи (/verbose).") # i18n

    # Отримуємо звіт від сервісу
    # Сервіс має повернути об'єкт, сумісний з OverallHealthReport
    # (який ми визначили як Pydantic модель в самому сервісі або як тут для відповідності)
    health_report: OverallHealthReport = await health_service.get_detailed_system_health()

    # Перетворення звітів компонентів сервісу на відповіді API
    api_component_reports: List[ComponentHealthResponse] = []
    for service_report in health_report.components:
        api_component_reports.append(
            ComponentHealthResponse(
                name=service_report.name,
                status=HealthStatusEnum(service_report.status.value), # Переконуємося, що статус є членом Enum
                details=service_report.details,
                checked_at=service_report.checked_at
            )
        )

    # Формування відповіді API
    api_response_data = DetailedHealthResponse(
        overall_status=HealthStatusEnum(health_report.overall_status.value),
        timestamp=health_report.timestamp,
        components=api_component_reports
    )

    # Встановлення HTTP статус-коду відповіді залежно від загального стану системи
    if api_response_data.overall_status == HealthStatusEnum.ERROR:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.warning(f"Детальна перевірка стану: СИСТЕМА НЕПРАЦЕЗДАТНА. Загальний статус: {api_response_data.overall_status}. Деталі: {api_component_reports}") # i18n
    elif api_response_data.overall_status == HealthStatusEnum.WARNING:
        response.status_code = status.HTTP_200_OK # Система працює, але є попередження
        logger.warning(f"Детальна перевірка стану: Є ПОПЕРЕДЖЕННЯ. Загальний статус: {api_response_data.overall_status}. Деталі: {api_component_reports}") # i18n
    else: # HealthStatusEnum.OK
        response.status_code = status.HTTP_200_OK
        logger.info(f"Детальна перевірка стану: ОК. Загальний статус: {api_response_data.overall_status}.") # i18n

    return api_response_data

# Додамо простий "ping" ендпоінт для базової перевірки доступності сервісу
@router.get(
    "/ping",
    summary="Проста перевірка доступності сервісу (Ping)", # i18n
    description="Повертає 'pong', якщо сервіс працює. Не виконує глибоких перевірок.", # i18n
    response_model=dict, # Проста відповідь
    tags=["V1 System Health"]
)
async def ping():
    """
    Простий ендпоінт для перевірки, чи сервіс запущений і відповідає.
    """
    logger.debug("Ping запит отримано.") # i18n
    return {"message": "pong"} # i18n


logger.info("Маршрутизатор для ендпоінтів перевірки стану системи API v1 (`health.router`) визначено.") # i18n
# Примітка: назва файлу health_endpoints.py, але лог повідомлення було health_endpoints.router. Виправлено на health.router.
# Також, враховуючи, що клас HealthCheckService імпортується з health_check_service.py,
# можливо, цей файл (health.py) є тим, що раніше називався health_endpoints.py.
# Назва змінної `router` є локальною для цього файлу і не конфліктує з іншими.
