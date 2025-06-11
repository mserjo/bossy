# backend/app/src/services/system/health.py
# import logging # Замінено на централізований логер
import time # Для вимірювання часу відповіді
from typing import List, Dict, Any, Literal, Optional
from datetime import datetime, timezone # Додано timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text # Для виконання "сирих" SQL запитів, наприклад 'SELECT 1'

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.schemas.system.health import ( # Схеми Pydantic
    HealthCheckResponse,
    ComponentHealth,
    HealthStatusEnum # Enum або Literal для статусів
)
from backend.app.src.config.redis import get_redis_pool_or_none # Оновлено для отримання пулу або None
from backend.app.src.config.logging import logger # Централізований логер
from backend.app.src.config import settings # Для доступу до конфігурацій (наприклад, DEBUG)

# TODO: Додати залежність: pip install httpx (якщо буде реальна перевірка зовнішніх API)
# import httpx # Для перевірки зовнішніх HTTP сервісів

# Використовуємо HealthStatusEnum, якщо визначено, інакше Literal як запасний варіант
# Це забезпечує роботу, навіть якщо HealthStatusEnum не імпортовано належним чином,
# але для генерації схем Pydantic краще, щоб HealthStatusEnum був правильно визначений
# в backend.app.src.schemas.system.health та імпортований.
ComponentStatusType = HealthStatusEnum # Припускаємо, що HealthStatusEnum визначено як Enum


