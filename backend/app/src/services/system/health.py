# backend/app/src/services/system/health.py
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.app.src.services.base import BaseService
from backend.app.src.repositories.system.health_repository import ServiceHealthStatusRepository # Імпорт репозиторію
from backend.app.src.schemas.system.health import (
    OverallHealthStatusSchema, # Імпортуємо напряму
    ComponentHealth
)
from backend.app.src.core.dicts import HealthStatusType # Імпортуємо напряму з core.dicts
# ServiceHealthStatusCreateSchema, ServiceHealthStatusUpdateSchema не потрібні сервісу напряму
from backend.app.src.config.redis import get_redis_client # Змінено імпорт
from backend.app.src.config import settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


ComponentStatusType = HealthStatusType # Використовуємо імпортований HealthStatusType


class HealthCheckService(BaseService):
    """
    Сервіс для виконання перевірок стану системи та її різних компонентів,
    таких як база даних, кеш (Redis) та інші залежні сервіси.
    Зберігає результати перевірок у БД.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.health_repo = ServiceHealthStatusRepository() # Ініціалізація репозиторію
        self.is_redis_configured = bool(settings.USE_REDIS and settings.REDIS_URL)
        if self.is_redis_configured:
            logger.info("HealthCheckService: Redis налаштовано, буде перевірятися.")
        else:
            logger.warning("HealthCheckService: Redis не налаштовано або вимкнено. Перевірка Redis буде недоступна.")
        logger.info("HealthCheckService ініціалізовано.")

    async def _check_database_health(self) -> ComponentHealth:
        """
        Перевіряє стан основної бази даних та зберігає результат.
        Намагається виконати простий запит.
        """
        component_name = "database"
        start_time = time.perf_counter()
        status: ComponentStatusType = HealthStatusType.HEALTHY
        message = "База даних успішно підключена та відповідає."
        details_dict: Dict[str, Any] = {} # Змінено ім'я, щоб не конфліктувати з параметром details в repo

        try:
            result = await self.db_session.execute(text("SELECT 1"))
            if result.scalar_one() != 1:
                raise Exception("Запит перевірки стану бази даних не повернув 1.")
        except Exception as e:
            logger.error(f"Перевірка стану бази даних не вдалася: {e}", exc_info=settings.DEBUG)
            status = HealthStatusType.UNHEALTHY
            message = f"Помилка з'єднання з базою даних: {str(e)}"

        duration_ms = (time.perf_counter() - start_time) * 1000
        details_dict["response_time_ms"] = round(duration_ms, 2)

        # Зберігаємо статус в БД
        await self.health_repo.update_or_create_status(
            session=self.db_session,
            service_name=component_name,
            status=status, # Передаємо Enum член
            details=message if status == HealthStatusType.UNHEALTHY else None # Зберігаємо message як details при помилці
        )
        # Потрібен commit після update_or_create_status, якщо він сам не комітить.
        # Припускаємо, що коміт буде в perform_full_health_check або зовнішньому контексті.

        return ComponentHealth(
            component_name=component_name,
            status=status,
            message=message,
            details=details_dict,
            timestamp=datetime.now(timezone.utc)
        )

    async def _check_redis_health(self) -> Optional[ComponentHealth]:
        """
        Перевіряє стан кешу Redis та зберігає результат.
        Потребує наявності клієнта Redis.
        """
        component_name = "redis_cache"
        start_time = time.perf_counter()
        details_dict: Dict[str, Any] = {}

        if not self.is_redis_configured:
            logger.info("HealthCheckService: Redis не налаштовано або вимкнено, пропуск перевірки стану Redis.")
            status = HealthStatusType.DEGRADED # Або UNKNOWN, якщо це краще відображає ситуацію
            message = "Redis не налаштовано або вимкнено."
            details_dict["reason"] = "USE_REDIS is False or REDIS_URL is not set."
            await self.health_repo.update_or_create_status(
                session=self.db_session, service_name=component_name, status=status, details=message
            )
            return ComponentHealth(
                component_name=component_name, status=status, message=message, details=details_dict,
                timestamp=datetime.now(timezone.utc)
            )

        status: ComponentStatusType = HealthStatusType.HEALTHY
        message = "З'єднання з Redis успішне, PING отримав відповідь."
        redis_client = None
        try:
            redis_client = await get_redis_client() # Отримуємо клієнт тут
            if not await redis_client.ping():
                raise Exception("Команда Redis PING не вдалася (повернула False).")
            # Не потрібно redis_client.close() тут, оскільки get_redis_client керує глобальним клієнтом
        except ConnectionRefusedError: # Більш специфічна обробка помилки підключення
            logger.error(f"Перевірка стану Redis: ConnectionRefusedError", exc_info=settings.DEBUG)
            status = HealthStatusType.UNHEALTHY
            message = "Помилка з'єднання з Redis: Connection refused."
        except Exception as e:
            logger.error(f"Перевірка стану Redis не вдалася: {e}", exc_info=settings.DEBUG)
            status = HealthStatusType.UNHEALTHY
            message = f"Помилка з'єднання з Redis: {str(e)}"

        duration_ms = (time.perf_counter() - start_time) * 1000
        details_dict["response_time_ms"] = round(duration_ms, 2)

        await self.health_repo.update_or_create_status(
            session=self.db_session, service_name=component_name, status=status,
            details=message if status != HealthStatusType.HEALTHY else None
        )
        # Потрібен commit після update_or_create_status

        return ComponentHealth(
            component_name=component_name,
            status=status,
            message=message,
            details=details_dict,
            timestamp=datetime.now(timezone.utc)
        )

    async def _check_external_api_health(self, api_name: str, api_url: str, http_method: str = "GET",
                                         expected_status: int = 200) -> ComponentHealth:
        """
        [ЗАГЛУШКА/TODO] Перевіряє стан зовнішньої залежності HTTP API та зберігає результат.
        Потребує реалізації з використанням httpx або подібної бібліотеки.
        """
        component_name = f"external_api:{api_name}"
        start_time = time.perf_counter()
        details_dict: Dict[str, Any] = {"url": api_url, "method": http_method}
        status: ComponentStatusType = HealthStatusType.DEGRADED # За замовчуванням для заглушки
        message = f"Перевірка API {api_name} не реалізована повністю (заглушка)."

        # Логіка перевірки (закоментовано)
        # ...

        duration_ms = (time.perf_counter() - start_time) * 1000
        details_dict["response_time_ms"] = round(duration_ms, 2)

        logger.warning(f"Перевірка зовнішнього API для {api_name} є заглушкою.")

        await self.health_repo.update_or_create_status(
            session=self.db_session, service_name=component_name, status=status, details=message
        )
        # Потрібен commit після update_or_create_status

        return ComponentHealth(
            component_name=component_name,
            status=status,
            message=message,
            details=details_dict,
            timestamp=datetime.now(timezone.utc)
        )

    async def perform_full_health_check(self) -> OverallHealthStatusSchema: # Змінено тип повернення
        """
        Виконує комплексну перевірку стану всіх критичних компонентів системи,
        зберігає їх статуси та агрегує загальний статус.
        """
        logger.info("Виконання повної перевірки стану системи...")
        components_health_list: List[ComponentHealth] = [] # Змінено ім'я для уникнення конфлікту

        db_health = await self._check_database_health()
        components_health_list.append(db_health)

        redis_health = await self._check_redis_health()
        if redis_health: # _check_redis_health може повернути None, якщо Redis не налаштовано
            components_health_list.append(redis_health)

        # Приклад заглушки для зовнішнього API
        # external_api_health = await self._check_external_api_health("some_service", "http://example.com/health")
        # components_health_list.append(external_api_health)

        # Коміт всіх оновлень статусу, зроблених в _check_* методах
        try:
            await self.commit()
            logger.info("Результати перевірки стану компонентів збережено в БД.")
        except Exception as e:
            await self.rollback() # Відкат у разі помилки коміту
            logger.error(f"Помилка коміту при збереженні результатів перевірки стану: {e}", exc_info=True)
            # Навіть якщо коміт не вдався, продовжуємо формувати відповідь з поточними даними
            # Можливо, варто додати спеціальний статус або повідомлення про помилку збереження.

        overall_status: ComponentStatusType = HealthStatusType.HEALTHY
        for component in components_health_list:
            if component.status == HealthStatusType.UNHEALTHY:
                overall_status = HealthStatusType.UNHEALTHY
                break
            if component.status == HealthStatusType.DEGRADED and overall_status == HealthStatusType.HEALTHY:
                overall_status = HealthStatusType.DEGRADED

        response = OverallHealthStatusSchema( # Змінено на OverallHealthStatusSchema
            overall_status=overall_status,
            components=components_health_list,
            timestamp=datetime.now(timezone.utc) # Змінено system_timestamp на timestamp
        )

        # Використовуємо logger з backend.app.src.config.logging, який вже налаштований
        # Тому logging.INFO та logging.WARNING тут не потрібні.
        status_value = overall_status.value if hasattr(overall_status, 'value') else str(overall_status)
        if overall_status == HealthStatusType.HEALTHY:
            logger.info(f"Повну перевірку стану системи завершено. Загальний статус: {status_value}")
        else:
            logger.warning(f"Повну перевірку стану системи завершено. Загальний статус: {status_value}")
        return response


logger.info("HealthCheckService (сервіс перевірки стану) успішно визначено.")
