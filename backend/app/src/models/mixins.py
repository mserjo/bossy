# backend/app/src/models/mixins.py

"""
Цей модуль визначає загальні класи-домішки (mixins) для SQLAlchemy.
Домішки надають спосіб композиції наборів полів моделі та функціональностей,
що можуть використовуватися повторно.
"""

import logging
from datetime import datetime, timezone
from typing import Optional # Додано для Mapped[Optional[datetime]]

from sqlalchemy import Column, DateTime, String, Text, Integer, ForeignKey, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

# Налаштувати логер для цього модуля
logger = logging.getLogger(__name__)

class TimestampedMixin:
    """
    Домішка для додавання полів часових міток `created_at` та `updated_at` до моделі.
    `created_at` встановлюється один раз при створенні запису.
    `updated_at` встановлюється при створенні та оновлюється кожного разу при зміні запису.
    """
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(), # Використовувати функцію now() бази даних за замовчуванням
            nullable=False,
            comment="Часова мітка створення запису (UTC)"
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(), # Використовувати функцію now() бази даних за замовчуванням
            onupdate=func.now(),       # Оновлювати функцією now() бази даних при зміні
            nullable=False,
            comment="Часова мітка останнього оновлення запису (UTC)"
        )

class SoftDeleteMixin:
    """
    Домішка для реалізації функціональності м'якого видалення.
    Додає часову мітку `deleted_at`. Якщо встановлено, запис вважається видаленим.
    """
    @declared_attr
    def deleted_at(cls) -> Mapped[Optional[datetime]]:
        return mapped_column(
            DateTime(timezone=True),
            nullable=True,
            comment="Часова мітка м'якого видалення запису (UTC). Null, якщо не видалено."
        )

    @hybrid_property
    def is_deleted(self) -> bool:
        """Повертає True, якщо запис м'яко видалено, інакше False."""
        return self.deleted_at is not None

    @is_deleted.setter # type: ignore[no-redef]
    def is_deleted(self, value: bool) -> None:
        """Сетер для is_deleted. Встановлює/очищає deleted_at."""
        self.deleted_at = datetime.now(timezone.utc) if value else None

    # Опціонально: метод для легкого запиту активних (не видалених) записів.
    # Це краще розмістити в базовому класі репозиторію або сервісу.
    # @classmethod
    # def query_active(cls, session):
    #     return session.query(cls).filter(cls.deleted_at.is_(None))

class NameDescriptionMixin:
    """
    Домішка для додавання загальних полів `name` та `description`.
    """
    @declared_attr
    def name(cls) -> Mapped[str]:
        return mapped_column(String(255), nullable=False, comment="Назва сутності (наприклад, назва групи, назва завдання)")

    @declared_attr
    def description(cls) -> Mapped[Optional[str]]:
        return mapped_column(Text, nullable=True, comment="Опціональний детальний опис сутності")

class StateMixin:
    """
    Домішка для додавання поля `state`, що зазвичай представляє статус або стан сутності.
    Фактичний тип стану (наприклад, рядок, enum) може відрізнятися, тому тут String використовується як загальне значення за замовчуванням.
    Розгляньте можливість використання типу Enum SQLAlchemy, якщо стани фіксовані та відомі.
    """
    @declared_attr
    def state(cls) -> Mapped[Optional[str]]: # Або специфічний Enum(YourStateType) для суворішої типізації
        return mapped_column(String(50), nullable=True, comment="Поточний стан або статус сутності")

class GroupAffiliationMixin:
    """
    Домішка для додавання зовнішнього ключа `group_id`, що пов'язує сутність з групою.
    Припускає наявність таблиці 'groups' з первинним ключем 'id'.
    """
    @declared_attr
    def group_id(cls) -> Mapped[Optional[int]]:
        # Ціль ForeignKey 'groups.id' є рядком. SQLAlchemy розпізнає це пізніше.
        # Переконайтеся, що у вас є модель Group з таблицею на ім'я 'groups'.
        return mapped_column(Integer, ForeignKey("groups.id"), nullable=True, index=True, comment="Ідентифікатор групи, до якої належить ця сутність, якщо застосовно")

    # Якщо ви також хочете встановити зв'язок з цієї домішки, ви можете додати:
    # from sqlalchemy.orm import relationship
    # @declared_attr
    # def group(cls) -> Mapped[Optional["Group"]]: # Пряме посилання на модель Group
    #     return relationship("Group", primaryjoin=lambda: cls.group_id == foreign(Group.id))
    # Однак, явне керування зв'язками в основних класах моделей часто є зрозумілішим.

class NotesMixin:
    """
    Домішка для додавання поля `notes` для загальних зауважень або внутрішніх коментарів.
    """
    @declared_attr
    def notes(cls) -> Mapped[Optional[str]]:
        return mapped_column(Text, nullable=True, comment="Внутрішні нотатки або загальні зауваження щодо сутності")

