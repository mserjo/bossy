# backend/app/src/models/mixins.py
# -*- coding: utf-8 -*-
"""Модуль домішок (mixins) для моделей SQLAlchemy.

Цей модуль визначає класи-домішки, які надають спільні набори полів
та пов'язану з ними функціональність для різних моделей SQLAlchemy.
Використання домішок допомагає уникнути дублювання коду, стандартизувати
структуру моделей даних та спростити їх підтримку.

Кожен міксин може визначати один або декілька стовпців (`mapped_column`)
за допомогою декоратора `@declared_attr`, що дозволяє SQLAlchemy коректно
інтегрувати ці стовпці в таблиці моделей, які успадковують ці домішки.

Також міксини можуть визначати список `_repr_fields`, який використовується
кастомним методом `__repr__` у базовому класі моделі (`models.base.Base`)
для автоматичної генерації інформативного рядкового представлення об'єктів.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class TimestampedMixin:
    """Додає поля часових міток `created_at` та `updated_at` до моделей.

    Атрибути:
        created_at (Mapped[datetime]): Дата та час створення запису.
            Автоматично встановлюється сервером бази даних при створенні.
        updated_at (Mapped[datetime]): Дата та час останнього оновлення запису.
            Автоматично встановлюється та оновлюється сервером бази даних
            при кожному оновленні запису.
    """
    __abstract__ = True # Вказує, що це абстрактний міксин, не для створення таблиці

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        """Дата та час створення запису (UTC)."""
        return mapped_column(
            DateTime(timezone=True), # Зберігання часу з інформацією про часову зону (рекомендовано UTC)
            server_default=func.now(), # Значення за замовчуванням на рівні БД
            nullable=False,
            comment="Час створення запису (UTC)"
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        """Дата та час останнього оновлення запису (UTC)."""
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(), # Оновлення значення на рівні БД при кожному UPDATE
            nullable=False,
            comment="Час останнього оновлення запису (UTC)"
        )

    _repr_fields: tuple[str, ...] = ("created_at", "updated_at")


class SoftDeleteMixin:
    """Додає функціональність "м'якого видалення" до моделей.

    Замість фізичного видалення записів з бази даних, встановлюється
    мітка часу видалення та прапорець `is_deleted`.

    Атрибути:
        deleted_at (Mapped[Optional[datetime]]): Дата та час "м'якого" видалення запису (UTC).
            Значення `None` означає, що запис не видалено. Індексується для оптимізації запитів.
        is_deleted (Mapped[bool]): Прапорець, що вказує на стан м'якого видалення.
            `True` – запис видалено, `False` – запис активний. Індексується.
            Має значення за замовчуванням `False`.
    """
    __abstract__ = True

    @declared_attr
    def deleted_at(cls) -> Mapped[Optional[datetime]]:
        """Дата та час "м'якого" видалення запису (UTC). `None`, якщо запис не видалено."""
        return mapped_column(
            DateTime(timezone=True),
            nullable=True,
            index=True,
            comment="Час м'якого видалення запису (UTC), якщо видалено"
        )

    @declared_attr
    def is_deleted(cls) -> Mapped[bool]:
        """Прапорець, що вказує, чи запис "м'яко" видалено."""
        return mapped_column(
            Boolean,
            default=False,
            server_default='false', # Значення за замовчуванням на рівні БД
            nullable=False,
            index=True,
            comment="Прапорець м'якого видалення (true, якщо видалено)"
        )

    _repr_fields: tuple[str, ...] = ("deleted_at", "is_deleted")


class NameDescriptionMixin:
    """Додає поля `name` (назва) та `description` (опис) до моделей.

    Атрибути:
        name (Mapped[str]): Обов'язкове поле для назви сутності.
            Індексується для швидкого пошуку. Максимальна довжина 255 символів.
        description (Mapped[Optional[str]]): Необов'язкове текстове поле
            для детального опису сутності.
    """
    __abstract__ = True

    @declared_attr
    def name(cls) -> Mapped[str]:
        """Назва сутності (наприклад, ім'я користувача, назва групи)."""
        return mapped_column(
            String(255), # Обмеження довжини для індексації та сумісності
            index=True,
            nullable=False,
            comment="Назва сутності"
        )

    @declared_attr
    def description(cls) -> Mapped[Optional[str]]:
        """Детальний опис сутності (необов'язково)."""
        return mapped_column(
            Text,
            nullable=True,
            comment="Опис сутності"
        )

    _repr_fields: tuple[str, ...] = ("name",) # description може бути довгим, тому не в repr за замовчуванням


class StateMixin:
    """Додає поле `state_id` до моделей для зв'язку зі станами/статусами.

    Атрибути:
        state_id (Mapped[Optional[int]]): Зовнішній ключ до таблиці `statuses` (поле `id`),
            що представляє поточний стан або статус сутності. Індексується.
            `use_alter=True` та явне іменування ForeignKey (`fk_%(table_name)s_state_id`)
            використовуються для кращої підтримки міграцій Alembic.
    """
    __abstract__ = True

    # Назва таблиці "statuses" та колонки "id" є припущенням.
    # Це має відповідати реальній таблиці-довіднику статусів у вашій БД.
    @declared_attr
    def state_id(cls) -> Mapped[Optional[int]]:
        """ID стану/статусу сутності (зовнішній ключ до таблиці dict_statuses)."""
        # Використання %(table_name)s дозволяє Alembic автоматично підставляти
        # ім'я таблиці при генерації міграцій для ForeignKey.
        fk_name = f"fk_{cls.__tablename__}_state_id" # Використовуємо f-string, оскільки %(table_name)s тут не працює напряму
                                                  # В Alembic env.py можна налаштувати convention для імен FK.
                                                  # Для простоти тут можна використовувати f-string,
                                                  # але стандартна конвенція Alembic з %(table_name)s краща,
                                                  # якщо налаштована в env.py -> context.configure(naming_convention=...)
        return mapped_column(
            ForeignKey("dict_statuses.id", name=fk_name, use_alter=True), # Явне ім'я FK та use_alter, змінено на dict_statuses
            nullable=True, # Залежить від бізнес-логіки, чи може стан бути відсутнім
            index=True,
            comment="ID стану/статусу сутності (FK до таблиці dict_statuses)"
        )

    # Примітка: Відповідний `relationship` до моделі статусів (наприклад, `StatusModel`)
    # зазвичай визначається в самій моделі, що використовує цей міксин,
    # а не в міксині, щоб уникнути проблем з циклічними імпортами та для кращої кастомізації.
    # Приклад:
    # from .dictionaries.status_model import StatusModel # Приклад шляху
    # state: Mapped[Optional["StatusModel"]] = relationship(foreign_keys=[state_id], lazy="selectin")

    _repr_fields: tuple[str, ...] = ("state_id",)


class GroupAffiliationMixin:
    """Додає поле `group_id` до моделей для зв'язку сутності з групою.

    Атрибути:
        group_id (Mapped[Optional[int]]): Зовнішній ключ до таблиці `groups` (поле `id`),
            що позначає групу, до якої належить сутність. Індексується.
            `ondelete='SET NULL'` означає, що якщо пов'язана група видаляється,
            це поле буде встановлено в `NULL`.
            `use_alter=True` та явне іменування ForeignKey використовуються для Alembic.
    """
    __abstract__ = True

    # Назва таблиці "groups" та колонки "id" є припущенням.
    @declared_attr
    def group_id(cls) -> Mapped[Optional[int]]:
        """ID групи, до якої належить ця сутність (необов'язково, FK до таблиці груп)."""
        fk_name = f"fk_{cls.__tablename__}_group_id" # Див. коментар у StateMixin щодо іменування FK
        return mapped_column(
            ForeignKey("groups.id", name=fk_name, ondelete="SET NULL", use_alter=True), # Явне ім'я FK та use_alter
            nullable=True,
            index=True,
            comment="ID групи, до якої належить сутність (FK до таблиці груп)"
        )

    # Примітка: Відповідний `relationship` до моделі групи (наприклад, `GroupModel`)
    # зазвичай визначається в моделі, що використовує цей міксин.

    _repr_fields: tuple[str, ...] = ("group_id",)


class NotesMixin:
    """Додає текстове поле `notes` до моделей.

    Це поле призначене для зберігання довільних текстових нотаток, коментарів
    або іншої додаткової інформації, пов'язаної із сутністю.

    Атрибути:
        notes (Mapped[Optional[str]]): Додаткові нотатки або коментарі.
    """
    __abstract__ = True

    @declared_attr
    def notes(cls) -> Mapped[Optional[str]]:
        """Додаткові текстові нотатки або коментарі щодо сутності (необов'язково)."""
        return mapped_column(
            Text,
            nullable=True,
            comment="Додаткові нотатки або коментарі"
        )

    # 'notes' може містити довгий текст. Включення його до __repr__
    # може зробити вивід занадто громіздким для деяких випадків,
    # але це відповідає вимозі завдання.
    _repr_fields: tuple[str, ...] = ("notes",)

# Приклад використання міксинів у демонстраційній моделі:
# (Цей блок не є частиною модуля, а лише для ілюстрації і може бути видалений
# або залишений для тестування при прямому запуску файлу)
#
# if __name__ == "__main__":
#     from backend.app.src.models.base import Base # Потрібно імпортувати Base
#
#     class SampleModelWithMixins(
#         Base, # Важливо успадковувати Base
#         TimestampedMixin,
#         SoftDeleteMixin,
#         NameDescriptionMixin,
#         # StateMixin, # Потребує таблиці "statuses"
#         # GroupAffiliationMixin, # Потребує таблиці "groups"
#         NotesMixin
#     ):
#         __tablename__ = "sample_mixins_table"
#         # id визначається в Base або BaseMainModel, тому тут не потрібен, якщо успадковуємо їх
#         # Якщо SampleModelWithMixins успадковує напряму Base, то id потрібно визначити:
#         id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
#         _repr_fields = ("id",) # Додаємо id до repr
#
#     # Створення екземпляра (поза контекстом БД, лише для демонстрації атрибутів)
#     sample = SampleModelWithMixins(
#         id=1,
#         name="Зразок з міксинами",
#         description="Це демонстрація використання міксинів.",
#         notes="Деякі нотатки тут."
#         # state_id та group_id можуть бути None або мати значення
#     )
#     # __repr__ з Base збере поля з усіх _repr_fields
#     logger.info("Демонстраційний екземпляр моделі з міксинами: %s", sample)
#
#     # Перевірка, чи міксини не створюють власних таблиць
#     logger.info("TimestampedMixin є абстрактним: %s", getattr(TimestampedMixin, '__abstract__', False))
#     logger.info("SoftDeleteMixin є абстрактним: %s", getattr(SoftDeleteMixin, '__abstract__', False))
#     # і т.д. для інших міксинів
