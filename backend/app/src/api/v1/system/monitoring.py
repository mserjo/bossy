# backend/app/src/api/v1/system/monitoring.py
# -*- coding: utf-8 -*-
"""
API ендпоінти для моніторингу системи.

Надає доступ до даних моніторингу, таких як системні логи
(SystemLog) та метрики продуктивності (PerformanceMetric).
Доступ до цих ендпоінтів зазвичай обмежений суперкористувачами.
"""
import json  # Для розбору JSON рядка для тегів
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query

# Залежності API та моделі користувача
from backend.app.src.api.dependencies import get_current_active_superuser
from backend.app.src.models.auth import User as UserModel  # Для типізації current_user

# Схеми Pydantic для моніторингу (припускаємо, що вони визначені тут)
from backend.app.src.schemas.system.monitoring_schemas import (
    SystemLogResponseSchema,
    PerformanceMetricResponseSchema,
    SystemLogQueryFiltersSchema,
    PerformanceMetricQueryFiltersSchema  # Додамо схему для фільтрів метрик
)

# Сервіс моніторингу
from backend.app.src.services.system.system_monitoring_service import SystemMonitoringService
# Логер з конфігурації
from backend.app.src.config.logging import logger  # Використовуємо централізований логер

router = APIRouter()


# --- Ендпоінти ---
# TODO: Уточнити, які саме дані моніторингу є критично важливими (наприклад, логи Celery, довжина черг, стан БД).

@router.get(
    "/logs",
    response_model=List[SystemLogResponseSchema],
    summary="Отримати системні логи",  # i18n
    description="Дозволяє суперкористувачам переглядати системні логи з можливістю фільтрації та пагінації.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]
)
async def list_system_logs(
        filters: SystemLogQueryFiltersSchema = Depends(),  # Фільтри з query параметрів
        skip: int = Query(0, ge=0, description="Кількість записів для пропуску (пагінація)"),  # i18n
        limit: int = Query(100, ge=1, le=500, description="Максимальна кількість записів для повернення (пагінація)"),
        # i18n
        service: SystemMonitoringService = Depends(),  # Реальна ін'єкція сервісу
        current_superuser: UserModel = Depends(get_current_active_superuser)  # Поточний суперкористувач
):
    """
    Повертає список записів системного логу.
    Доступно тільки суперкористувачам.
    Підтримує фільтрацію за рівнем, іменем логера, ID користувача, датою та вмістом повідомлення, а також пагінацію.
    """
    active_filters_dict = filters.model_dump(exclude_none=True)
    logger.info(
        f"Користувач '{current_superuser.username}' запитує список системних логів. "  # i18n
        f"Фільтри: {active_filters_dict if active_filters_dict else 'немає'}. "  # i18n
        f"Пагінація: skip={skip}, limit={limit}."  # i18n
    )

    system_logs = await service.get_system_logs(filters=filters, skip=skip, limit=limit)
    # TODO: Додати обробку можливих помилок від сервісу, якщо це потрібно (наприклад, якщо сервіс може повернути помилку)
    return system_logs


@router.get(
    "/metrics",
    response_model=List[PerformanceMetricResponseSchema],
    summary="Отримати метрики продуктивності",  # i18n
    description="Дозволяє суперкористувачам переглядати зібрані метрики продуктивності системи.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]
)
async def list_performance_metrics(
        # Використовуємо Depends для фільтрів метрик так само, як для логів
        filters: PerformanceMetricQueryFiltersSchema = Depends(),
        tags_json: Optional[str] = Query(None,
                                         description="Фільтр по тегах у форматі JSON рядка (наприклад, '{\"service\":\"worker\"}')"),
        # i18n
        skip: int = Query(0, ge=0, description="Кількість записів для пропуску (пагінація)"),  # i18n
        limit: int = Query(100, ge=1, le=1000, description="Максимальна кількість записів для повернення (пагінація)"),
        # i18n
        service: SystemMonitoringService = Depends(),
        current_superuser: UserModel = Depends(get_current_active_superuser)
):
    """
    Повертає список зібраних метрик продуктивності.
    Доступно тільки суперкористувачам.
    Підтримує фільтрацію за назвою метрики, датою, тегами (через JSON рядок) та пагінацію.
    """
    parsed_tags_filter: Optional[Dict[str, str]] = None
    if tags_json:
        try:
            parsed_tags_filter = json.loads(tags_json)
            if not isinstance(parsed_tags_filter, dict):
                raise ValueError("Теги мають бути представлені як словник JSON.")  # i18n
            # Додаткова валідація: ключі та значення мають бути рядками
            if not all(isinstance(k, str) and isinstance(v, str) for k, v in parsed_tags_filter.items()):
                raise ValueError("Ключі та значення тегів повинні бути рядками.")  # i18n
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Некоректний JSON для фільтра тегів: '{tags_json}'. Помилка: {e}")  # i18n
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Некоректний формат JSON для тегів: {e}"  # i18n
            )

    # Оновлюємо об'єкт фільтрів з розпарсеними тегами
    # Краще було б, якби PerformanceMetricQueryFiltersSchema мав поле tags: Optional[Dict[str,str]]
    # і FastAPI автоматично парсив його, але це може бути складніше для query параметрів.
    # Поки що передаємо окремо в сервіс.
    # Або модифікувати filters об'єкт: filters.tags = parsed_tags_filter (якщо таке поле існує в схемі)

    active_filters_dict = filters.model_dump(exclude_none=True)
    log_message = (
        f"Користувач '{current_superuser.username}' запитує список метрик продуктивності. "  # i18n
        f"Фільтри: {active_filters_dict if active_filters_dict else 'немає'}. "  # i18n
    )
    if parsed_tags_filter:
        log_message += f"Теги: {parsed_tags_filter}. "  # i18n
    log_message += f"Пагінація: skip={skip}, limit={limit}."  # i18n
    logger.info(log_message)

    # Передаємо розпарсені теги в сервіс. Сервіс має очікувати `tags_filter: Optional[Dict[str, str]]`
    performance_metrics = await service.get_performance_metrics(
        filters=filters,  # Передаємо об'єкт фільтрів
        tags_filter=parsed_tags_filter,  # Окремо передаємо теги
        skip=skip,
        limit=limit
    )
    # TODO: Додати обробку можливих помилок від сервісу
    return performance_metrics


logger.info("Маршрутизатор для ендпоінтів моніторингу API v1 (`monitoring.router`) визначено.")  # i18n
# Примітка: назва файлу monitoring.py, лог повідомлення було monitoring_endpoints.router. Виправлено на monitoring.router.
