# backend/app/src/models/mixins.py
# -*- coding: utf-8 -*-
"""
Модуль міксинів (домішок) для моделей SQLAlchemy.

Цей модуль визначає класи-міксини, які надають спільні поля та функціональність
для різних моделей SQLAlchemy. Використання міксинів допомагає уникнути
дублювання коду та стандартизувати структуру моделей.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, declared_attr

class TimestampedMixin:
    """
    Міксин для додавання полів `created_at` та `updated_at` до моделей.

    `created_at`: Дата та час створення запису (встановлюється сервером бази даних).
    `updated_at`: Дата та час останнього оновлення запису (оновлюється сервером бази даних
                  при кожному оновленні запису).
    """
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        """Дата та час створення запису."""
        return mapped_column(server_default=func.now(), nullable=False, comment="Час створення запису")

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        """Дата та час останнього оновлення запису."""
        return mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False, comment="Час останнього оновлення запису")

    # Допоміжні поля для __repr__
    _repr_fields: List[str] = ['created_at', 'updated_at']


class SoftDeleteMixin:
    """
    Міксин для реалізації "м'якого видалення" записів.
    Додає поле `deleted_at`, яке позначає час видалення запису.
    Якщо `deleted_at` встановлено, запис вважається видаленим, але залишається в базі даних.
    """
    @declared_attr
    def deleted_at(cls) -> Mapped[Optional[datetime]]:
        """Дата та час "м'якого" видалення запису. NULL, якщо запис не видалено."""
        return mapped_column(nullable=True, index=True, comment="Час м'якого видалення запису (якщо видалено)")

    # Допоміжні поля для __repr__
    _repr_fields: List[str] = ['deleted_at']


class NameDescriptionMixin:
    """
    Міксин для додавання полів `name` та `description` до моделей.

    `name`: Обов'язкове поле для назви сутності, індексоване для швидкого пошуку.
    `description`: Необов'язкове текстове поле для детального опису сутності.
    """
    @declared_attr
    def name(cls) -> Mapped[str]:
        """Назва сутності (наприклад, ім'я користувача, назва групи, назва завдання)."""
        return mapped_column(index=True, nullable=False, comment="Назва сутності")

    @declared_attr
    def description(cls) -> Mapped[Optional[str]]:
        """Детальний опис сутності (необов'язково)."""
        return mapped_column(Text, nullable=True, comment="Опис сутності")

    # Допоміжні поля для __repr__
    _repr_fields: List[str] = ['name']


class StateMixin:
    """
    Міксин для додавання поля `state` до моделей.
    Поле `state` може використовуватися для зберігання поточного стану сутності
    (наприклад, статус завдання, стан користувача).

    Значення для стану можуть бути визначені в Enum у `core.dicts`.
    Поле індексується для ефективної фільтрації за станом.
    """
    # TODO: Розглянути можливість використання ForeignKey до таблиці-довідника станів,
    #       якщо стани є складними або потребують додаткових атрибутів.
    #       Або ж валідувати значення стану на основі Enum з `core.dicts` на рівні Pydantic схем.
    @declared_attr
    def state(cls) -> Mapped[Optional[str]]:
        """Поточний стан сутності (наприклад, 'active', 'pending_review')."""
        return mapped_column(nullable=True, index=True, comment="Стан сутності")

    # Допоміжні поля для __repr__
    _repr_fields: List[str] = ['state']


class GroupAffiliationMixin:
    """
    Міксин для додавання поля `group_id`, що пов'язує сутність з групою.

    `group_id`: Зовнішній ключ до таблиці `groups` (поле `id`).
                Позначає групу, до якої належить сутність.
                `ondelete='SET NULL'` означає, що якщо пов'язана група видаляється,
                це поле буде встановлено в NULL (сутність більше не належатиме цій групі).
                Це може бути змінено на `CASCADE` або іншу стратегію залежно від вимог.
    """
    # Важливо: Назва таблиці 'groups' та поле 'id' мають відповідати реальній таблиці груп.
    # Назва зовнішнього ключа 'fk_group_affiliation_group_id' є рекомендованою конвенцією.
    @declared_attr
    def group_id(cls) -> Mapped[Optional[int]]:
        """ID групи, до якої належить ця сутність (необов'язково)."""
        # Використовуємо f-string для формування унікального імені зовнішнього ключа для кожної таблиці,
        # яка використовує цей міксин, щоб уникнути конфліктів імен.
        return mapped_column(
            ForeignKey('groups.id', name=f'fk_{cls.__tablename__}_group_id', ondelete='SET NULL'),
            nullable=True,
            index=True,
            comment="ID групи, до якої належить сутність"
        )

    # Допоміжні поля для __repr__
    _repr_fields: List[str] = ['group_id']


class NotesMixin:
    """
    Міксин для додавання поля `notes` до моделей.
    Це поле призначене для зберігання довільних текстових нотаток або коментарів,
    пов'язаних із сутністю.
    """
    @declared_attr
    def notes(cls) -> Mapped[Optional[str]]:
        """Додаткові нотатки або коментарі щодо сутності (необов'язково)."""
        return mapped_column(Text, nullable=True, comment="Додаткові нотатки")

    # Допоміжні поля для __repr__
    # 'notes' може бути занадто довгим для repr, тому не додаємо його за замовчуванням.
    _repr_fields: List[str] = []
