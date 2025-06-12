# backend/app/src/models/base.py
# -*- coding: utf-8 -*-
# # Модуль базових класів для моделей SQLAlchemy програми Kudos (Virtus).
# #
# # Цей файл визначає:
# # - `Base`: Декларативний базовий клас SQLAlchemy (`DeclarativeBase`), від якого
# #   мають успадковуватися всі моделі даних програми. Метадані цього класу
# #   використовуються Alembic для генерації міграцій.
# # - `BaseModel`: Базовий клас для всіх моделей, що містить спільні поля,
# #   такі як `id` (первинний ключ) та автоматично оновлювані часові мітки
# #   `created_at` та `updated_at`.
# # - `BaseMainModel`: Розширює `BaseModel`, додаючи типові поля для основних
# #   сутностей, такі як `name`, `description`, `state`, `group_id` (опціонально),
# #   `deleted_at` (для м'якого видалення) та `notes`.
# #
# # Використання цих базових класів забезпечує узгодженість структури моделей
# # та зменшує дублювання коду.

from datetime import datetime, timezone
from typing import Optional, Any # Any для типізації в __repr__, якщо буде додано

from sqlalchemy import func, ForeignKey # ForeignKey потрібен для BaseMainModel.group_id
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr, relationship # relationship для прикладу в BaseMainModel

# Імпорт логера (хоча в цьому файлі він використовується лише в __main__)
from backend.app.src.config.logging import get_logger

# TODO: Розглянути імпорт Enum типів з `core.dicts`, коли вони будуть використовуватися
#       як типи для полів, наприклад, для `state` в `BaseMainModel`.
# from backend.app.src.core.dicts import UserState, TaskStatus # Приклади Enum для поля 'state'

logger = get_logger(__name__)

# --- Декларативний базовий клас SQLAlchemy ---
class Base(DeclarativeBase):
    """
    Декларативний базовий клас для всіх моделей SQLAlchemy в програмі.
    Метадані (`metadata`) цього класу використовуються Alembic для автоматичної
    генерації та управління міграціями схеми бази даних.

    Можна також налаштувати `type_annotation_map` для кастомних типів даних,
    якщо це потрібно для всього проекту. Наприклад:
    ```python
    # from sqlalchemy.dialects.postgresql import JSONB
    # type_annotation_map = {
    #     Dict[str, Any]: JSONB, # Усі поля типу Dict[str, Any] будуть мапитися на JSONB в PostgreSQL
    # }
    ```
    """
    pass


# --- Базовий клас для моделей з ID та часовими мітками ---
class BaseModel(Base):
    """
    Абстрактний базовий клас для моделей даних, що містить спільні поля:
    `id` (первинний ключ), `created_at` (час створення) та `updated_at` (час останнього оновлення).

    Атрибут `__abstract__ = True` вказує SQLAlchemy, що цей клас
    не повинен створювати власну таблицю в базі даних, а слугує лише
    шаблоном (міксином) для успадкування іншими моделями.
    """
    __abstract__ = True # Означає, що для цього класу не буде створено окрему таблицю в БД.

    id: Mapped[int] = mapped_column(
        primary_key=True,      # Первинний ключ таблиці.
        index=True,            # Створює індекс для цього поля для швидшого пошуку.
        autoincrement=True,    # Автоматично збільшує значення ID для нових записів (типово для PostgreSQL).
        comment="Унікальний ідентифікатор запису (первинний ключ)" # Коментар для схеми БД.
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), # Значення за замовчуванням на рівні Python (використовує lambda для динамічного значення).
        server_default=func.now(), # SQL функція (`NOW()` або аналог) для значення за замовчуванням на рівні БД.
                                   # Це гарантує, що час буде встановлено БД, навіть якщо Python не передасть значення.
        comment="Час створення запису (в UTC)"
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), # Початкове значення при створенні.
        onupdate=lambda: datetime.now(timezone.utc), # Оновлюється автоматично на рівні Python при зміні запису.
        server_default=func.now(), # Початкове значення на рівні БД.
        server_onupdate=func.now(), # Автоматичне оновлення на рівні БД при зміні запису (якщо підтримується СУБД, наприклад, через тригери).
        comment="Час останнього оновлення запису (в UTC)"
    )

    # Можна додати типовий __repr__ для зручності відладки, якщо потрібно.
    # def __repr__(self) -> str:
    #     """Повертає рядкове представлення об'єкта моделі."""
    #     return f"<{self.__class__.__name__}(id={self.id})>"


