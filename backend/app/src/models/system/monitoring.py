# backend/app/src/models/system/monitoring.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає моделі SQLAlchemy для збору та зберігання даних моніторингу системи.
Це може включати системні логи, метрики продуктивності, записи про помилки тощо.
Ці дані допомагають відстежувати стан системи, діагностувати проблеми та аналізувати її роботу.
"""
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Float, ForeignKey # type: ignore
from sqlalchemy.dialects.postgresql import UUID, INET # type: ignore
import uuid # Для роботи з UUID

from sqlalchemy.orm import Mapped, relationship, mapped_column # type: ignore # Додано mapped_column

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel, оскільки це записи логів/метрик

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import UserModel

# TODO: Розділити на декілька моделей, якщо потрібно:
# - SystemLogModel: для текстових логів додатку.
# - PerformanceMetricModel: для числових метрик (CPU, memory, response_time).
# - ErrorLogModel: для деталізованих записів про помилки та винятки.
# Поки що спробуємо створити більш загальну модель логування, яку можна буде розширити.

class SystemEventLogModel(BaseModel):
    """
    Модель для зберігання системних подій та логів.
    Це можуть бути інформаційні повідомлення, попередження, помилки, аудиторські записи.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запису логу (успадковано).
        timestamp (datetime): Точний час виникнення події/запису логу. За замовчуванням created_at з BaseModel.
        level (str): Рівень логування (наприклад, 'INFO', 'WARNING', 'ERROR', 'DEBUG', 'CRITICAL', 'AUDIT').
        logger_name (str | None): Назва логгера, який згенерував запис (наприклад, 'auth_service', 'task_processor').
        message (Text): Основне повідомлення логу.
        source_component (str | None): Компонент системи, звідки надійшов лог (наприклад, 'backend-api', 'celery-worker').
        request_id (str | None): Ідентифікатор запиту, якщо лог пов'язаний з обробкою HTTP-запиту.
        user_id (uuid.UUID | None): Ідентифікатор користувача, якщо дія пов'язана з користувачем.
        ip_address (INET | None): IP-адреса джерела запиту/події.
        details (JSON | None): Додаткові структуровані дані, пов'язані з подією (наприклад, traceback, параметри запиту).
        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано, тут може бути нерелевантним).
                               Логи зазвичай не оновлюються.
    """
    __tablename__ = "system_event_logs"

    # `id` та `created_at` успадковані. `updated_at` також, але для логів воно зазвичай не змінюється
    # і буде дорівнювати `created_at`. Можна розглянути його видалення для цієї моделі, якщо перевизначати BaseModel.
    # Або ж залишити як є.

    # Точний час події. `created_at` з `BaseModel` може виконувати цю роль.
    # Якщо потрібна окрема мітка часу самої події, а не створення запису логу:
    # event_timestamp: Column[DateTime] = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    # Але для простоти, будемо вважати, що created_at є часом події.

    # Рівень логування.
    level: Column[str] = Column(String(50), nullable=False, index=True) # INFO, WARNING, ERROR, DEBUG, AUDIT

    # Назва логгера або модуля, який згенерував запис.
    logger_name: Column[str | None] = Column(String(255), nullable=True, index=True)

    # Основне повідомлення логу.
    message: Column[str] = Column(Text, nullable=False)

    # Компонент системи, звідки надійшов лог.
    source_component: Column[str | None] = Column(String(100), nullable=True, index=True)

    # Ідентифікатор запиту (якщо лог пов'язаний з HTTP-запитом).
    request_id: Column[str | None] = Column(String(100), nullable=True, index=True)

    # Ідентифікатор користувача, дії якого спричинили цей лог.
    # TODO: Замінити "users.id" на правильний шлях до моделі користувача, коли вона буде готова.
    user_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_system_event_logs_user_id"), nullable=True, index=True)

    # IP-адреса, з якої прийшов запит або відбулася подія.
    ip_address: Column[INET | None] = Column(INET, nullable=True)

    # Додаткові структуровані дані у форматі JSON.
    # Наприклад, стек викликів для помилок, параметри запиту, змінені дані для аудиту.
    details: Column[JSON | None] = Column(JSON, nullable=True)

    # TODO: Розглянути партиціонування таблиці логів за датою для дуже великих об'ємів даних.
    # TODO: Додати індекси для полів, за якими часто буде відбуватися пошук (наприклад, level, timestamp, user_id).
    # `created_at` (якщо використовується як timestamp) вже має індекс з BaseModel.

    # Зв'язок з користувачем
    user: Mapped[Optional["UserModel"]] = relationship(foreign_keys=[user_id], back_populates="system_event_logs", lazy="selectin")

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі SystemEventLogModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', level='{self.level}', message='{self.message[:50]}...')>"

# class PerformanceMetricModel(BaseModel):
#     """
#     Модель для зберігання метрик продуктивності системи.
#     Наприклад: CPU load, memory usage, response time, DB query time.
#     """
#     __tablename__ = "performance_metrics"
#
#     metric_name: Column[str] = Column(String(255), nullable=False, index=True) # e.g., "cpu_utilization", "response_time_avg"
#     metric_value_float: Column[float | None] = Column(Float, nullable=True) # For float values
#     metric_value_int: Column[int | None] = Column(Integer, nullable=True) # For int values
#     metric_value_str: Column[str | None] = Column(String, nullable=True) # For other types or units
#
#     # `timestamp` буде `created_at` з BaseModel
#
#     source_component: Column[str | None] = Column(String(100), nullable=True, index=True) # 'backend-api', 'db-server'
#     tags: Column[JSON | None] = Column(JSON, nullable=True) # Додаткові теги/лейбли для метрики
#
#     def __repr__(self) -> str:
#         value = self.metric_value_float if self.metric_value_float is not None else \
#                 (self.metric_value_int if self.metric_value_int is not None else self.metric_value_str)
#         return f"<{self.__class__.__name__}(name='{self.metric_name}', value='{value}')>"

# Наразі зосередимося на `SystemEventLogModel`. Модель для метрик може бути додана пізніше, якщо буде потреба
# зберігати їх саме в PostgreSQL, а не в спеціалізованих системах моніторингу (Prometheus, Grafana).

# TODO: Перевірити відповідність `technical-task.md` та `structure-claude-v3.md`.
# `technical-task.md` згадує "логігування backend (logger)", "очищення логування", "відрізання і пакування логування".
# `structure-claude-v3.md` вказує `backend/app/src/models/system/monitoring.py`.
# Модель `SystemEventLogModel` призначена для зберігання таких логів.
# Назва таблиці `system_event_logs` є достатньо описовою.
# Поля `level`, `message`, `details` є стандартними для логів.
# Додаткові поля, такі як `logger_name`, `source_component`, `request_id`, `user_id`, `ip_address`,
# збагачують контекст логу.
# Використання `BaseModel` як основи є доречним.
# ForeignKey на `users.id` потребуватиме створення моделі `UserModel`.
# Тип `INET` для `ip_address` є специфічним для PostgreSQL і добре підходить для зберігання IP-адрес.
# `JSON` для `details` дозволяє зберігати гнучку структуровану інформацію.
# `updated_at` з `BaseModel` для логів менш релевантне, але не шкодить.
