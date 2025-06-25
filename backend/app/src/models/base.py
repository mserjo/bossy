# backend/app/src/models/base.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає базові класи моделей SQLAlchemy, які слугуватимуть основою для всіх інших моделей даних у проекті.
Він включає `BaseModel` з основними полями аудиту (id, created_at, updated_at) та `BaseMainModel`,
який розширює `BaseModel` полями, загальними для більшості основних сутностей проекту (name, description, state_id, group_id, deleted_at, notes).
"""

import uuid  # Для генерації унікальних ідентифікаторів
from datetime import datetime  # Для роботи з датами та часом

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func, Boolean
from sqlalchemy.dialects.postgresql import UUID  # Специфічний для PostgreSQL тип UUID
from sqlalchemy.orm import declarative_base, declared_attr, relationship # type: ignore

# Створення базового класу для декларативного визначення моделей
# Усі моделі SQLAlchemy успадковуватимуться від цього класу.
Base = declarative_base()


class BaseModel(Base): # type: ignore
    """
    Базовий клас моделі, що надає спільні поля та функціональність для всіх моделей.
    Включає унікальний ідентифікатор (UUID) та позначки часу створення та оновлення.
    """
    __abstract__ = True  # Вказує, що SQLAlchemy не повинна створювати таблицю для цього класу

    # Унікальний ідентифікатор запису, використовується UUID v4.
    # primary_key=True: Вказує, що це поле є первинним ключем.
    # default=uuid.uuid4: Генерує новий UUID за замовчуванням при створенні запису.
    # index=True: Створює індекс для цього поля для пришвидшення пошуку.
    id: Column[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Дата та час створення запису.
    # default=func.now(): Встановлює поточний час бази даних за замовчуванням при створенні.
    # nullable=False: Поле не може бути порожнім.
    created_at: Column[datetime] = Column(DateTime, default=func.now(), nullable=False)

    # Дата та час останнього оновлення запису.
    # default=func.now(): Встановлює поточний час бази даних за замовчуванням при створенні.
    # onupdate=func.now(): Автоматично оновлює значення на поточний час бази даних при кожному оновленні запису.
    # nullable=False: Поле не може бути порожнім.
    updated_at: Column[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # TODO: Розглянути можливість додавання поля `created_by` та `updated_by` для відстеження користувача,
    # який створив або оновив запис, коли буде реалізована модель користувача.
    # created_by: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # updated_by: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі, корисне для відладки.
        Наприклад: <BaseModel(id='...')>
        """
        return f"<{self.__class__.__name__}(id='{self.id}')>"


