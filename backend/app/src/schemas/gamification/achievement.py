# backend/app/src/schemas/gamification/achievement.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `AchievementModel`.
Схеми використовуються для відображення інформації про досягнення (отримані бейджі)
користувачами. Записи `AchievementModel` зазвичай створюються автоматично системою
або вручну адміністратором, а не через прямі API запити на створення користувачем.
"""

from pydantic import Field
from typing import Optional, List, Any, ForwardRef, Dict # Додано Dict
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.gamification.badge import BadgeSchema # Або BadgeSimpleSchema

from typing import TYPE_CHECKING # Додано TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.src.schemas.auth.user import UserPublicSchema
    from backend.app.src.schemas.gamification.badge import BadgeSchema

# UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema') # Перенесено
# BadgeSchema = ForwardRef('backend.app.src.schemas.gamification.badge.BadgeSchema') # Перенесено

# --- Схема для відображення інформації про досягнення (отриманий бейдж) ---
class AchievementSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення запису про отримання бейджа користувачем.
    `created_at` використовується як `achieved_at`.
    """
    user_id: uuid.UUID = Field(..., description="ID користувача, який отримав бейдж")
    badge_id: uuid.UUID = Field(..., description="ID отриманого бейджа")

    context_details: Optional[Dict[str, Any]] = Field(None, description="Додатковий контекст для повторюваних бейджів (JSON)")

    awarded_by_user_id: Optional[uuid.UUID] = Field(None, description="ID адміністратора, який вручну присудив бейдж")
    award_reason: Optional[str] = Field(None, description="Причина ручного присудження")

    # --- Розгорнуті зв'язки (приклад) ---
    user: Optional['UserPublicSchema'] = Field(None, description="Користувач, який отримав досягнення") # Рядкове посилання
    badge: Optional['BadgeSchema'] = Field(None, description="Інформація про отриманий бейдж") # Рядкове посилання
    awarder: Optional['UserPublicSchema'] = Field(None, description="Адміністратор, який вручну присудив досягнення (якщо є)") # Рядкове посилання


# --- Схема для створення запису про досягнення (зазвичай внутрішнє використання або адміном) ---
class AchievementCreateSchema(BaseSchema):
    """
    Схема для створення запису про отримання бейджа.
    Використовується або системою автоматично, або адміністратором для ручного присудження.
    """
    user_id: uuid.UUID = Field(..., description="ID користувача")
    badge_id: uuid.UUID = Field(..., description="ID бейджа")
    # achieved_at: datetime # Встановлюється автоматично як created_at

    context_details: Optional[Dict[str, Any]] = Field(None, description="Контекст для повторюваного бейджа (JSON)")

    # Для ручного присудження
    awarded_by_user_id: Optional[uuid.UUID] = Field(None, description="ID адміністратора (якщо присуджено вручну, встановлюється сервісом)")
    award_reason: Optional[str] = Field(None, description="Причина ручного присудження (якщо є)")

    # Перевірка унікальності (user_id, badge_id) залежить від BadgeModel.is_repeatable
    # і виконується на сервісному рівні.


# --- Схема для оновлення запису про досягнення (дуже рідко використовується) ---
# Зазвичай досягнення не оновлюються. Якщо потрібно відкликати бейдж,
# це може бути видалення запису AchievementModel або зміна його статусу (якщо є поле статусу).
# class AchievementUpdateSchema(BaseSchema):
#     """
#     Схема для оновлення запису про досягнення (використовується рідко).
#     """
#     context_details: Optional[Dict[str, Any]] = Field(None)
#     # Можливо, зміна `award_reason`, якщо було ручне присудження.
#     award_reason: Optional[str] = Field(None)


# AchievementSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `AchievementModel`.
# `AchievementModel` успадковує від `BaseModel`.
# `AchievementSchema` успадковує від `AuditDatesSchema` і відображає поля досягнення.
# Розгорнуті зв'язки `user`, `badge`, `awarder` додані з `ForwardRef`.
#
# `AchievementCreateSchema` містить поля для створення запису.
# `awarded_by_user_id` встановлюється сервісом, якщо це ручне присудження.
#
# `AchievementUpdateSchema` закоментована, оскільки оновлення таких записів нетипове.
#
# Логіка перевірки, чи можна користувачеві присудити цей бейдж (умови, is_repeatable),
# виконується на сервісному рівні перед створенням запису `AchievementModel`.
#
# Все виглядає узгоджено.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` використовується як час отримання досягнення (`achieved_at`).
# `updated_at` - якщо, наприклад, оновлюється `context_details` або `award_reason`.
#
# `context_details` (JSONB в моделі, Dict в схемі) для гнучкості зберігання контексту.
# Поля для ручного нагородження (`awarded_by_user_id`, `award_reason`) передбачені.
#
# Все виглядає добре.

# AchievementSchema.model_rebuild() # Виклик перенесено до schemas/__init__.py
# AchievementCreateSchema.model_rebuild() # Зазвичай не потрібно для схем без ForwardRef
