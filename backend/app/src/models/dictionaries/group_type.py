# backend/app/src/models/dictionaries/group_type.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `GroupTypeModel` для довідника "Типи груп".
Типи груп використовуються для класифікації груп за їх призначенням або структурою,
наприклад, "сім'я", "відділ", "організація". Це може впливати на доступні налаштування
або функціонал для групи.

Модель `GroupTypeModel` успадковує `BaseDictModel`, що надає їй стандартний набір полів
(id, name, description, code, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes)
та функціональність.
"""

from sqlalchemy import UniqueConstraint, Boolean  # type: ignore # Для визначення обмежень унікальності
from sqlalchemy.orm import relationship, Mapped, mapped_column

# from sqlalchemy.orm import relationship # type: ignore # Для визначення зв'язків, наприклад, з GroupModel

from backend.app.src.models.dictionaries.base import BaseDictModel # Імпорт базової моделі для довідників

# TODO: Визначити, чи потрібні специфічні поля для моделі GroupTypeModel, окрім успадкованих.
# Наприклад, чи дозволена ієрархія для цього типу групи, чи доступні певні модулі.

class GroupTypeModel(BaseDictModel):
    """
    Модель для довідника "Типи груп".

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор типу групи (успадковано).
        name (str): Назва типу групи (наприклад, "Сім'я", "Робоча команда") (успадковано).
        description (str | None): Детальний опис типу групи (успадковано).
        code (str): Унікальний символьний код типу групи (наприклад, "family", "work_team") (успадковано).
        state_id (uuid.UUID | None): Ідентифікатор стану запису типу групи (успадковано, використання під питанням).
        group_id (uuid.UUID | None): Для довідника типів груп це поле, ймовірно, завжди буде NULL,
                                     оскільки типи груп є глобальними (успадковано).
        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення запису (успадковано).
        is_deleted (bool): Прапорець, що вказує, чи запис "м'яко" видалено (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Ім'я таблиці в базі даних: `group_types`.
    """
    __tablename__ = "group_types"

    # Обмеження унікальності для поля `code`.
    # Гарантує, що кожен символьний код типу групи є унікальним.
    __table_args__ = (
        UniqueConstraint('code', name='uq_group_types_code'),
        # Типи груп зазвичай глобальні, тому group_id тут не використовується для унікальності.
    )

    # --- Зворотні зв'язки (Relationships) ---
    # Зв'язок з GroupModel (групи, що мають цей тип)
    # TODO: Узгодити back_populates="group_type" з GroupModel
    groups_of_this_type = relationship("GroupModel", back_populates="group_type", foreign_keys="[GroupModel.group_type_id]")

    # Прапорець, що вказує, чи можуть групи цього типу мати ієрархічну структуру (підгрупи).
    can_have_hierarchy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")

    # TODO: Розглянути можливість додавання інших характеристик типу групи,
    # наприклад, max_members: Column[int] = Column(Integer, nullable=True) # Максимальна кількість учасників

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі GroupTypeModel.
        Наприклад: <GroupTypeModel(id='...', name='Сім'я', code='family')>
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', code='{self.code}')>"

# Приклади початкових даних для довідника типів груп (згідно technical-task.md):
# - сім'я (code: 'family', name: 'Сім\'я')
# - група (code: 'generic_group', name: 'Група') - можливо, більш загальний тип
# - відділ (code: 'department', name: 'Відділ')
# - організація (code: 'organization', name: 'Організація')

# TODO: Перевірити відповідність `technical-task.md` та `structure-claude-v3.md`.
# `BaseDictModel` надає необхідні поля. `group_id` для цієї моделі, скоріш за все, буде `None`.
# Назва таблиці `group_types` відповідає структурі.
# Унікальність `code` встановлена.
# Специфічні поля (наприклад, `can_have_hierarchy`) можуть бути додані для розширення функціоналу.
