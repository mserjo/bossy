# backend/app/src/models/dictionaries/user_roles.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для довідника "Ролі користувачів".

Цей модуль визначає модель `UserRole`, яка представляє записи в довіднику
системних ролей користувачів (наприклад, "superuser", "user", "bot").
Ці ролі відрізняються від ролей всередині груп (`GroupRole` з `core.dicts`).
"""

# Абсолютний імпорт базової моделі для довідників
from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


# Можливо, знадобляться додаткові імпорти, якщо будуть специфічні поля.
# from sqlalchemy.orm import Mapped, mapped_column
# from sqlalchemy import String

class UserRole(BaseDictionaryModel):
    """
    Модель SQLAlchemy для довідника "Ролі користувачів".

    Успадковує всі поля від `BaseDictionaryModel` (включаючи `id`, `name`, `description`, `code`,
    часові мітки, м'яке видалення, стан, нотатки та опціональний `group_id`).
    `group_id` для системних ролей, ймовірно, буде NULL.

    Атрибути:
        __tablename__ (str): Назва таблиці в базі даних (`dict_user_roles`).
    """
    __tablename__ = "dict_user_roles"

    # Якщо для ролей користувачів потрібні специфічні додаткові поля,
    # наприклад, рівень доступу або набір дозволів за замовчуванням,
    # їх можна визначити тут.
    # Наприклад:
    # permission_level: Mapped[int] = mapped_column(nullable=True, comment="Числовий рівень доступу для ролі")

    # _repr_fields успадковуються та збираються автоматично з BaseDictionaryModel.
    # Немає додаткових специфічних полів для __repr__ на цьому рівні.
    _repr_fields: tuple[str, ...] = ()


if __name__ == "__main__":
    # Демонстраційний блок для моделі UserRole.
    logger.info("--- Модель Довідника: UserRole ---")
    logger.info(f"Назва таблиці: {UserRole.__tablename__}")

    logger.info("\nОчікувані поля (успадковані та власні):")
    expected_fields = ['id', 'name', 'description', 'code', 'created_at', 'updated_at', 'deleted_at', 'state',
                       'group_id', 'notes']
    # Якщо додано кастомні поля, їх теж сюди:
    # expected_fields.append('permission_level')
    for field in expected_fields:
        logger.info(f"  - {field}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_user_role = UserRole(
        id=1,
        name="Суперкористувач",
        description="Роль з повним доступом до всіх функцій системи.",
        code="SUPERUSER",
        state="active"
    )

    logger.info(f"\nПриклад екземпляра UserRole (без сесії):\n  {example_user_role}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <UserRole(id=1, name='Суперкористувач', code='SUPERUSER', state='active')>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
