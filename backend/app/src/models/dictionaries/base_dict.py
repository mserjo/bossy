# backend/app/src/models/dictionaries/base_dict.py
"""
Базовий клас для моделей-довідників SQLAlchemy.

Цей модуль визначає `BaseDictionaryModel`, який успадковує `BaseMainModel`
та додає спільне поле `code`, характерне для довідникових моделей.
Всі конкретні моделі-довідники (наприклад, Статуси, Типи користувачів)
повинні успадковувати цей клас.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

# Абсолютний імпорт базової моделі з основного модуля моделей
from backend.app.src.models.base import BaseMainModel


class BaseDictionaryModel(BaseMainModel):
    """
    Абстрактний базовий клас для всіх моделей-довідників.

    Успадковує всі поля від `BaseMainModel` (включаючи `id`, `name`, `description`,
    часові мітки, м'яке видалення, стан, нотатки та опціональний `group_id`)
    і додає обов'язкове, унікальне, індексоване поле `code`.

    Атрибути:
        code (Mapped[str]): Унікальний текстовий код для запису довідника (наприклад, "active", "admin_role").
                            Максимальна довжина 100 символів.
    """
    __abstract__ = True  # Вказує SQLAlchemy, що це не таблиця, а базовий клас для інших таблиць.

    code: Mapped[str] = mapped_column(
        String(100),  # Довжина 100 є прикладом, можна налаштувати.
        unique=True,
        index=True,
        nullable=False,
        comment="Унікальний текстовий код запису довідника"
    )

    # _repr_fields успадковуються з BaseMainModel та його міксинів.
    # Додаємо 'code' до списку полів для __repr__ цього конкретного класу.
    # Важливо, щоб це не був список, а кортеж або змінна класу, щоб уникнути проблем з mutable defaults.
    # Однак, оскільки __repr__ в Base збирає поля динамічно, ми можемо просто додати до списку.
    # Якщо _repr_fields ще не існує в батьківських класах (що малоймовірно з BaseMainModel),
    # його потрібно ініціалізувати як список.
    # Краще, щоб __repr__ метод динамічно збирав _repr_fields з усіх предків, що він і робить.
    # Тому тут ми визначаємо _repr_fields, специфічні для цього рівня ієрархії.
    _repr_fields = ["code"]


if __name__ == "__main__":
    # Цей блок для демонстрації та базового тестування при прямому запуску модуля.
    print("--- Базова модель для довідників (BaseDictionaryModel) ---")
    print(f"Клас BaseDictionaryModel: {BaseDictionaryModel}")
    print(f"Абстрактний: {getattr(BaseDictionaryModel, '__abstract__', False)}")

    # Демонстрація очікуваних атрибутів (для цього потрібне відображення SQLAlchemy)
    # У реальному сценарії це перевіряється через інстанціювання конкретної моделі-довідника.
    expected_attrs_from_basemainmodel = [
        'id', 'created_at', 'updated_at', 'deleted_at', 'name',
        'description', 'state', 'group_id', 'notes'
    ]
    expected_attrs_own = ['code']

    print("\nОчікувані атрибути, успадковані від BaseMainModel:")
    for attr in expected_attrs_from_basemainmodel:
        print(f"  - {attr}")
    print("\nВласні атрибути BaseDictionaryModel:")
    for attr in expected_attrs_own:
        print(f"  - {attr}")

    # Приклад того, як __repr__ може виглядати для моделі, що успадковує BaseDictionaryModel
    # (спрощена імітація без реальної інженерії SQLAlchemy)
    from backend.app.src.models.base import Base
    from datetime import datetime


    class DummyStatus(BaseDictionaryModel):
        __tablename__ = "dummy_statuses"  # Потрібно для @declared_attr в міксинах
        # Імітація __mapper__ для __repr__
        __mapper__ = type('Mapper', (), {'columns': {
            'id': None, 'name': None, 'code': None, 'created_at': None,
            'description': None, 'state': None,  # Додаємо state, оскільки він у BaseMainModel
        }})()
        # _repr_fields для DummyStatus, якщо він не додає нових полів до repr
        # _repr_fields = [] # Це б означало, що тільки поля з BaseDictionaryModel та його предків будуть в repr


    # Встановлюємо _repr_fields для міксинів, щоб __repr__ їх підхопив
    # (це потрібно лише для цього демонстраційного блоку __main__)
    from backend.app.src.models import mixins

    mixins.TimestampedMixin._repr_fields = ['created_at']
    mixins.NameDescriptionMixin._repr_fields = ['name']
    mixins.StateMixin._repr_fields = ['state']

    dummy_status_instance = DummyStatus()
    dummy_status_instance.id = 1
    dummy_status_instance.name = "Активний"
    dummy_status_instance.code = "ACTIVE"
    dummy_status_instance.created_at = datetime(2023, 1, 1, 12, 0, 0)
    dummy_status_instance.description = "Статус активного елемента"
    dummy_status_instance.state = "enabled"  # Приклад стану для самого довідника

    print(f"\nПриклад __repr__ для екземпляра DummyStatus:\n  {dummy_status_instance}")
    # Очікуваний вивід (порядок може відрізнятися):
    # <DummyStatus(id=1, name='Активний', code='ACTIVE', created_at=datetime.datetime(2023, 1, 1, 12, 0), state='enabled')>

    # Повертаємо _repr_fields до початкових значень, щоб не впливати на інші можливі тести/використання
    mixins.TimestampedMixin._repr_fields = ['created_at', 'updated_at']
    mixins.NameDescriptionMixin._repr_fields = ['name']
    mixins.StateMixin._repr_fields = ['state']

    print("\nПримітка: Поля `group_id` та `notes` також успадковуються, але не показані в цьому простому __repr__ прикладі.")
