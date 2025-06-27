# backend/app/src/api/v1/system/health.py
# -*- coding: utf-8 -*-
"""
Ендпоінт для перевірки стану системи (Health Check).

Цей модуль надає API ендпоінт, який дозволяє перевірити базову
працездатність сервісу. Він може включати перевірки доступності
бази даних, зовнішніх сервісів (якщо критично важливі) тощо.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.src.api.dependencies import DBSession # Використовуємо реальну залежність
from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.system.health import HealthCheckResponseSchema, ServiceStatusSchema
import sqlalchemy # для перевірки з'єднання з БД
# TODO: Якщо є HealthService, його можна імпортувати для більш складних перевірок
# from backend.app.src.services.system.health_service import HealthService

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponseSchema,
    tags=["System", "Health Check"],
    summary="Перевірка стану сервісу",
    description="""
    Надає інформацію про стан сервісу та його залежностей (наприклад, бази даних).
    - **api_status**: Загальний стан API.
    - **db_status**: Стан підключення до бази даних.
    """
)
async def health_check(
    db_session: DBSession = Depends() # Використовуємо ін'єкцію DBSession
):
    """
    Перевіряє стан API та його основних залежностей.
    """
    api_status = ServiceStatusSchema(status="ok", message="API функціонує нормально.")
    db_status_val = "ok"
    db_message = "Підключення до бази даних успішне."

    try:
        # Проста перевірка підключення до БД
        # TODO: Можна замінити на більш надійну перевірку, наприклад, виконання простого запиту
        # connection = await db.connection() # Отримати з'єднання з пулу
        # await connection.execute(sqlalchemy.text("SELECT 1")) # Виконати простий запит
        # await connection.close() # Закрити з'єднання

        # Альтернативний спосіб перевірки, якщо попередній не працює з AsyncSession напряму
        async with db.begin(): # Почати транзакцію (і відкотити її)
            await db.execute(sqlalchemy.text("SELECT 1"))

        logger.info("Перевірка стану БД: успішно.")
    except Exception as e:
        logger.error(f"Помилка підключення до бази даних під час перевірки стану: {e}", exc_info=True)
        db_status_val = "error"
        db_message = "Помилка підключення до бази даних."
        # Якщо БД критична, можна змінити загальний статус API
        # api_status.status = "error"
        # api_status.message = "API має проблеми через недоступність бази даних."
        # і повернути відповідний HTTP статус, наприклад 503 Service Unavailable
        # raise HTTPException(
        #     status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        #     detail="Сервіс тимчасово недоступний через проблеми з базою даних."
        # )

    db_service_status = ServiceStatusSchema(status=db_status_val, message=db_message)

    # TODO: Додати перевірки інших важливих залежностей (Redis, Celery, зовнішні API тощо)
    # redis_status = ServiceStatusSchema(status="ok", message="Підключення до Redis успішне.")
    # external_service_status = ServiceStatusSchema(status="degraded", message="Зовнішній сервіс X відповідає повільно.")

    return HealthCheckResponseSchema(
        api_status=api_status,
        db_status=db_service_status
        # Додати інші статуси сюди
        # redis_status=redis_status,
        # external_services=[external_service_status]
    )

# TODO: Можливо, додати інші ендпоінти для більш детальної діагностики,
# наприклад, /health/db, /health/redis тощо.

# Роутер буде підключений в backend/app/src/api/v1/system/__init__.py
# або безпосередньо в backend/app/src/api/v1/router.py
