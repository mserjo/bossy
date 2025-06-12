# backend/app/src/models/base.py
# -*- coding: utf-8 -*-
"""
Базові класи для моделей SQLAlchemy програми Kudos.

Цей модуль визначає:
- `Base`: Декларативний базовий клас для всіх моделей SQLAlchemy, що дозволяє SQLAlchemy
           автоматично відображати класи Python на таблиці бази даних.
- `BaseMainModel`: Основний базовий клас для більшості моделей предметної області,
                   який успадковує `Base` та включає набір стандартних полів
                   через міксини (ID, часові мітки, м'яке видалення, назва, опис,
                   стан, приналежність до групи, нотатки).

Використання міксинів та спільного базового класу `BaseMainModel` сприяє
узгодженості між моделями та зменшує дублювання коду.
"""
from datetime import datetime
from typing import Optional, List, Any

from sqlalchemy import Text, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column  # removed declared_attr as it's used in mixins
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Імпорт міксинів з локального файлу mixins.py
# Використовуємо абсолютний шлях для надійності
from backend.app.src.models.mixins import (
    TimestampedMixin,
    SoftDeleteMixin,
    NameDescriptionMixin,
    StateMixin,
    GroupAffiliationMixin,
    NotesMixin
)


class Base(DeclarativeBase):
    """
    Декларативний базовий клас для всіх моделей SQLAlchemy.
    Надає функціональність для визначення метаданих таблиць.
    Також може містити спільну логіку для всіх моделей, наприклад, кастомний `__repr__`.
    """

    # Кастомний __repr__ для кращого налагодження
    def __repr__(self) -> str:
        """Генерує рядкове представлення екземпляра моделі для налагодження."""
        # Збираємо поля з поточного класу та всіх батьківських міксинів/класів
        repr_fields_collected = set()

        # Додамо 'id', якщо він є у __mapper__.columns (тобто це реальна колонка)
        # і не вказаний у _repr_fields (щоб уникнути дублювання, якщо міксин вже його додав)
        # або якщо _repr_fields взагалі не визначено на класі.
        # Це також гарантує, що 'id' буде першим, якщо він є.
        if hasattr(self, 'id') and 'id' in self.__mapper__.columns:
            is_id_in_custom_repr_fields = False
            for base_cls_for_check in self.__class__.__mro__:
                if 'id' in getattr(base_cls_for_check, '_repr_fields', []):
                    is_id_in_custom_repr_fields = True
                    break
            if not is_id_in_custom_repr_fields:
                repr_fields_collected.add('id')

        for base_cls in self.__class__.__mro__:
            # Шукаємо атрибут _repr_fields у класі та його предках
            # Це дозволяє міксинам визначати, які з їхніх полів включати в repr
            for field_name in getattr(base_cls, '_repr_fields', []):
                # Перевіряємо, чи це поле є реальною колонкою SQLAlchemy, а не, наприклад, relationship
                if field_name in self.__mapper__.columns:
                    repr_fields_collected.add(field_name)

        field_values_str = []
        # Сортуємо для узгодженого порядку, 'id' завжди перший, якщо він був зібраний
        sorted_fields = []
        if 'id' in repr_fields_collected:
            sorted_fields.append('id')
            repr_fields_collected.remove('id')  # Видаляємо, щоб не дублювати при сортуванні решти

        sorted_fields.extend(sorted(list(repr_fields_collected)))

        for field_name in sorted_fields:
            # hasattr перевіряє, чи існує атрибут на екземплярі (може бути ще не завантажений з БД)
            if hasattr(self, field_name):
                field_values_str.append(f"{field_name}={getattr(self, field_name)!r}")
            else:  # Якщо атрибута немає, але він є в repr_fields (наприклад, deferred)
                field_values_str.append(f"{field_name}=<не завантажено>")

        return f"<{self.__class__.__name__}({', '.join(field_values_str)})>"


class BaseMainModel(
    Base,
    TimestampedMixin,
    SoftDeleteMixin,
    NameDescriptionMixin,
    StateMixin,
    GroupAffiliationMixin,
    NotesMixin
):
    """
    Основний базовий клас для моделей предметної області.

    Успадковує від `Base` та включає набір стандартних полів і функціональностей
    через міксини:
    - `id`: Унікальний ідентифікатор (первинний ключ).
    - `TimestampedMixin`: Поля `created_at` та `updated_at`.
    - `SoftDeleteMixin`: Поле `deleted_at` для м'якого видалення.
    - `NameDescriptionMixin`: Поля `name` та `description`.
    - `StateMixin`: Поле `state` для відстеження стану сутності.
    - `GroupAffiliationMixin`: Поле `group_id` для зв'язку з групою.
    - `NotesMixin`: Поле `notes` для додаткових нотаток.

    Моделі, що представляють основні сутності програми (наприклад, Користувачі,
    Групи, Завдання), повинні успадковувати цей клас.
    """
    __abstract__ = True  # Вказує SQLAlchemy, що це не таблиця, а базовий клас для інших таблиць.

    # Первинний ключ, спільний для всіх основних моделей.
    # UUID може бути альтернативою, якщо потрібні глобально унікальні ID без залежності від БД.
    # Наразі використовується автоінкрементний Integer.
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Унікальний ідентифікатор запису"
    )
    # Поле 'id' автоматично додається до __repr__ через логіку в Base.__repr__


