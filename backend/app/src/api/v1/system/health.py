# backend/app/src/api/v1/system/health.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перевірки стану "здоров'я" системи API v1.

Ці ендпоінти використовуються для моніторингу доступності та
базової працездатності сервісу.
"""

import logging
from typing import Dict, Any, Optional # Optional для Pydantic моделі
from datetime import datetime # Для timestamp

from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession # Для перевірки БД
# from sqlalchemy import text # Для виконання простого запиту

# from app.src.core.database import get_api_db_session # Або інший спосіб отримати сесію, наприклад, з api.dependencies
# from app.src.config.settings import settings # Можливо, для версії додатку

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Модель відповіді для детального стану здоров'я (приклад) ---
from pydantic import BaseModel # Pydantic має бути доступний у FastAPI проектах
class DependencyStatus(BaseModel):
    status: str
    message: Optional[str] = None

class DetailedHealthStatus(BaseModel):
    api_status: str = "healthy"
    timestamp: datetime
    app_version: Optional[str] = None # settings.APP_VERSION if settings else "N/A"
    dependencies: Dict[str, DependencyStatus] = {}


@router.get(
    "/status", # Шлях відносно префікса system_router, наприклад /api/v1/system/status
    summary="Проста перевірка стану здоров'я API",
    response_description="Повертає статус 'ok', якщо API працює.",
    tags=["V1 System Health & Status"] # Тег може бути уточнений тут або успадкований
)
async def simple_health_check() -> Dict[str, str]:
    """
    Найпростіший ендпоінт для перевірки доступності API.
    Якщо цей ендпоінт відповідає, це означає, що FastAPI додаток запущено
    і може обробляти запити на цьому рівні.
    Не перевіряє залежності (БД, кеш тощо).
    """
    logger.debug("Simple health check (/status) викликано.")
    return {"status": "ok", "message": "API (v1/system) is running"}

@router.get(
    "/healthz", # Популярний шлях для детальної перевірки (liveness/readiness probes)
    summary="Детальна перевірка стану здоров'я системи та її залежностей",
    response_model=DetailedHealthStatus, # Використовуємо Pydantic модель для відповіді
    response_description="Повертає детальний стан API та його основних залежностей.",
    tags=["V1 System Health & Status"]
)
async def detailed_health_check(
    # У реальному додатку тут була б залежність для сесії БД:
    # db_session: AsyncSession = Depends(get_api_db_session)
) -> DetailedHealthStatus: # Повертаємо екземпляр Pydantic моделі
    """
    Детальна перевірка стану здоров'я, включаючи залежності (наприклад, БД).

    У цьому прикладі перевірка БД є заглушкою. В реальній системі тут
    має бути спроба підключитися до БД та виконати простий запит (наприклад, SELECT 1).
    Якщо будь-яка критична залежність не працює, загальний статус може
    змінюватися, або ендпоінт може повертати HTTP 503.
    """
    logger.info("Detailed health check (/healthz) викликано.")

    current_time = datetime.utcnow()

    # --- Перевірка стану бази даних (заглушка) ---
    db_is_healthy = True # За замовчуванням вважаємо здоровою для заглушки
    db_status_message = "Database connection check not implemented in stub (assumed healthy)."

    # Приклад реальної перевірки (потребує db_session та sqlalchemy.text):
    # try:
    #     # Спроба виконати простий запит до БД
    #     # result = await db_session.execute(text("SELECT 1"))
    #     # if result.scalar_one() == 1:
    #     #     db_is_healthy = True
    #     #     db_status_message = "Database connection successful and responsive."
    #     #     logger.debug("Health check: Database connection verified (SELECT 1).")
    #     # else:
    #     #     db_is_healthy = False # Малоймовірно для SELECT 1
    #     #     db_status_message = "Database query 'SELECT 1' did not return 1."
    #     #     logger.warning(f"Health check: {db_status_message}")
    #
    #     # Імітуємо невелику затримку для IO операції
    #     await asyncio.sleep(0.01)
    #     # Для тестування помилки можна розкоментувати:
    #     # raise Exception("Simulated DB connection error")
    #
    # except Exception as e:
    #     db_is_healthy = False
    #     db_status_message = f"Database connection failed: {str(e)}"
    #     logger.error(f"Health check: Database connection or query error. Details: {e}", exc_info=True)

    dependencies_status = {
        "database": DependencyStatus(
            status="healthy" if db_is_healthy else "unhealthy",
            message=db_status_message
        )
        # Можна додати перевірки інших залежностей:
        # "redis_cache": DependencyStatus(status="healthy", message="Connection successful (stub)."),
        # "message_queue": DependencyStatus(status="unhealthy", message="RabbitMQ connection failed (stub).")
    }

    # Визначення загального статусу API на основі стану залежностей
    api_overall_status = "healthy"
    if not db_is_healthy: # Якщо будь-яка критична залежність не працює
        api_overall_status = "degraded" # Або "unhealthy", якщо це критично
        # У Kubernetes readiness probe, якщо повертається не 2xx, под не буде отримувати трафік.
        # Якщо потрібно повернути 503, можна підняти HTTPException тут,
        # але тоді Pydantic модель відповіді не буде використана для тіла помилки автоматично.
        # Краще повернути 200 OK, але зі статусом "unhealthy" в тілі, якщо сервіс ще працює, але деградував.
        # Якщо сервіс зовсім не може працювати без БД, тоді 503 доречний.
        # Для прикладу, залишимо 200 ОК, але зі зміненим api_status.
        logger.warning(f"Detailed health check: API status is '{api_overall_status}' due to unhealthy dependencies.")

    health_response = DetailedHealthStatus(
        api_status=api_overall_status,
        timestamp=current_time,
        # app_version=settings.APP_VERSION if hasattr(settings, "APP_VERSION") else "N/A",
        app_version = "0.1.0-stub", # Заглушка для версії
        dependencies=dependencies_status
    )

    # Якщо потрібно повернути 503, коли система не здорова:
    # if api_overall_status != "healthy":
    #     # Важливо: якщо піднімати HTTPException, то модель DetailedHealthStatus не буде автоматично
    #     # використана для форматування тіла відповіді про помилку. Потрібен кастомний обробник для 503,
    #     # або формувати JSONResponse вручну з тілом моделі.
    #     # Для простоти, ми повертаємо 200, але зі статусом "unhealthy" в тілі.
    #     # Якщо ж потрібно саме 503, то:
    #     # raise HTTPException(
    #     #     status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    #     #     detail=health_response.model_dump() # Використовуємо .model_dump() для Pydantic v2
    #     # )
    #     pass

    return health_response

# Коментар для розробника:
# Не забудьте оновити `backend/app/src/api/v1/system/__init__.py`, щоб підключити цей `router`.
# Наприклад, додати в __init__.py:
#
# from .health import router as health_router
# system_router.include_router(health_router) # Теги та префікс можна задати тут або в system_router

logger.info("Модуль API v1 System Health (`health.py`) завантажено.")
