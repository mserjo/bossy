# backend/app/src/models/dictionaries/user_type.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `UserTypeModel` для довідника типів користувачів.
Типи користувачів (наприклад, "superadmin", "user", "bot") визначають загальну категорію користувача в системі.
"""

from sqlalchemy import UniqueConstraint # type: ignore
from sqlalchemy.orm import relationship, Mapped # type: ignore
from typing import List, TYPE_CHECKING

from backend.app.src.models.dictionaries.base import BaseDictModel # Базовий клас для довідників

if TYPE_CHECKING: # Блок для імпортів, що потрібні лише для перевірки типів
    from backend.app.src.models.auth.user import UserModel


class UserTypeModel(BaseDictModel):
    """
    Модель для довідника "Типи користувачів".

    Атрибути успадковані від `BaseDictModel`:
        id (uuid.UUID): Унікальний ідентифікатор.
        name (str): Назва типу користувача (наприклад, "Супер-Адміністратор", "Звичайний користувач").
        description (str | None): Детальний опис типу користувача.
        code (str): Унікальний символьний код типу (наприклад, "superadmin", "user", "bot").
        state_id (uuid.UUID | None): Статус запису довідника (якщо використовується).
        group_id (uuid.UUID | None): Для глобальних довідників, таких як типи користувачів, це поле буде NULL.
        created_at (datetime): Дата та час створення.
        updated_at (datetime): Дата та час останнього оновлення.
        deleted_at (datetime | None): Дата та час "м'якого" видалення.
        is_deleted (bool): Прапорець "м'якого" видалення.
        notes (str | None): Додаткові нотатки.

    Зв'язки:
        users (List["UserModel"]): Список користувачів, що належать до цього типу.
    """
    __tablename__ = "user_types"

    # Зв'язок з користувачами, що мають цей тип
    users: Mapped[List["UserModel"]] = relationship(
        "UserModel",
        back_populates="user_type",
        foreign_keys="[UserModel.user_type_id]" # Явно вказуємо foreign_keys для SQLAlchemy
    )

    # Обмеження унікальності для поля `code`, щоб коди типів користувачів були унікальними.
    __table_args__ = (
        UniqueConstraint('code', name='uq_user_type_code'),
    )

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі UserTypeModel.
        """
        return f"<UserTypeModel(id='{self.id}', name='{self.name}', code='{self.code}')>"