# Для демонстрації, якщо цей файл запускається окремо
if __name__ == "__main__":
    logger.info("--- Базові класи моделей SQLAlchemy ---")
    logger.info(f"Клас Base: {Base}")
    logger.info(f"Клас BaseMainModel: {BaseMainModel}")


    # Створення прикладу моделі, що успадковує BaseMainModel, для демонстрації
    # Це лише для тестування структури; реальні моделі будуть в інших файлах.
    # Для реального тестування потрібна engine та сесія.

    class ExampleEntity(BaseMainModel):
        __tablename__ = "example_entities"
        # Додаткові специфічні поля для ExampleEntity
        extra_data: Mapped[Optional[str]]

        # Додаємо 'extra_data' до списку полів для __repr__ цього конкретного класу
        _repr_fields = ["extra_data"]  # Це поле буде додано до тих, що збираються з міксинів


    logger.info(f"\nСтворено демонстраційну модель ExampleEntity, що успадковує BaseMainModel.")
    logger.info(f"Очікувані атрибути в ExampleEntity (включаючи успадковані):")
    # Приблизний список атрибутів, які мають бути в ExampleEntity
    # Реальний introspection краще робити через SQLAlchemy Inspector після створення таблиць.
    expected_attrs = ['id', 'created_at', 'updated_at', 'deleted_at', 'name',
                      'description', 'state', 'group_id', 'notes', 'extra_data']
    logger.info(f"  Очікувані атрибути: {', '.join(expected_attrs)}")

    logger.info("\nДемонстрація __repr__:")
    # Створюємо фіктивний екземпляр. Для реального __repr__ з усіма полями,
    # особливо тими, що з @declared_attr, потрібна ініціалізація через SQLAlchemy.
    # Ця демонстрація буде обмеженою без реальної сесії.

    # Імітуємо, як SQLAlchemy міг би створити екземпляр (дуже спрощено)
    # У реальному випадку __mapper__ та інші атрибути SQLAlchemy будуть заповнені.
    # Для цілей __repr__ тут, ми можемо створити простий об'єкт з потрібними полями.

    # Створимо фіктивний mapper для демонстрації __repr__
    mock_mapper_columns = {
        'id': None, 'created_at': None, 'updated_at': None, 'deleted_at': None,
        'name': None, 'description': None, 'state': None, 'group_id': None,
        'notes': None, 'extra_data': None
    }

    # Динамічно створюємо клас для тесту, щоб не конфліктувати з ExampleEntity вище,
    # якщо __name__ == "__main__" запускається кілька разів або в іншому контексті.
    TestReprEntity = type(
        "TestReprEntity",
        (BaseMainModel,),
        {
            "__tablename__": "test_repr_entities",  # Потрібно для @declared_attr в міксинах
            "extra_data": mapped_column(Text, nullable=True),  # Приклад поля
            "_repr_fields": ["extra_data"],  # Додаємо специфічне поле до repr
            # Імітація __mapper__ для __repr__
            "__mapper__": type('Mapper', (), {'columns': mock_mapper_columns})()
        }
    )

    # Важливо: _repr_fields з міксинів повинні бути доступні класу TestReprEntity.
    # Наша реалізація __repr__ в Base збирає їх через MRO.

    test_instance = TestReprEntity()
    test_instance.id = 1
    test_instance.name = "Тестовий Запис"
    test_instance.state = "активний"
    test_instance.created_at = datetime(2023, 1, 1, 10, 0, 0)
    test_instance.extra_data = "Це додаткові дані"
    # updated_at, deleted_at, description, group_id, notes - залишаться None або значеннями за замовчуванням

    logger.info(f"  Екземпляр TestReprEntity: {test_instance}")
    # Очікуваний вивід буде приблизно:
    # <TestReprEntity(id=1, name='Тестовий Запис', state='активний', created_at=datetime.datetime(2023, 1, 1, 10, 0), extra_data='Це додаткові дані')>
    # (порядок може трохи відрізнятися через сортування set, крім id)

    test_instance_minimal = TestReprEntity()
    test_instance_minimal.id = 2
    test_instance_minimal.name = "Мінімальний"
    logger.info(f"  Екземпляр TestReprEntity (мінімальний): {test_instance_minimal}")

    logger.info("\nПримітка: Повноцінне тестування SQLAlchemy моделей та їх __repr__")
    logger.info("зазвичай включає створення тестової бази даних та взаємодію з сесіями.")