class BaseMainModel(BaseModel):
    """
    Розширений базовий клас моделі, що успадковує `BaseModel` та додає поля,
    характерні для основних сутностей системи, такі як назва, опис, статус,
    приналежність до групи, позначка "м'якого" видалення та нотатки.
    """
    __abstract__ = True  # Вказує, що SQLAlchemy не повинна створювати таблицю для цього класу

    # Назва сутності (наприклад, назва групи, завдання, нагороди).
    # nullable=False: Поле не може бути порожнім.
    # index=True: Створює індекс для цього поля.
    name: Column[str] = Column(String(255), nullable=False, index=True)

    # Детальний опис сутності. Може бути довгим текстом.
    # nullable=True: Поле може бути порожнім.
    description: Column[str | None] = Column(Text, nullable=True)

    # Ідентифікатор статусу сутності. Посилається на довідник статусів.
    # ForeignKey("statuses.id"): Встановлює зовнішній ключ до таблиці `statuses` (модель `StatusModel`).
    # nullable=True: Дозволяє сутності не мати статусу, хоча зазвичай це поле буде заповнене.
    # index=True: Створює індекс для цього поля.
    # TODO: Замінити "statuses.id" на константу або імпорт моделі StatusModel після її створення.
    # TODO: Визначити, чи `nullable` має бути `False` для цього поля.
    state_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("statuses.id"), nullable=True, index=True)

    # Ідентифікатор групи, до якої належить сутність.
    # ForeignKey("groups.id"): Встановлює зовнішній ключ до таблиці `groups` (модель `GroupModel`).
    # nullable=True: Дозволяє сутності не належати до жодної групи (наприклад, системні налаштування).
    # index=True: Створює індекс для цього поля.
    # TODO: Замінити "groups.id" на константу або імпорт моделі GroupModel після її створення.
    # TODO: Визначити, чи `nullable` має бути `False` для деяких моделей, що успадковують цей клас.
    group_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=True, index=True)

    # Дата та час "м'якого" видалення запису.
    # Якщо значення встановлено, запис вважається видаленим, але фізично залишається в базі даних.
    # nullable=True: Поле може бути порожнім (запис не видалено).
    # index=True: Створює індекс для цього поля для ефективного відфільтровування "видалених" записів.
    deleted_at: Column[datetime | None] = Column(DateTime, nullable=True, index=True)

    # Позначка, чи запис видалено ("м'яке" видалення).
    # default=False: За замовчуванням запис не видалено.
    # nullable=False: Поле не може бути порожнім.
    is_deleted: Column[bool] = Column(Boolean, default=False, nullable=False)

    # Додаткові нотатки або коментарі до сутності.
    # nullable=True: Поле може бути порожнім.
    notes: Column[str | None] = Column(Text, nullable=True)

    # TODO: Додати зв'язки (relationships) до моделей StatusModel та GroupModel, коли вони будуть створені.
    # state = relationship("StatusModel", back_populates="...")
    # group = relationship("GroupModel", back_populates="...")

    # TODO: Розглянути можливість додавання поля `version` для оптимістичного блокування,
    # якщо це буде потрібно для запобігання конфліктам при одночасному оновленні.
    # version: Column[int] = Column(Integer, nullable=False, default=1)

    # TODO: Розглянути можливість додавання поля `is_active` або `is_enabled`,
    # якщо потрібен більш гранульований контроль над активністю сутності, окрім `state_id`.
    # is_active: Column[bool] = Column(Boolean, default=True, nullable=False)

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Автоматично генерує ім'я таблиці в нижньому регістрі на основі імені класу моделі.
        Наприклад, для класу `MyAwesomeModel` ім'я таблиці буде `myawesomemodel`.
        """
        return cls.__name__.lower() + "s" # Додаємо 's' для утворення множини, типово для назв таблиць
                                         # TODO: Переглянути цю логіку, можливо, для деяких моделей 's' буде зайвим або неправильним (наприклад, Status -> Statuss)
                                         # Можливо, краще використовувати явне визначення __tablename__ в кожній моделі або більш складну логіку перетворення.

# TODO: Додати глобальний Base для всіх моделей, можливо, перемістити `Base = declarative_base()` сюди,
# щоб усі моделі імпортували його з одного місця.
# from sqlalchemy.ext.declarative import declarative_base
# Base = declarative_base()
# Або вже використовується `Base` з цього файлу. Потрібно узгодити.

# TODO: Додати документацію щодо використання `declared_attr` для __tablename__.
# `declared_attr` використовується для атрибутів класу, які обчислюються під час створення класу,
# а не під час створення екземпляра. Це дозволяє мати динамічні імена таблиць.

# TODO: Описати, як міграції Alembic будуть працювати з цими базовими моделями.
# Alembic автоматично виявлятиме зміни в моделях, що успадковують ці базові класи,
# та генеруватиме відповідні скрипти міграцій.
# Важливо, щоб `Base` був імпортований у `env.py` Alembic.
# Файл alembic/env.py повинен містити:
# from backend.app.src.models.base import Base
# target_metadata = Base.metadata

# TODO: Розглянути необхідність створення `IdMixin`, `TimestampMixin` окремо,
# якщо деякі моделі не потребуватимуть всіх полів з `BaseModel`.
# Наприклад, таблиці зв'язків "багато-до-багатьох" можуть не потребувати `created_at`/`updated_at`.
# Хоча наявність цих полів може бути корисною для аудиту.
# Поки що `BaseModel` виглядає достатньо універсальним.

# TODO: Додати приклад використання цих базових моделей:
# class UserModel(BaseMainModel):
#     __tablename__ = "users"  # Явне визначення, якщо автоматична генерація не підходить
#
#     email: Column[str] = Column(String, unique=True, index=True, nullable=False)
#     # ... інші поля
#
#     # Приклад використання ForeignKey до іншої моделі
#     profile_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"))
#     profile = relationship("UserProfileModel", back_populates="user")