class UserAffiliationMixin:
    """
    Домішка для додавання зовнішнього ключа `user_id`, що пов'язує сутність з користувачем.
    Припускає наявність таблиці 'users' з первинним ключем 'id'.
    """
    @declared_attr
    def user_id(cls) -> Mapped[int]: # Припускаючи, що user_id зазвичай є обов'язковим, якщо використовується ця домішка
        return mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="Ідентифікатор користувача, пов'язаного з цією сутністю")

    # Подібно до GroupAffiliationMixin, зв'язки можна визначати тут або в основній моделі.
    # @declared_attr
    # def user(cls) -> Mapped["User"]:
    #     return relationship("User", primaryjoin=lambda: cls.user_id == foreign(User.id))

class CodeMixin:
    """
    Домішка для додавання поля `code`, яке часто використовується для унікальних, людиночитаних ідентифікаторів.
    """
    @declared_attr
    def code(cls) -> Mapped[str]:
        return mapped_column(String(100), nullable=False, unique=True, index=True, comment="Унікальний код або короткий ідентифікатор сутності")

if __name__ == "__main__":
    # Цей блок призначений для демонстрації та базового тестування визначень домішок.
    # Щоб запустити це, вам знадобиться SQLAlchemy Base та налаштування engine.
    # Наразі він просто логує інформацію про домішки.

    # Налаштувати базове логування для демонстрації, якщо обробники не налаштовані через setup_logging
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Домішки моделей SQLAlchemy --- демонстрація структури (без взаємодії з БД)")

    mixins_info = {
        "TimestampedMixin": [col for col in dir(TimestampedMixin) if not col.startswith('_') and col not in ['metadata']],
        "SoftDeleteMixin": [col for col in dir(SoftDeleteMixin) if not col.startswith('_') and col not in ['metadata', 'is_deleted']], # is_deleted - це hybrid_property, а не прямий стовпець
        "NameDescriptionMixin": [col for col in dir(NameDescriptionMixin) if not col.startswith('_') and col not in ['metadata']],
        "StateMixin": [col for col in dir(StateMixin) if not col.startswith('_') and col not in ['metadata']],
        "GroupAffiliationMixin": [col for col in dir(GroupAffiliationMixin) if not col.startswith('_') and col not in ['metadata']],
        "NotesMixin": [col for col in dir(NotesMixin) if not col.startswith('_') and col not in ['metadata']],
        "UserAffiliationMixin": [col for col in dir(UserAffiliationMixin) if not col.startswith('_') and col not in ['metadata']],
        "CodeMixin": [col for col in dir(CodeMixin) if not col.startswith('_') and col not in ['metadata']],
    }

    for mixin_name, attributes in mixins_info.items():
        # Для declared_attr це методи класу, а не атрибути екземпляра поки що
        actual_attrs = []
        mixin_class = globals()[mixin_name]
        for attr_name in attributes:
            attr = getattr(mixin_class, attr_name)
            if isinstance(attr, declared_attr) or isinstance(attr, hybrid_property):
                 actual_attrs.append(attr_name)
            elif callable(attr) and not attr_name.startswith('_'): # методи з declared_attr
                 actual_attrs.append(attr_name + "()")


        logger.debug(f"{mixin_name} надає атрибути/методи: {actual_attrs}")


    # Приклад використання домішки (концептуально, без повного налаштування SQLAlchemy тут)
    # Потрібен Base, щоб це було більш значущим
    # from sqlalchemy.orm import DeclarativeBase
    # class Base(DeclarativeBase): pass

    class ExampleModel(TimestampedMixin, NameDescriptionMixin, SoftDeleteMixin): # Додайте Base, якщо тестуєте з SQLAlchemy
        # __tablename__ = "examples" # Потрібно для реальної моделі SQLAlchemy
        id: Mapped[int] = mapped_column(primary_key=True) # Приклад первинного ключа
        # Щоб це можна було запустити для перевірки атрибутів, нам знадобився б Base
        # та визначення __table_args__ або подібного, якщо не використовується Base.
        # Наразі це концептуально.

    logger.info(f"Концептуальна ExampleModel успадковувала б поля від TimestampedMixin, NameDescriptionMixin, SoftDeleteMixin.")
    # Щоб фактично побачити стовпці, потрібно було б перевірити ExampleModel.__table__.columns
    # після Base.metadata.create_all(engine) або шляхом компіляції моделі.

    # Тестування гібридної властивості SoftDeleteMixin (концептуально)
    class DummyDeletable(SoftDeleteMixin): # Додайте Base, якщо тестуєте з SQLAlchemy
        pass # Немає первинного ключа, тому не може бути зіставлено безпосередньо

    dummy = DummyDeletable()
    logger.debug(f"Початкове dummy.is_deleted: {dummy.is_deleted}, dummy.deleted_at: {dummy.deleted_at}")
    dummy.is_deleted = True
    logger.debug(f"Після dummy.is_deleted = True: dummy.is_deleted: {dummy.is_deleted}, dummy.deleted_at: {str(dummy.deleted_at)[:19] if dummy.deleted_at else None}}") # Обрізати для чистішого логу
    dummy.is_deleted = False
    logger.debug(f"Після dummy.is_deleted = False: dummy.is_deleted: {dummy.is_deleted}, dummy.deleted_at: {dummy.deleted_at}")