class HealthCheckService(BaseService):
    """
    Сервіс для виконання перевірок стану системи та її різних компонентів,
    таких як база даних, кеш (Redis) та інші залежні сервіси.
    """

    def __init__(self, db_session: AsyncSession): # Додати інші клієнти, наприклад, redis_client, якщо потрібно
        super().__init__(db_session)
        self.redis_pool = get_redis_pool_or_none() # Отримуємо пул Redis або None, якщо не налаштовано
        if self.redis_pool:
            # import redis.asyncio as aioredis # Локальний імпорт або на рівні модуля, якщо використовується часто
            # self.redis_client = aioredis.Redis(connection_pool=self.redis_pool)
            logger.info("HealthCheckService: Клієнт Redis буде створено з пулу при потребі.")
        else:
            logger.warning("HealthCheckService: Пул з'єднань Redis не налаштовано. Перевірка Redis буде недоступна.")
        logger.info("HealthCheckService ініціалізовано.")

    async def _check_database_health(self) -> ComponentHealth:
        """
        Перевіряє стан основної бази даних.
        Намагається виконати простий запит.
        """
        component_name = "database" # i18n
        start_time = time.perf_counter()
        status: ComponentStatusType = HealthStatusEnum.HEALTHY
        message = "База даних успішно підключена та відповідає." # i18n
        details: Dict[str, Any] = {}

        try:
            # Виконання простого запиту для перевірки з'єднання з БД
            result = await self.db_session.execute(text("SELECT 1"))
            if result.scalar_one() != 1:
                # i18n
                raise Exception("Запит перевірки стану бази даних не повернув 1.")
            # Тут можна додати перевірку статусу міграцій, якщо потрібно
            # details["migrations_status"] = "актуальний" # i18n example
        except Exception as e:
            logger.error(f"Перевірка стану бази даних не вдалася: {e}", exc_info=settings.DEBUG)
            status = HealthStatusEnum.UNHEALTHY
            message = f"Помилка з'єднання з базою даних: {str(e)}" # i18n

        duration_ms = (time.perf_counter() - start_time) * 1000
        details["response_time_ms"] = round(duration_ms, 2)

        return ComponentHealth(
            component_name=component_name,
            status=status,
            message=message,
            details=details,
            timestamp=datetime.now(timezone.utc) # Використовуємо timezone.utc
        )

    async def _check_redis_health(self) -> Optional[ComponentHealth]:
        """
        Перевіряє стан кешу Redis.
        Потребує наявності клієнта Redis.
        """
        component_name = "redis_cache" # i18n
        start_time = time.perf_counter()
        details: Dict[str, Any] = {}

        if not self.redis_pool:
            logger.info("Клієнт Redis не налаштований, пропуск перевірки стану Redis.")
            # Можна повернути DEGRADED або взагалі не включати цей компонент
            return ComponentHealth(
                component_name=component_name,
                status=HealthStatusEnum.DEGRADED,
                message="Клієнт Redis не налаштований.", # i18n
                details={"reason": "Пул з'єднань Redis не доступний."}, # i18n
                timestamp=datetime.now(timezone.utc)
            )

        status: ComponentStatusType = HealthStatusEnum.HEALTHY
        message = "З'єднання з Redis успішне, PING отримав відповідь." # i18n

        try:
            # TODO: Ініціалізувати redis_client тут або в __init__, якщо він потрібен часто.
            #  Поточна реалізація get_redis_pool_or_none() повертає пул.
            import redis.asyncio as aioredis # Локальний імпорт
            redis_client = aioredis.Redis(connection_pool=self.redis_pool)
            if not await redis_client.ping():
                # i18n
                raise Exception("Команда Redis PING не вдалася (повернула False).")
            # Опціонально: перевірити деякі ключі або статистику
            # info = await redis_client.info()
            # details["redis_version"] = info.get("redis_version")
            await redis_client.close() # Закриваємо з'єднання, отримане напряму, не з пулу для одноразового використання
        except Exception as e:
            logger.error(f"Перевірка стану Redis не вдалася: {e}", exc_info=settings.DEBUG)
            status = HealthStatusEnum.UNHEALTHY
            message = f"Помилка з'єднання з Redis: {str(e)}" # i18n

        duration_ms = (time.perf_counter() - start_time) * 1000
        details["response_time_ms"] = round(duration_ms, 2)

        return ComponentHealth(
            component_name=component_name,
            status=status,
            message=message,
            details=details,
            timestamp=datetime.now(timezone.utc)
        )

    async def _check_external_api_health(self, api_name: str, api_url: str, http_method: str = "GET", expected_status: int = 200) -> ComponentHealth:
        """
        [ЗАГЛУШКА/TODO] Перевіряє стан зовнішньої залежності HTTP API.
        Потребує реалізації з використанням httpx або подібної бібліотеки.
        """
        component_name = f"external_api:{api_name}" # i18n
        start_time = time.perf_counter()
        details: Dict[str, Any] = {"url": api_url, "method": http_method}

        # TODO: Реалізувати перевірку зовнішнього API за допомогою httpx.
        # try:
        #     async with httpx.AsyncClient(timeout=5.0) as client:
        #         response = await client.request(http_method, api_url)
        #         if response.status_code != expected_status:
        #             raise Exception(f"API {api_name} повернуло статус {response.status_code}, очікувалося {expected_status}.")
        #         # Додаткові перевірки відповіді, якщо потрібно
        #     status = HealthStatusEnum.HEALTHY
        #     message = f"З'єднання з API {api_name} успішне (статус {expected_status})." # i18n
        # except Exception as e:
        #     logger.error(f"Перевірка API {api_name} ({api_url}) не вдалася: {e}", exc_info=settings.DEBUG)
        #     status = HealthStatusEnum.UNHEALTHY
        #     message = f"Помилка з'єднання або відповіді від API {api_name}: {str(e)}" # i18n
        #     if hasattr(e, 'response') and e.response is not None: details["status_code"] = e.response.status_code

        duration_ms = (time.perf_counter() - start_time) * 1000
        details["response_time_ms"] = round(duration_ms, 2)

        logger.warning(f"Перевірка зовнішнього API для {api_name} є заглушкою.")
        return ComponentHealth(
            component_name=component_name,
            status=HealthStatusEnum.DEGRADED, # Позначаємо як DEGRADED, оскільки це заглушка
            message=f"Перевірка API {api_name} не реалізована повністю (заглушка).", # i18n
            details=details,
            timestamp=datetime.now(timezone.utc)
        )

    async def perform_full_health_check(self) -> HealthCheckResponse:
        """
        Виконує комплексну перевірку стану всіх критичних компонентів системи.
        Агрегує статуси окремих компонентів.
        """
        logger.info("Виконання повної перевірки стану системи...")
        components_health: List[ComponentHealth] = []

        # Стан бази даних
        db_health = await self._check_database_health()
        components_health.append(db_health)

        # Стан Redis (якщо налаштовано)
        redis_health = await self._check_redis_health()
        if redis_health:
             components_health.append(redis_health)

        # TODO: Додати перевірки інших критичних залежностей, якщо вони є.
        # Приклад: перевірка зовнішнього сервісу (заглушка)
        # external_api_health = await self._check_external_api_health(
        #     api_name="ExampleExternalService",
        #     api_url=getattr(settings, "EXAMPLE_SERVICE_HEALTH_URL", "http://api.example.com/health")
        # )
        # components_health.append(external_api_health)

        # Визначення загального стану системи
        overall_status: ComponentStatusType = HealthStatusEnum.HEALTHY
        for component in components_health:
            if component.status == HealthStatusEnum.UNHEALTHY:
                overall_status = HealthStatusEnum.UNHEALTHY
                break # Якщо один компонент не здоровий, вся система не здорова
            if component.status == HealthStatusEnum.DEGRADED and overall_status == HealthStatusEnum.HEALTHY:
                overall_status = HealthStatusEnum.DEGRADED # DEGRADED менш серйозний, ніж UNHEALTHY

        response = HealthCheckResponse(
            overall_status=overall_status,
            components=components_health,
            system_timestamp=datetime.now(timezone.utc) # Використовуємо timezone.utc
        )

        log_level = logging.INFO if overall_status == HealthStatusEnum.HEALTHY else logging.WARNING
        status_value = overall_status.value if hasattr(overall_status, 'value') else overall_status # Для Enum
        logger.log(log_level, f"Повну перевірку стану системи завершено. Загальний статус: {status_value}")
        return response

logger.info("HealthCheckService (сервіс перевірки стану) успішно визначено.")
