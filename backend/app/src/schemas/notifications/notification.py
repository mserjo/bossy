# backend/app/src/schemas/notifications/notification.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `NotificationModel`.
Схеми використовуються для валідації даних при створенні (зазвичай системою),
оновленні (наприклад, позначка про прочитання) та відображенні сповіщень.
"""

from pydantic import Field
from typing import Optional, List, Any, ForwardRef, Dict # Додано Dict
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.auth.user import UserPublicSchema (для recipient)
# from backend.app.src.schemas.groups.group import GroupSimpleSchema (для group)
# from backend.app.src.schemas.notifications.delivery import NotificationDeliverySchema

UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema')
NotificationDeliverySchema = ForwardRef('backend.app.src.schemas.notifications.delivery.NotificationDeliverySchema')

# --- Схема для відображення інформації про сповіщення (для читання) ---
class NotificationSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення сповіщення.
    """
    recipient_user_id: uuid.UUID = Field(..., description="ID користувача-отримувача сповіщення")
    group_id: Optional[uuid.UUID] = Field(None, description="ID групи, в контексті якої створено сповіщення")

    title: Optional[str] = Field(None, max_length=255, description="Заголовок сповіщення")
    body: str = Field(..., description="Основний текст (вміст) сповіщення")
    notification_type_code: str = Field(..., max_length=100, description="Код типу сповіщення")

    source_entity_type: Optional[str] = Field(None, max_length=100, description="Тип сутності, що спричинила сповіщення")
    source_entity_id: Optional[uuid.UUID] = Field(None, description="ID сутності-джерела")

    is_read: bool = Field(..., description="Чи прочитане сповіщення користувачем")
    read_at: Optional[datetime] = Field(None, description="Час, коли сповіщення було прочитане")

    metadata: Optional[Dict[str, Any]] = Field(None, description="Додаткові дані для сповіщення (JSON)")

    # --- Розгорнуті зв'язки (приклад) ---
    recipient: Optional[UserPublicSchema] = Field(None, description="Отримувач сповіщення")
    group: Optional[GroupSimpleSchema] = Field(None, description="Група, пов'язана зі сповіщенням")

    # Список спроб доставки
    deliveries: List[NotificationDeliverySchema] = Field(default_factory=list, description="Статуси доставки цього сповіщення")


# --- Схема для створення нового сповіщення (зазвичай використовується внутрішньо системою) ---
class NotificationCreateSchema(BaseSchema):
    """
    Схема для створення нового сповіщення.
    Зазвичай використовується сервісною логікою, а не напряму через API користувачем.
    """
    recipient_user_id: uuid.UUID = Field(..., description="ID користувача-отримувача")
    group_id: Optional[uuid.UUID] = Field(None, description="ID групи (якщо є контекст групи)")

    title: Optional[str] = Field(None, max_length=255, description="Заголовок сповіщення")
    body: str = Field(..., description="Текст сповіщення")
    notification_type_code: str = Field(..., max_length=100, description="Код типу сповіщення")

    source_entity_type: Optional[str] = Field(None, max_length=100, description="Тип сутності-джерела")
    source_entity_id: Optional[uuid.UUID] = Field(None, description="ID сутності-джерела")

    # is_read за замовчуванням False.
    # read_at встановлюється при прочитанні.
    metadata: Optional[Dict[str, Any]] = Field(None, description="Додаткові дані (JSON)")

    # `id`, `created_at`, `updated_at` встановлюються автоматично.

# --- Схема для оновлення сповіщення (наприклад, позначка про прочитання) ---
class NotificationUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючого сповіщення.
    Зазвичай використовується для позначки про прочитання.
    """
    is_read: Optional[bool] = Field(None, description="Новий статус прочитання")
    # read_at: Optional[datetime] # Встановлюється сервісом, якщо is_read стає True.

    # Інші поля (title, body, type тощо) зазвичай не змінюються для існуючого сповіщення.
    # Якщо потрібно "змінити" сповіщення, то це, скоріше, видалення старого і створення нового.

# --- Схема для масового оновлення статусу прочитання ---
class NotificationBulkReadSchema(BaseSchema):
    notification_ids: List[uuid.UUID] = Field(..., min_length=1, description="Список ID сповіщень для позначки як прочитані")
    is_read: bool = Field(default=True, description="Встановити статус прочитання (зазвичай True)")


# NotificationSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `NotificationModel`.
# `NotificationModel` успадковує від `BaseModel`.
# `NotificationSchema` успадковує від `AuditDatesSchema` і відображає поля сповіщення.
#
# Поля: `recipient_user_id`, `group_id`, `title`, `body`, `notification_type_code`,
# `source_entity_type`, `source_entity_id`, `is_read`, `read_at`, `metadata`.
#
# `NotificationCreateSchema` для створення.
# `NotificationUpdateSchema` для оновлення статусу `is_read`.
# `NotificationBulkReadSchema` для масової позначки про прочитання.
#
# Розгорнуті зв'язки в `NotificationSchema` (recipient, group, deliveries) додані з `ForwardRef`
# або закоментовані (deliveries зазвичай не потрібні при читанні самого сповіщення).
#
# Все виглядає узгоджено.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` - час створення сповіщення.
# `updated_at` - час останнього оновлення (наприклад, при зміні `is_read`).
#
# `metadata` (JSONB/Dict) для гнучкості зберігання додаткових даних,
# наприклад, URL для переходу, параметри для відображення тощо.
#
# Важливо, щоб `notification_type_code` був стандартизованим (Enum або довідник)
# для коректної обробки та відображення сповіщень на клієнті.
#
# Все виглядає добре.

NotificationSchema.model_rebuild()
NotificationCreateSchema.model_rebuild()
NotificationUpdateSchema.model_rebuild()
NotificationBulkReadSchema.model_rebuild()
