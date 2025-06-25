# backend/app/src/schemas/gamification/rating.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `RatingModel`.
Схеми використовуються для відображення інформації про рейтинги користувачів
в групах. Записи `RatingModel` зазвичай створюються (або оновлюються)
періодично системою на основі активності користувачів.
"""

from pydantic import Field
from typing import Optional, List, ForwardRef
import uuid
from datetime import datetime
from decimal import Decimal # Використовуємо Decimal

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.groups.group import GroupSimpleSchema

UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema')

# --- Схема для відображення інформації про запис рейтингу (для читання) ---
class RatingSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення запису про рейтинг користувача в групі.
    `snapshot_date` (або `created_at`) вказує на час, коли рейтинг був актуальним.
    """
    user_id: uuid.UUID = Field(..., description="ID користувача")
    group_id: uuid.UUID = Field(..., description="ID групи, в якій розрахований рейтинг")
    rating_type_code: str = Field(..., max_length=100, description="Код типу рейтингу (наприклад, 'by_completed_tasks', 'by_earned_bonuses')")
    rating_value: Decimal = Field(..., description="Значення рейтингу (наприклад, кількість балів, позиція)")
    rank_position: Optional[int] = Field(None, ge=1, description="Позиція користувача в рейтингу (якщо застосовно)")

    period_start_date: Optional[datetime] = Field(None, description="Початок періоду, за який розрахований рейтинг")
    # `snapshot_date` з моделі - це дата, на яку актуальний зріз рейтингу.
    # В `AuditDatesSchema` є `created_at`, яке може використовуватися як `snapshot_date`.
    # Якщо в моделі є окреме поле `snapshot_date`, його треба додати сюди.
    # Поточна модель `RatingModel` має `snapshot_date`.
    snapshot_date: datetime = Field(..., description="Дата зрізу або кінця періоду, на яку актуальний рейтинг")


    # --- Розгорнуті зв'язки (приклад) ---
    user: Optional[UserPublicSchema] = Field(None, description="Користувач, до якого відноситься рейтинг")
    group: Optional[GroupSimpleSchema] = Field(None, description="Група, в якій розраховано рейтинг")


# --- Схема для створення запису рейтингу (зазвичай внутрішнє використання системою) ---
class RatingCreateSchema(BaseSchema):
    """
    Схема для створення нового запису рейтингу.
    Зазвичай використовується внутрішньою логікою системи (наприклад, періодичною задачею).
    """
    user_id: uuid.UUID = Field(..., description="ID користувача")
    group_id: uuid.UUID = Field(..., description="ID групи")
    rating_type_code: str = Field(..., max_length=100, description="Код типу рейтингу")
    rating_value: Decimal = Field(..., description="Значення рейтингу")
    rank_position: Optional[int] = Field(None, ge=1, description="Позиція в рейтингу")

    period_start_date: Optional[datetime] = Field(None, description="Початок періоду рейтингу")
    snapshot_date: datetime = Field(default_factory=datetime.utcnow, description="Дата зрізу рейтингу (за замовчуванням - поточна)")


# --- Схема для оновлення запису рейтингу (зазвичай не використовується, створюються нові зрізи) ---
# Рейтинги зазвичай є знімками стану на певний момент часу.
# Якщо потрібно оновити, то це, скоріше, перерахунок і створення нового запису
# з новою `snapshot_date` (або оновлення запису, якщо `snapshot_date` та інші ключі збігаються,
# що залежить від логіки зберігання - чи це історія, чи поточний стан).
# Модель `RatingModel` призначена для зберігання історії, тому оновлення існуючих записів
# малоймовірне, крім випадків виправлення помилок.
#
# class RatingUpdateSchema(BaseSchema):
#     """
#     Схема для оновлення існуючого запису рейтингу (використовується рідко).
#     """
#     rating_value: Optional[Decimal] = Field(None)
#     rank_position: Optional[int] = Field(None, ge=1)
#     # Інші поля (user_id, group_id, type, dates) зазвичай не змінюються для історичного запису.


# RatingSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `RatingModel`.
# `RatingModel` успадковує від `BaseModel`.
# `RatingSchema` успадковує від `AuditDatesSchema` і відображає поля рейтингу.
# Використання `Decimal` для `rating_value`.
#
# Поля: `user_id`, `group_id`, `rating_type_code`, `rating_value`, `rank_position`,
# `period_start_date`, `snapshot_date`.
#
# `RatingCreateSchema` містить поля для створення запису.
# `snapshot_date` за замовчуванням - поточний час.
#
# `RatingUpdateSchema` закоментована, оскільки рейтинги зазвичай є незмінними зрізами.
#
# Розгорнуті зв'язки в `RatingSchema` (user, group) додані з `ForwardRef`.
#
# Все виглядає узгоджено.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` може використовуватися як час запису рейтингу, якщо `snapshot_date`
# не використовується або дублює його. Поточна модель `RatingModel` має окреме поле `snapshot_date`.
# `updated_at` - якщо запис рейтингу колись оновлюється (малоймовірно для історичних даних).
#
# `rating_type_code` дозволяє розрізняти різні типи рейтингів (за завданнями, за бонусами, за період тощо).
# `rank_position` - для турнірних таблиць.
# `period_start_date` та `snapshot_date` (як кінець періоду) важливі для контексту рейтингу.
#
# Все виглядає добре.
