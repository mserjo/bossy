# backend/app/src/models/mixins.py
# -*- coding: utf-8 -*-
"""
Цей модуль призначений для визначення SQLAlchemy міксинів.
Міксини (mixins) - це класи, які надають набір атрибутів (колонки, відносини, методи)
іншим класам моделей через множинне успадкування. Вони допомагають уникнути дублювання коду
та структурувати спільну функціональність між різними моделями.

Наприклад, тут можуть бути визначені міксини для:
- SoftDeleteMixin: реалізація "м'якого" видалення (позначка is_deleted та поле deleted_at).
- TimestampMixin: додавання полів created_at та updated_at (якщо не використовуються з BaseModel).
- CreatedUpdatedByMixin: додавання полів для відстеження, хто створив/оновив запис.
- ... та інші за потреби.

На даний момент більшість необхідної функціональності вже реалізована в `BaseModel` та `BaseMainModel`.
Цей файл залишено для можливого майбутнього розширення, якщо виникне потреба у більш гранулярних міксинах.
"""

from datetime import datetime # Для роботи з датами та часом
import uuid # Для генерації унікальних ідентифікаторів

from sqlalchemy import Column, DateTime, Boolean, func, ForeignKey # type: ignore
from sqlalchemy.dialects.postgresql import UUID # Специфічний для PostgreSQL тип UUID
from sqlalchemy.orm import declared_attr # type: ignore

# TODO: Розглянути необхідність винесення логіки "м'якого" видалення в окремий міксин,
# якщо не всі моделі, що успадковують BaseModel або BaseMainModel, потребуватимуть її.
# Наприклад:
# class SoftDeleteMixin:
#     """
#     Міксин для реалізації "м'якого" видалення записів.
#     Додає поле `deleted_at` та `is_deleted`.
#     """
#     deleted_at: Column[datetime | None] = Column(DateTime, nullable=True, index=True)
#     is_deleted: Column[bool] = Column(Boolean, default=False, nullable=False)

#     def soft_delete(self) -> None:
#         """Позначає запис як видалений."""
#         self.deleted_at = datetime.utcnow() # Або func.now() для часу БД
#         self.is_deleted = True

#     def restore(self) -> None:
#         """Відновлює "м'яко" видалений запис."""
#         self.deleted_at = None
#         self.is_deleted = False

# class TimestampMixin:
#     """
#     Міксин для додавання полів created_at та updated_at.
#     Корисно, якщо базова модель не має цих полів.
#     """
#     created_at: Column[datetime] = Column(DateTime, default=func.now(), nullable=False)
#     updated_at: Column[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


# class UserTrackingMixin:
#     """
#     Міксин для відстеження користувача, який створив або оновив запис.
#     Потребує наявності моделі користувача (зазвичай 'users').
#     """
#     @declared_attr
#     def created_by_id(cls) -> Column[uuid.UUID | None]:
#         # TODO: Замінити "users.id" на відповідний шлях до поля ID моделі користувача
#         return Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

#     @declared_attr
#     def updated_by_id(cls) -> Column[uuid.UUID | None]:
#         # TODO: Замінити "users.id" на відповідний шлях до поля ID моделі користувача
#         return Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # TODO: Додати relationships до моделі користувача, якщо це потрібно.
    # @declared_attr
    # def created_by(cls):
    #     return relationship("UserModel", foreign_keys=[cls.created_by_id])
    #
    # @declared_attr
    # def updated_by(cls):
    #     return relationship("UserModel", foreign_keys=[cls.updated_by_id])

# На даний момент цей файл порожній, оскільки основні потреби покриваються
# класами `BaseModel` та `BaseMainModel` з `backend.app.src.models.base`.
# Залишено для майбутніх розширень.
# Якщо в майбутньому виникне потреба у винесенні частини функціоналу з базових моделей
# в окремі міксини для більш гнучкого комбінування, їх слід розмістити тут.
# Наприклад, якщо якась модель не потребує полів `name` чи `description` з `BaseMainModel`,
# але потребує `deleted_at`, то можна буде успадкувати `BaseModel` та `SoftDeleteMixin`.

# Приклад використання міксину:
# from backend.app.src.models.base import BaseModel
#
# class SomeModel(BaseModel, SoftDeleteMixin): # type: ignore
#     __tablename__ = "some_entities"
#
#     # ... інші поля моделі
#
#     # Поля id, created_at, updated_at будуть успадковані з BaseModel
#     # Поля deleted_at, is_deleted та методи soft_delete/restore будуть з SoftDeleteMixin
#
# pass # Поки що файл порожній