# --- Розширений базовий клас для основних сутностей ---
class BaseMainModel(BaseModel):
    """
    Розширений базовий клас для основних сутностей програми, що успадковує від `BaseModel`.
    Додає поля, які часто зустрічаються в основних моделях, такі як:
    `name` (назва), `description` (опис), `state` (стан/статус),
    `group_id` (опціональний зовнішній ключ до групи),
    `deleted_at` (для реалізації м'якого видалення) та `notes` (додаткові примітки).

    Як і `BaseModel`, цей клас є абстрактним (`__abstract__ = True`).
    """
    __abstract__ = True

    name: Mapped[str] = mapped_column(
        index=True, # Часто використовується для пошуку, тому індексуємо.
        comment="Назва сутності (наприклад, ім'я користувача, назва групи, завдання). Має бути унікальною в межах певного контексту."
    )
    description: Mapped[Optional[str]] = mapped_column(
        nullable=True, # Опис може бути відсутнім.
        comment="Детальний опис сутності, якщо потрібно."
    )

    # Поле 'state' може використовувати рядок або спеціальний тип Enum з `core.dicts`.
    # Наприклад, для завдань це може бути `TaskStatus`, для користувачів - `UserState`.
    # Поки що використовуємо рядок, з можливістю доопрацювання з конкретним Enum у похідних моделях.
    # Приклад з Enum:
    # state: Mapped[Optional[TaskStatus]] = mapped_column(default=TaskStatus.OPEN, index=True)
    state: Mapped[Optional[str]] = mapped_column(
        nullable=True,
        index=True,
        comment="Поточний стан або статус сутності (наприклад, 'active', 'pending', 'completed')."
    )

    # `group_id` - опціональний зовнішній ключ до таблиці груп (якщо сутність може належати до групи).
    # TODO: (ВАЖЛИВО) Розкоментувати та налаштувати ForeignKey, коли модель `Group` буде визначена
    #       в `backend.app.src.models.groups.group.py` (або аналогічному файлі).
    #       Переконайтеся, що назва таблиці ('groups.id') та схема (якщо є) є правильними.
    # group_id: Mapped[Optional[int]] = mapped_column(
    #     ForeignKey("groups.id", name="fk_base_main_model_group_id", ondelete="SET NULL"), # Приклад: SET NULL при видаленні групи
    #     nullable=True,
    #     index=True,
    #     comment="Ідентифікатор групи, до якої належить ця сутність (якщо застосовно)."
    # )

    # Поле для реалізації механізму "м'якого видалення" (soft delete).
    # Якщо `deleted_at` встановлено, запис вважається видаленим, але залишається в БД.
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, # NULL означає, що запис не видалено.
        index=True,    # Індексуємо для ефективного фільтрування активних записів.
        comment="Час м'якого видалення запису (в UTC). Якщо NULL, запис вважається активним."
    )

    notes: Mapped[Optional[str]] = mapped_column(
        nullable=True,
        comment="Додаткові службові примітки або коментарі щодо запису."
    )

    # Приклад визначення зв'язку (relationship) для group_id.
    # Це дозволить легко доступатися до об'єкта групи з екземпляра цієї моделі.
    # Потрібно буде імпортувати модель Group та налаштувати `back_populates` в моделі Group.
    # @declared_attr
    # def group(cls) -> Mapped[Optional["Group"]]: # Використовуємо рядок "Group" для уникнення циклічних імпортів
    #     # Перевіряємо, чи клас має атрибут group_id, перш ніж створювати зв'язок.
    #     # Це робить зв'язок умовним, що може бути корисним, якщо не всі нащадки BaseMainModel мають group_id.
    #     if hasattr(cls, "group_id"):
    #         # from backend.app.src.models.groups.group import Group # Імпорт тут, всередині методу
    #         return relationship("Group", foreign_keys=[cls.group_id]) # back_populates="items_or_similar_name_in_group_model"
    #     return None # Якщо group_id немає, то і зв'язку немає.


# Блок для демонстрації структури класів при прямому запуску файлу.
if __name__ == "__main__":
    logger.info("Модуль базових моделей SQLAlchemy (`models.base.py`).")
    logger.info(f"Декларативна база SQLAlchemy, що використовується Alembic та моделями: {Base}")
    logger.info(f"Базовий клас моделей (ID, часові мітки): {BaseModel}")
    logger.info(f"Розширений базовий клас моделей (назва, опис, стан тощо): {BaseMainModel}")

    # Демонстрація атрибутів (не екземплярів, а структури класу)
    # Більш надійний спосіб інтроспекції - через __mapper__ або inspect(), але це вимагає,
    # щоб моделі були повністю ініціалізовані SQLAlchemy, що може не бути так при простому імпорті.
    # Тому тут простий dir() для базової демонстрації.

    base_model_defined_attrs = {
        attr for attr in dir(BaseModel)
        if not attr.startswith('_') and attr not in dir(Base) # Атрибути BaseModel, не успадковані від Base
    }
    # Атрибути, які Base успадковує від object, але які не є "магічними" і можуть бути цікаві
    # base_attrs_from_object = {attr for attr in dir(Base) if not attr.startswith('_') and attr in dir(object)}

    base_main_model_defined_attrs = {
        attr for attr in dir(BaseMainModel)
        if not attr.startswith('_') and attr not in dir(BaseModel) # Атрибути BaseMainModel, не успадковані від BaseModel
    }

    logger.info(f"\nАтрибути, визначені в BaseModel (окрім успадкованих від Base): {sorted(list(base_model_defined_attrs))}")
    logger.info(f"Атрибути, додані в BaseMainModel (окрім успадкованих від BaseModel): {sorted(list(base_main_model_defined_attrs))}")

    logger.info("\nДля використання цих базових класів, конкретні моделі даних (наприклад, User, Task) "
                "повинні успадковувати їх.")
    logger.info("Важливо: `Base.metadata` буде використовуватися Alembic для генерації міграцій схеми бази даних.")
    logger.info("Переконайтеся, що всі моделі, які мають відображатися в БД, імпортовані до того, "
                "як Alembic використовує `Base.metadata` (зазвичай це обробляється в `models/__init__.py` та `alembic/env.py`).")
