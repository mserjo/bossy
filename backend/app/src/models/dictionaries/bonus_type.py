# backend/app/src/models/dictionaries/bonus_type.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `BonusTypeModel` для довідника "Типи бонусів".
Типи бонусів використовуються для визначення одиниць виміру винагород або балів у системі,
наприклад, "бонуси", "бали", "зірочки". Адміністратор групи може обирати та налаштовувати
тип бонусів для своєї групи.

Модель `BonusTypeModel` успадковує `BaseDictModel`, що надає їй стандартний набір полів
(id, name, description, code, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes)
та функціональність.
"""

from sqlalchemy import UniqueConstraint, Column, Boolean # type: ignore
# from sqlalchemy.orm import relationship # type: ignore # Для визначення зв'язків, наприклад, з GroupSettingsModel
from sqlalchemy.orm import Mapped, mapped_column, relationship  # Для SQLAlchemy 2.0 стилю

from backend.app.src.models.dictionaries.base import BaseDictModel # Імпорт базової моделі для довідників

class BonusTypeModel(BaseDictModel):
    """
    Модель для довідника "Типи бонусів".

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор типу бонусів (успадковано).
        name (str): Назва типу бонусів (наприклад, "Бонусні бали", "Зірочки") (успадковано).
        description (str | None): Детальний опис типу бонусів (успадковано).
        code (str): Унікальний символьний код типу бонусів (наприклад, "points", "stars") (успадковано).
        state_id (uuid.UUID | None): Ідентифікатор стану запису типу бонусів (успадковано, використання під питанням).
        group_id (uuid.UUID | None): Ідентифікатор групи. Це поле буде NULL для глобально визначених
                                     типів бонусів. (успадковано).
        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення запису (успадковано).
        is_deleted (bool): Прапорець, що вказує, чи запис "м'яко" видалено (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Додаткові поля:
        allow_decimal (bool): Прапорець, що вказує, чи дозволені дробові значення для цього типу бонусів.
    """
    __tablename__ = "bonus_types"

    # Обмеження унікальності для поля `code`.
    # Гарантує, що кожен символьний код типу бонусів є унікальним (глобально).
    __table_args__ = (
        UniqueConstraint('code', name='uq_bonus_types_code'),
        # Типи бонусів зазвичай глобальні.
    )

    allow_decimal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Зворотні зв'язки (Relationships) ---
    # Зв'язок з GroupSettingsModel (налаштування груп, що використовують цей тип бонусу)
    # TODO: Узгодити back_populates="selected_bonus_type" з GroupSettingsModel
    group_settings_using_this_type = relationship("GroupSettingsModel", back_populates="selected_bonus_type", foreign_keys="[GroupSettingsModel.bonus_type_id]")

    # Зв'язок з AccountModel (рахунки, що використовують цей тип бонусу)
    # Поточна AccountModel має bonus_type_code (str). Потрібен primaryjoin.
    # TODO: Узгодити, чи буде AccountModel.bonus_type_code чи bonus_type_id.
    # Якщо AccountModel.bonus_type_code посилається на BonusTypeModel.code:
    accounts_with_this_type = relationship(
        "AccountModel",
        primaryjoin="foreign(AccountModel.bonus_type_code) == BonusTypeModel.code",
        back_populates="bonus_type_details" # Назва зв'язку в AccountModel
    )

    # Зв'язок з RewardModel (нагороди, вартість яких вказана в цьому типі бонусів)
    # Поточна RewardModel має bonus_type_code (str).
    # TODO: Узгодити, чи буде RewardModel.bonus_type_code чи bonus_type_id.
    # Якщо RewardModel.bonus_type_code посилається на BonusTypeModel.code:
    rewards_costed_in_this_type = relationship(
        "RewardModel",
        primaryjoin="foreign(RewardModel.bonus_type_code) == BonusTypeModel.code",
        back_populates="bonus_type_details" # Назва зв'язку в RewardModel
    )


    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі BonusTypeModel.
        Наприклад: <BonusTypeModel(id='...', name='Бали', code='points')>
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', code='{self.code}')>"
