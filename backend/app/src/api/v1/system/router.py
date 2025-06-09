# backend/app/src/api/v1/system/router.py
# -*- coding: utf-8 -*-
"""
Головний роутер для системних API ендпоінтів версії v1.

Цей модуль агрегує всі APIRouter'и, що стосуються системних функцій,
таких як управління налаштуваннями, моніторинг, перевірка стану системи
та ініціалізація даних.

`system_router` потім підключається до `v1_router` в `app.src.api.v1.router`.
"""

import logging
from fastapi import APIRouter, Depends

# Імпорт роутерів з окремих файлів ендпоінтів
# Кожен з цих модулів має експортувати змінну `router`, яка є APIRouter.
from . import settings_endpoints
from . import monitoring_endpoints
from . import health_endpoints
from . import init_data_endpoints

# Можна імпортувати загальні залежності, якщо вони потрібні для всього /system шляху
# from app.src.api.dependencies import get_current_active_superuser

logger = logging.getLogger(__name__)

system_router = APIRouter(
    # Префікс для всіх системних шляхів ("/system") буде додано при підключенні
    # цього `system_router` до `v1_router` в `api/v1/router.py`.
    # Наприклад: v1_router.include_router(system_router, prefix="/system")

    tags=["V1 System Management"], # Загальний тег для всіх ендпоінтів цього роутера в Swagger UI

    # Якщо всі ендпоінти під /system вимагають однакових прав (наприклад, суперюзера),
    # можна додати залежність тут. Однак, часто краще визначати залежності
    # на рівні конкретних ендпоінтів або під-роутерів для більшої гнучкості.
    # dependencies=[Depends(get_current_active_superuser)],
)

# Підключення роутерів для кожного типу системних ендпоінтів
# Кожен з цих модулів (`settings_endpoints`, etc.) має містити змінну `router: APIRouter`.

system_router.include_router(
    settings_endpoints.router, # Об'єкт APIRouter з settings_endpoints.py
    prefix="/settings",        # Шляхи будуть /system/settings/...
    tags=["V1 System Settings"] # Більш специфічний тег для цієї групи ендпоінтів
)
logger.debug("Роутер system.settings_endpoints підключено до system_router з префіксом /settings.")

system_router.include_router(
    monitoring_endpoints.router,
    prefix="/monitoring",      # Шляхи будуть /system/monitoring/...
    tags=["V1 System Monitoring"]
)
logger.debug("Роутер system.monitoring_endpoints підключено до system_router з префіксом /monitoring.")

system_router.include_router(
    health_endpoints.router,
    prefix="/health",          # Шляхи будуть /system/health/...
    tags=["V1 System Health"]  # Тег може дублювати тег з самого ендпоінта, але тут для групи
)
logger.debug("Роутер system.health_endpoints підключено до system_router з префіксом /health.")

system_router.include_router(
    init_data_endpoints.router,
    prefix="/data-initialization", # Шляхи будуть /system/data-initialization/...
    tags=["V1 System Data Initialization"]
)
logger.debug("Роутер system.init_data_endpoints підключено до system_router з префіксом /data-initialization.")


# Приклад простого ендпоінта безпосередньо в system_router, якщо потрібно.
# Цей ендпоінт буде доступний за шляхом /system/ (якщо system_router підключено з префіксом /system).
@system_router.get(
    "/",
    summary="Кореневий ендпоінт системного API v1",
    include_in_schema=True, # Включимо в схему для наочності
    tags=["V1 System Management"] # Використовуємо загальний тег
)
async def system_root_info():
    """
    Надає базову інформацію про доступні системні під-модулі API v1.
    """
    logger.debug("System root endpoint for v1 (/api/v1/system/) викликано.")
    return {
        "message": "Ласкаво просимо до системного API v1 Kudos.",
        "description": "Доступні під-модулі: /settings, /monitoring, /health, /data-initialization.",
        "version": "v1"
    }


logger.info("Системний роутер API v1 (`system_router`) налаштовано та агреговано всі під-роутери.")

# Експорт system_router для використання в app.src.api.v1.system.__init__.py
# (і далі для підключення до v1_router)
# __all__ = ["system_router"] # Не є строго обов'язковим для прямого імпорту, але може бути корисним.
# Ми будемо імпортувати як `from .router import system_router` в __init__.py цього ж пакету.
