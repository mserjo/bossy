# backend/app/src/models/system/health.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає моделі SQLAlchemy для моніторингу стану ("здоров'я") системи та її компонентів.
Це може включати статус доступності бази даних, зовнішніх сервісів, фонових задач тощо.
Ці дані використовуються для ендпоінта Health Check API.
"""

from sqlalchemy import Column, String, DateTime, JSON, Boolean # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
import uuid # Для роботи з UUID

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

# TODO: Визначити, чи потрібна таблиця в БД для health check, чи це буде динамічна перевірка.
# Зазвичай Health Check API динамічно перевіряє стан компонентів під час запиту.
# Однак, може бути корисно зберігати історію перевірок або статус компонентів,
# який оновлюється фоновою задачею.

# Варіант 1: Таблиця для запису результатів періодичних перевірок стану компонентів.
class ServiceHealthStatusModel(BaseModel):
    """
    Модель для зберігання історії статусів перевірки "здоров'я" окремих компонентів системи.
    Це може бути корисно для аналізу доступності сервісів з часом.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запису перевірки (успадковано).
        component_name (str): Назва компонента, що перевіряється (наприклад, "database", "redis", "celery_worker", "external_payment_api").
        status (str): Статус компонента ('healthy', 'unhealthy', 'degraded', 'unknown').
        checked_at (datetime): Час, коли була проведена перевірка. По суті, це `created_at` з BaseModel.
        details (JSON | None): Додаткові деталі про стан, повідомлення про помилку, час відповіді тощо.
        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення (успадковано, тут не дуже релевантно).
    """
    __tablename__ = "service_health_statuses"

    # Назва компонента або сервісу, стан якого перевіряється.
    # Наприклад: "database", "redis_cache", "celery_broker", "payment_gateway_api".
    component_name: Column[str] = Column(String(255), nullable=False, index=True)

    # Статус компонента.
    # Наприклад: "healthy" (все добре), "unhealthy" (недоступний або помилка),
    # "degraded" (працює, але з проблемами/повільно), "unknown" (не вдалося перевірити).
    status: Column[str] = Column(String(50), nullable=False, index=True)

    # `created_at` з `BaseModel` буде використовуватися як `checked_at`.
    # `updated_at` тут менш значуще, оскільки записи про стан зазвичай не змінюються.

    # Додаткові деталі у форматі JSON.
    # Може містити повідомлення про помилку, час відповіді, версію компонента тощо.
    details: Column[JSON | None] = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі ServiceHealthStatusModel.
        """
        return f"<{self.__class__.__name__}(component='{self.component_name}', status='{self.status}', checked_at='{self.created_at}')>"

# Якщо Health Check API буде суто динамічним і не потребуватиме зберігання історії в БД,
# то ця модель може бути непотрібною. Однак, для цілей моніторингу та аналізу тенденцій
# доступності сервісів, зберігання історії може бути корисним.
# Наприклад, фонова задача може періодично перевіряти компоненти і записувати їх стан сюди.

# TODO: Перевірити вимоги з `technical-task.md` та `structure-claude-v3.md`.
# `technical-task.md` згадує "Health Check API".
# `structure-claude-v3.md` вказує `backend/app/src/models/system/health.py`.
# Наявність моделі `ServiceHealthStatusModel` для зберігання історії перевірок
# є одним із способів реалізації частини моніторингу стану.
# Назва таблиці `service_health_statuses` є описовою.
# Поля `component_name`, `status`, `details` та використання `created_at` як `checked_at`
# виглядають доречними для такої моделі.
# Використання `BaseModel` як основи є адекватним.

# Подумайте, чи потрібні також моделі для:
# - `SystemInfoModel`: статична інформація про систему (версія ОС, версія Python, тощо),
#   яка може оновлюватися рідко. Або це краще отримувати динамічно.
# - `ResourceUsageModel`: історичні дані про використання ресурсів (CPU, RAM).
#   Це вже більше схоже на `PerformanceMetricModel` з `monitoring.py`.

# Наразі `ServiceHealthStatusModel` виглядає як єдина необхідна модель в цьому файлі
# для підтримки функціоналу Health Check та моніторингу стану компонентів.
# Якщо Health Check буде повністю динамічним, ця таблиця може використовуватися
# для запису результатів цих динамічних перевірок для подальшого аналізу.
