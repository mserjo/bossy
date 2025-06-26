# backend/app/src/models/base.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає базові класи моделей SQLAlchemy, які слугуватимуть основою для всіх інших моделей даних у проекті.
Він включає `BaseModel` з основними полями аудиту (id, created_at, updated_at, created_by_user_id, updated_by_user_id)
та `BaseMainModel`, який розширює `BaseModel` полями, загальними для більшості основних сутностей проекту
(name, description, state_id, group_id, deleted_at, is_deleted, notes) та відповідними зв'язками.
"""

import uuid  # Для генерації унікальних ідентифікаторів
from datetime import datetime  # Для роботи з датами та часом
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func, Boolean, Integer # Додано Integer для version
from sqlalchemy.dialects.postgresql import UUID  # Специфічний для PostgreSQL тип UUID
from sqlalchemy.orm import declarative_base, declared_attr, relationship, Mapped, mapped_column # type: ignore # Додано Mapped, mapped_column для SQLAlchemy 2.0 стилю

# Створення базового класу для декларативного визначення моделей
# Усі моделі SQLAlchemy успадковуватимуться від цього класу.
Base = declarative_base()


class BaseModel(Base): # type: ignore
    """
    Базовий клас моделі, що надає спільні поля та функціональність для всіх моделей.
    Включає унікальний ідентифікатор (UUID), позначки часу створення та оновлення,
    а також інформацію про користувачів, що створили/оновили запис.
    """
    __abstract__ = True  # Вказує, що SQLAlchemy не повинна створювати таблицю для цього класу

    # Унікальний ідентифікатор запису, використовується UUID v4.
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Дата та час створення запису.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Дата та час останнього оновлення запису.
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Користувач, який створив запис.
    # ForeignKey посилається на таблицю 'users', поле 'id'.
    # `name` для ForeignKey важливий для Alembic автогенерації.
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_created_by_user_id"), nullable=True, index=True)

    # Користувач, який востаннє оновив запис.
    updated_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_updated_by_user_id"), nullable=True, index=True)

    # Зв'язки з UserModel (використовуємо foreign_keys для уникнення неоднозначності)
    # TODO: Перевірити back_populates, коли UserModel буде оновлено.
    # Поки що без back_populates, оскільки UserModel може мати багато таких зв'язків.
    # Або використовувати різні назви для back_populates в UserModel.
    # Наприклад, created_by_user = relationship("UserModel", foreign_keys=[created_by_user_id], back_populates="created_records_by_user")
    # Але це ускладнить UserModel. Поки що залишаю без back_populates тут.
    # Сервіси будуть відповідати за заповнення created_by_user_id/updated_by_user_id.
    # Зв'язки тут можуть бути для зручності отримання об'єкта користувача.

    # created_by: Mapped[Optional["UserModel"]] = relationship(foreign_keys=[created_by_user_id])
    # updated_by: Mapped[Optional["UserModel"]] = relationship(foreign_keys=[updated_by_user_id])
    # TODO: Додати type hints для UserModel, коли він буде імпортований або через ForwardRef,
    #       але це може створити циклічні залежності на рівні імпорту файлів.
    #       Краще залишити ці зв'язки для визначення в конкретних моделях, якщо вони там потрібні,
    #       або використовувати їх без back_populates, якщо вони лише для читання звідси.
    #       Або ж, якщо UserModel матиме загальний `audited_records` зв'язок.
    #       Поки що закоментовано, щоб уникнути проблем з імпортами.

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
    __abstract__ = True

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    state_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("statuses.id", name="fk_state_id"), nullable=True, index=True)
    group_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id", name="fk_group_id"), nullable=True, index=True)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Версія для оптимістичного блокування (якщо буде потрібно)
    # version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    # --- Зв'язки (Relationships) ---
    # Зв'язок зі статусом
    # `lazy="joined"` може бути корисним, якщо статус часто потрібен разом з основною сутністю.
    # Або `lazy="selectin"` для SQLAlchemy 2.0 стилю.
    # Потрібно імпортувати StatusModel та GroupModel або використовувати ForwardRef.
    # from backend.app.src.models.dictionaries.status import StatusModel (Приклад)
    # from backend.app.src.models.groups.group import GroupModel (Приклад)

    # Використовуємо рядкові посилання на моделі для уникнення циклічних імпортів на рівні файлів.
    # SQLAlchemy зможе їх розпізнати, якщо всі моделі успадковують від одного Base.
    state: Mapped[Optional["StatusModel"]] = relationship("StatusModel", foreign_keys=[state_id], lazy="selectin")

    # Зв'язок з групою
    # `back_populates` має відповідати назві зв'язку в GroupModel, якщо там є зворотний зв'язок
    # до сутностей, що їй належать (наприклад, `group.tasks`, `group.rewards`).
    # Якщо це загальний `group_id` для багатьох типів сутностей, то універсальний `back_populates`
    # в `GroupModel` може бути складним.
    # Поки що без `back_populates` або з загальною назвою, яку треба буде узгодити.
    # `foreign_keys` вказується явно, щоб SQLAlchemy точно знав, яке поле використовувати.
    group: Mapped[Optional["GroupModel"]] = relationship("GroupModel", foreign_keys=[group_id], lazy="selectin")
    # TODO: Узгодити `back_populates` для `group` з `GroupModel`, коли там будуть визначені
    #       зворотні зв'язки до різних типів сутностей, що належать групі.
    #       Наприклад, `GroupModel` може мати `tasks = relationship("TaskModel", back_populates="group")`.
    #       Тоді тут `back_populates` не потрібен, якщо зв'язок однонаправлений звідси,
    #       або якщо `GroupModel` не має універсального поля для всіх "дочірніх" об'єктів.
    #       Поки що залишаю `lazy="selectin"` для ефективного завантаження, якщо потрібно.

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Автоматично генерує ім'я таблиці в нижньому регістрі на основі імені класу моделі,
        додаючи 's' для утворення множини.
        Наприклад, для класу `MyAwesomeModel` ім'я таблиці буде `myawesomemodels`.

        УВАГА: Ця логіка може бути неідеальною для всіх назв моделей (наприклад, Status -> statuss).
        Для таких випадків краще явно визначати `__tablename__` в самій моделі.
        Або використовувати більш складний алгоритм плюралізації (наприклад, бібліотеку `inflect`).
        Поки що залишаємо цю просту реалізацію як базову.
        """
        # Проста плюралізація додаванням 's'.
        # Можна додати винятки або більш складну логіку.
        # if cls.__name__.endswith('s'): # Простий виняток
        #     return cls.__name__.lower() + 'es' # Hoặc просто cls.__name__.lower()
        # elif cls.__name__.endswith('y') and not cls.__name__.endswith('ey'):
        #     return cls.__name__[:-1].lower() + 'ies'
        # else:
        #     return cls.__name__.lower() + 's'
        #
        # Поки що залишаю найпростіший варіант:
        table_name = cls.__name__.lower()
        if table_name.endswith("model"): # Відрізаємо "model" з кінця, якщо є
            table_name = table_name[:-5]

        # Проста плюралізація (може потребувати покращення)
        if table_name.endswith('y') and table_name[-2] not in 'aeiou':
            return table_name[:-1] + 'ies'
        elif table_name.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return table_name + 'es'
        else:
            return table_name + 's'

