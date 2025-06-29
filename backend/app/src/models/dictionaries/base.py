# backend/app/src/models/dictionaries/base.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає базовий клас `BaseDictModel` для всіх моделей-довідників.
Моделі-довідники представляють собою таблиці з наперед визначеними або конфігурованими значеннями,
які використовуються для класифікації або типізації інших сутностей в системі (наприклад, статуси, ролі, типи).

`BaseDictModel` успадковує `BaseMainModel` і додає специфічне для довідників поле `code`.
"""

from sqlalchemy import Column, String # type: ignore
from sqlalchemy.orm import Mapped, mapped_column # Додано для SQLAlchemy 2.0

from backend.app.src.models.base import BaseMainModel # Імпорт базової моделі

class BaseDictModel(BaseMainModel):
    """
    Базовий клас для моделей-довідників.
    Успадковує всі поля від `BaseMainModel` (id, name, description, state_id, group_id,
    created_at, updated_at, deleted_at, is_deleted, notes) та додає поле `code`.

    Поле `code` призначене для зберігання унікального рядкового ідентифікатора запису довідника,
    який може використовуватися в коді системи для посилання на конкретні значення довідника
    без прив'язки до `id`. Наприклад, `code='active'` для статусу "Активний".
    """
    __abstract__ = True  # Вказує, що SQLAlchemy не повинна створювати таблицю для цього класу

    # Унікальний символьний код для запису довідника.
    # Наприклад, 'admin_role', 'task_type_bug', 'status_completed'.
    # Це поле повинно бути унікальним в межах одного довідника.
    # index=True: Створює індекс для цього поля для пришвидшення пошуку.
    # nullable=False: Поле не може бути порожнім.
    # Примітка: Обмеження унікальності (UniqueConstraint) для поля `code`
    # слід додавати в конкретних моделях-наслідниках через атрибут `__table_args__`.
    # Наприклад:
    # class MySpecificDictModel(BaseDictModel):
    #     __tablename__ = "my_specific_dicts"
    #     __table_args__ = (UniqueConstraint('code', name='uq_my_specific_dict_code'),)
    #
    # Це забезпечить унікальність коду в межах конкретної таблиці довідника.
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # TODO: Подумати над тим, чи потрібне поле `group_id` для всіх довідників.
    # Деякі довідники можуть бути глобальними (наприклад, системні статуси, ролі),
    # а деякі - специфічними для груп (наприклад, типи бонусів, налаштовані адміном групи).
    # Якщо довідник глобальний, `group_id` буде `None`.
    # Можливо, варто зробити `group_id` `nullable=True` в `BaseMainModel` (що вже зроблено)
    # і просто не заповнювати його для глобальних довідників.

    # TODO: Визначити, чи потрібне поле `state_id` для довідників.
    # Зазвичай записи в довідниках або існують (активні), або ні.
    # Можливо, замість `state_id` для довідників достатньо `is_deleted` або окремого `is_active` поля.
    # Поки що залишаємо `state_id` успадкованим, але його використання для довідників під питанням.
    # Якщо `state_id` не потрібен, можна його "приховати" або перевизначити в `BaseDictModel`.

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі довідника.
        Наприклад: <MyDictModel(id='...', code='...')>
        """
        return f"<{self.__class__.__name__}(id='{self.id}', code='{self.code}')>"

# TODO: Додати документацію щодо того, як створювати нові моделі-довідники на основі `BaseDictModel`.
# Приклад:
# class StatusModel(BaseDictModel):
#     __tablename__ = "statuses"  # Явне визначення імені таблиці
#     # Тут можна додати унікальність для поля code, якщо потрібно
#     # __table_args__ = (UniqueConstraint('code', name='uq_status_code'),)
#
#     # ... будь-які специфічні поля для цього довідника, якщо є
#
#     # Поля id, name, description, state_id, group_id, created_at, updated_at,
#     # deleted_at, is_deleted, notes, code успадковуються.
#
#     # Наприклад, якщо статуси можуть мати колір:
#     # color: Column[str] = Column(String(7), nullable=True) # #RRGGBB
