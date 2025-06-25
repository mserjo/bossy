# backend/app/src/schemas/system/monitoring.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделей, пов'язаних з моніторингом системи,
зокрема для `SystemEventLogModel`.
Схеми використовуються для валідації даних при створенні (записі логів)
та відображенні логів.
"""

from pydantic import Field, field_validator
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema, IdentifiedSchema, TimestampedSchema
# Потрібно імпортувати схему користувача для `user` (якщо розгортаємо)
# from backend.app.src.schemas.auth.user import UserMinimumSchema # Приклад

# --- Схема для відображення запису системного логу (для читання) ---
class SystemEventLogSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення запису системного логу/події.
    """
    # `created_at` з AuditDatesSchema використовується як час події/логу.
    # `updated_at` тут менш релевантне, зазвичай логи не змінюються.

    level: str = Field(..., description="Рівень логування (наприклад, 'INFO', 'WARNING', 'ERROR')")
    logger_name: Optional[str] = Field(None, description="Назва логгера, який згенерував запис")
    message: str = Field(..., description="Основне повідомлення логу")

    source_component: Optional[str] = Field(None, description="Компонент системи, звідки надійшов лог")
    request_id: Optional[str] = Field(None, description="Ідентифікатор запиту, якщо лог пов'язаний з обробкою HTTP-запиту")

    user_id: Optional[uuid.UUID] = Field(None, description="Ідентифікатор користувача, якщо дія пов'язана з користувачем")
    # user: Optional[UserMinimumSchema] = None # Для відображення мінімальної інформації про користувача

    ip_address: Optional[str] = Field(None, description="IP-адреса джерела запиту/події (представлена як рядок)")
    # В моделі `ip_address` має тип INET, Pydantic може потребувати кастомного типу або серіалізації в рядок.
    # SQLAlchemy зазвичай повертає рядок для INET, тому тут `str` має бути ОК.

    details: Optional[Dict[str, Any]] = Field(None, description="Додаткові структуровані дані, пов'язані з подією (JSON)")

    # @field_validator('ip_address', mode='before')
    # @classmethod
    # def validate_ip_address(cls, value):
    #     # Якщо з БД приходить об'єкт ipaddress.IPv4Address/IPv6Address, конвертуємо в рядок.
    #     # Зазвичай SQLAlchemy повертає рядок.
    #     if value is not None and not isinstance(value, str):
    #         return str(value)
    #     return value


# --- Схема для створення нового запису системного логу ---
# Ця схема зазвичай використовується внутрішньо системою логування, а не через API.
# Але може бути корисною для тестування або якщо є ендпоінт для прийому логів.
class SystemEventLogCreateSchema(BaseSchema):
    """
    Схема для створення нового запису системного логу.
    `created_at` буде встановлено автоматично.
    """
    level: str = Field(..., description="Рівень логування")
    logger_name: Optional[str] = Field(None, max_length=255, description="Назва логгера")
    message: str = Field(..., description="Повідомлення логу")

    source_component: Optional[str] = Field(None, max_length=100, description="Компонент системи")
    request_id: Optional[str] = Field(None, max_length=100, description="Ідентифікатор запиту")
    user_id: Optional[uuid.UUID] = Field(None, description="Ідентифікатор користувача")
    ip_address: Optional[str] = Field(None, description="IP-адреса") # Очікуємо рядок
    details: Optional[Dict[str, Any]] = Field(None, description="Додаткові дані (JSON)")

    @field_validator('level')
    @classmethod
    def level_must_be_known(cls, value: str) -> str:
        # TODO: Визначити список дозволених рівнів логування (можливо, з Enum)
        known_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'AUDIT']
        if value.upper() not in known_levels:
            raise ValueError(f"Невідомий рівень логування: {value}. Дозволені: {', '.join(known_levels)}")
        return value.upper()

    # @field_validator('ip_address')
    # @classmethod
    # def validate_ip_address_format(cls, value: Optional[str]) -> Optional[str]:
    #     if value is not None:
    #         try:
    #             # import ipaddress
    #             # ipaddress.ip_address(value) # Перевірка формату
    #             pass # Проста перевірка, або використання stricter валідатора
    #         except ValueError:
    #             raise ValueError(f"Некоректний формат IP-адреси: {value}")
    #     return value


# TODO: Схеми для PerformanceMetricModel, якщо вона буде реалізована.
# class PerformanceMetricSchema(AuditDatesSchema):
#     metric_name: str
#     metric_value_float: Optional[float] = None
#     metric_value_int: Optional[int] = None
#     metric_value_str: Optional[str] = None
#     source_component: Optional[str] = None
#     tags: Optional[Dict[str, Any]] = None
#
# class PerformanceMetricCreateSchema(BaseSchema):
#     metric_name: str
#     metric_value_float: Optional[float] = None
#     metric_value_int: Optional[int] = None
#     metric_value_str: Optional[str] = None
#     source_component: Optional[str] = None
#     tags: Optional[Dict[str, Any]] = None
#     timestamp: Optional[datetime] = None # Час метрики, якщо відрізняється від created_at


# TODO: Переконатися, що схеми відповідають моделі `SystemEventLogModel`.
# `SystemEventLogModel` успадковує від `BaseModel` (id, created_at, updated_at).
# `SystemEventLogSchema` успадковує від `AuditDatesSchema` (id, created_at, updated_at)
# і додає специфічні поля: level, logger_name, message, source_component, request_id, user_id, ip_address, details.
# Це виглядає узгоджено.
#
# Валідатор для `level` в `SystemEventLogCreateSchema` корисний.
# Валідація `ip_address` (закоментована) може бути додана для строгості.
# Поле `user` (розгорнутий об'єкт користувача) в `SystemEventLogSchema` закоментоване,
# оскільки потребує імпорту `UserMinimumSchema` (яка ще не створена) і може призвести до циклічних залежностей
# на цьому етапі. Це можна буде додати пізніше, якщо потрібно буде відображати інформацію про користувача разом з логом.
# Поки що достатньо `user_id`.
# `ip_address` в схемі представлений як `str`, що відповідає тому, як SQLAlchemy зазвичай повертає тип `INET`.
# `details` як `Dict[str, Any]` для JSON даних.
# Все виглядає добре.