# TODO: Додати документацію щодо використання `declared_attr` для __tablename__.
# `declared_attr` використовується для атрибутів класу, які обчислюються під час створення класу,
# а не під час створення екземпляра. Це дозволяє мати динамічні імена таблиць.

# TODO: Описати, як міграції Alembic будуть працювати з цими базовими моделями.
# Alembic автоматично виявлятиме зміни в моделях, що успадковують ці базові класи,
# та генеруватиме відповідні скрипти міграцій.
# Важливо, щоб `Base` був імпортований у `env.py` Alembic:
# from backend.app.src.models.base import Base
# target_metadata = Base.metadata

# TODO: Переглянути використання `Optional` для `Mapped`.
# `Mapped[Optional[str]]` або `Mapped[str | None]` є коректним для SQLAlchemy 2.0.
# `nullable=True` в `mapped_column` також вказує на опціональність.
# Використовую `Mapped[Optional[...]]` для консистентності з Python типами.
# `DateTime(timezone=True)` важливо для коректної роботи з часовими зонами (зберігати все в UTC).
# `func.now()` для PostgreSQL повертає час з часовою зоною (timestamptz).
#
# Перехід на SQLAlchemy 2.0 стиль з `Mapped` та `mapped_column` зроблено.
# Це покращує типізацію та інтеграцію з Mypy.
#
# Зв'язки `created_by` та `updated_by` в `BaseModel` закоментовані,
# оскільки їх реалізація з `back_populates` може бути складною для базового класу,
# який не знає про всі моделі, що його успадковують.
# Поля `created_by_user_id` та `updated_by_user_id` залишені як `ForeignKey`.
# Отримання об'єктів користувачів за цими ID може бути реалізовано на сервісному рівні
# або в конкретних моделях, якщо це часто потрібно.
#
# Логіка генерації `__tablename__` трохи покращена, але все ще може потребувати
# ручного перевизначення для деяких моделей.
#
# Зв'язки `state` та `group` в `BaseMainModel` реалізовані з `lazy="selectin"`,
# що є хорошою стратегією завантаження для SQLAlchemy 2.0, якщо ці об'єкти
# часто потрібні разом з основною сутністю.
# Використання рядкових посилань на моделі ("StatusModel", "GroupModel")
# допомагає уникнути проблем з циклічними імпортами.
#
# Все готово для цього файлу.
