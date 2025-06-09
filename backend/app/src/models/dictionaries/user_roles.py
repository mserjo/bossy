# backend/app/src/models/dictionaries/user_roles.py

"""
Модель SQLAlchemy для таблиці-довідника 'UserRole'.
Ця таблиця зберігає різні ролі, які можуть бути призначені користувачам у системі або в групах.
"""

import logging
from typing import Optional, List # Для Mapped[Optional[List[str]]], якщо використовуються JSON для дозволів
from datetime import datetime, timezone # Для прикладу в __main__

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON, Boolean # Якщо зберігати дозволи як JSON або додавати is_system_role

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Налаштувати логер для цього модуля
logger = logging.getLogger(__name__)

class UserRole(BaseDictionaryModel):
    """
    Представляє роль користувача в таблиці-довіднику (наприклад, Superuser, Admin, User, Guest, Bot).
    Успадковує загальні поля від BaseDictionaryModel.

    Поле 'state' з BaseDictionaryModel може використовуватися для позначення ролі як 'active' або 'deprecated'.
    Поле 'code' з BaseDictionaryModel буде ключовим (наприклад, 'SUPERUSER', 'GROUP_ADMIN', 'MEMBER').
    """
    __tablename__ = "dict_user_roles"

    # Додайте будь-які поля, специфічні для 'UserRole'.
    # Наприклад, список дозволів, пов'язаних з цією роллю.
    # Зберігання дозволів безпосередньо в таблиці ролей може бути простим для деяких випадків,
    # але складніша система RBAC може включати окремі таблиці дозволів та зв'язків роль-дозвіл.
    # permissions: Mapped[Optional[List[str]]] = mapped_column(
    #     JSON,
    #     nullable=True,
    #     comment="Список рядків дозволів або ключів, пов'язаних з цією роллю."
    # )

    # Інший приклад: is_system_role, якщо деякі ролі є фундаментальними і не можуть бути видалені користувачем.
    # is_system_role: Mapped[bool] = mapped_column(
    #     Boolean,
    #     default=False,
    #     nullable=False,
    #     comment="True, якщо це основна системна роль і не може бути видалена користувачами."
    # )

    def __repr__(self) -> str:
        return super().__repr__() # BaseDictionaryModel надає хороший стандартний __repr__

if __name__ == "__main__":
    # Цей блок призначений для демонстрації структури моделі UserRole.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Модель довідника UserRole --- Демонстрація")

    # Приклади екземплярів UserRole
    superuser_role = UserRole(
        code="SUPERUSER",
        name="Суперкористувач",
        description="Має всі дозволи в усій системі.",
        state="active",
        is_default=False, # Зазвичай не є роллю 'за замовчуванням' для нових користувачів
        display_order=1,
        # permissions=["system:admin", "user:manage", "group:manage_all"], # Якби поле permissions було додано
        # is_system_role=True # Якби поле було додано
    )
    superuser_role.id = 1 # Імітація ID, встановленого ORM
    superuser_role.created_at = datetime.now(timezone.utc) # Імітація часової мітки
    superuser_role.updated_at = datetime.now(timezone.utc) # Імітація часової мітки
    logger.info(f"Приклад UserRole: {superuser_role!r}, Опис: {superuser_role.description}")
    # if hasattr(superuser_role, 'permissions'):
    #     logger.info(f"  Дозволи: {superuser_role.permissions}")

    group_admin_role = UserRole(
        code="GROUP_ADMIN",
        name="Адміністратор групи",
        description="Керує конкретною групою, її учасниками та завданнями.",
        state="active",
        display_order=2
    )
    group_admin_role.id = 2
    group_admin_role.created_at = datetime.now(timezone.utc)
    group_admin_role.updated_at = datetime.now(timezone.utc)
    logger.info(f"Приклад UserRole: {group_admin_role!r}, Назва: {group_admin_role.name}")

    member_role = UserRole(
        code="MEMBER",
        name="Учасник",
        description="Звичайний користувач у групі, може виконувати завдання.",
        state="active",
        is_default=True, # Може бути роллю за замовчуванням для нових учасників групи
        display_order=3
    )
    member_role.id = 3
    member_role.created_at = datetime.now(timezone.utc)
    member_role.updated_at = datetime.now(timezone.utc)
    logger.info(f"Приклад UserRole: {member_role!r}, За замовчуванням: {member_role.is_default}")

    # Показати успадковані та специфічні атрибути (якщо такі були додані)
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Переконайтеся, що Base правильно імпортовано
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # Це створить усі таблиці, визначені за допомогою цього Base
    # logger.info(f"Стовпці в UserRole ({UserRole.__tablename__}): {[c.name for c in UserRole.__table__.columns]}")
    logger.info("Щоб побачити фактичні стовпці таблиці, метадані SQLAlchemy потрібно ініціалізувати за допомогою engine (наприклад, Base.metadata.create_all(engine)).")
