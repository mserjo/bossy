# backend/app/src/models/dictionaries/base_dict.py

"""
Визначає базову модель для всіх таблиць-довідників (lookup tables).
"""

import logging
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from sqlalchemy import String, Boolean, Integer # Для is_active, display_order

from backend.app.src.models.base import BaseMainModel # Використання BaseMainModel для name, description, state, notes, soft_delete, timestamps
from backend.app.src.models.mixins import CodeMixin # Для унікального поля 'code'

# Налаштувати логер для цього модуля
logger = logging.getLogger(__name__)

class BaseDictionaryModel(BaseMainModel, CodeMixin):
    """
    Базовий клас для моделей-довідників.
    Успадковує від BaseMainModel для отримання загальних полів, таких як id, name, description,
    state, notes, created_at, updated_at, deleted_at.
    Додає поле `code` з CodeMixin для унікального, людиночитаного ідентифікатора.
    Також включає `is_default` та `display_order` для типової поведінки довідників.

    Загальні поля для моделей-довідників:
    - id: Первинний ключ (з BaseModel -> BaseMainModel).
    - code: Унікальний рядковий ідентифікатор (з CodeMixin).
    - name: Людиночитана назва (з NameDescriptionMixin -> BaseMainModel).
    - description: Опціональний детальний опис (з NameDescriptionMixin -> BaseMainModel).
    - state: Опціональний стан (наприклад, 'active', 'inactive') (зі StateMixin -> BaseMainModel).
    - is_default: Булеве значення, чи є це значенням за замовчуванням для типу довідника.
    - display_order: Ціле число для впорядкування елементів у списках UI.
    - created_at, updated_at: Часові мітки (з TimestampedMixin -> BaseModel -> BaseMainModel).
    - deleted_at: Для м'якого видалення (з SoftDeleteMixin -> BaseMainModel).
    - notes: Опціональні внутрішні нотатки (з NotesMixin -> BaseMainModel).
    """
    __abstract__ = True

    # `code` успадковується з CodeMixin (унікальний, індексований рядок)
    # `name`, `description` успадковуються з NameDescriptionMixin (через BaseMainModel)
    # `state` успадковується зі StateMixin (через BaseMainModel)
    # `notes` успадковується з NotesMixin (через BaseMainModel)
    # `created_at`, `updated_at`, `deleted_at`, `is_deleted` успадковуються через BaseMainModel

    is_default: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        default=False,
        nullable=True, # Може бути True, False або Null, якщо не застосовується/не встановлено
        comment="Вказує, чи є це значенням за замовчуванням для типу довідника."
    )

    display_order: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=0,
        nullable=True, # Може бути впорядковано або Null, якщо не застосовується/не встановлено
        comment="Порядок, у якому цей елемент повинен відображатися у списках/випадаючих списках."
    )

    # Перевизначити генерацію назви таблиці, якщо таблиці довідників повинні мати специфічний префікс або суфікс
    # Наприклад, якщо всі таблиці довідників повинні називатися 'dict_statuses', 'dict_user_roles'
    # @declared_attr
    # def __tablename__(cls) -> str:
    #     import re
    #     # Генерація назви таблиці за замовчуванням з BaseModel: ClassName -> class_names
    #     # Для довідників ми можемо віддати перевагу dict_class_names
    #     base_tablename = super().__tablename__
    #     return f"dict_{base_tablename}"
    # Наразі буде використовуватися значення за замовчуванням з BaseModel (наприклад, UserRole -> user_roles)
    # що часто є нормальним.

    def __repr__(self) -> str:
        # Перевірки hasattr для запобігання помилок, якщо підклас якимось чином не має цих полів (хоча повинен)
        _id = getattr(self, 'id', 'N/A')
        _code = getattr(self, 'code', 'N/A')
        _name = getattr(self, 'name', 'N/A')
        return f"<{self.__class__.__name__}(id={_id}, code='{_code}', name='{_name}')>"

if __name__ == "__main__":
    # Цей блок призначений для демонстрації структури BaseDictionaryModel.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- BaseDictionaryModel --- Демонстрація")

    # Показати, як конкретна модель довідника успадковуватиме поля
    class ExampleStatus(BaseDictionaryModel):
        # Якщо __tablename__ не встановлено, за замовчуванням це буде 'example_statuss' з логіки BaseModel
        # або 'dict_example_statuss', якби розкоментований __tablename__ у BaseDictionaryModel був активним.
        __tablename__ = "example_statuses" # Явна назва таблиці для наочності прикладу

        # Автоматично отримує id, code, name, description, state, is_default, display_order,
        # created_at, updated_at, deleted_at, notes.
        custom_field_for_status: Mapped[Optional[str]] = mapped_column(String(100))

    logger.info(f"BaseDictionaryModel успадковує від: {BaseDictionaryModel.__mro__}")
    logger.info(f"ExampleStatus успадковує від: {ExampleStatus.__mro__}")
    logger.info(f"Назва таблиці ExampleStatus за замовчуванням, якщо не перевизначено: {ExampleStatus.__tablename__}")


    # Щоб перевірити фактичні стовпці, вам потрібно було б ініціалізувати Base.metadata за допомогою engine
    # а потім отримати доступ до ExampleStatus.__table__.columns
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Переконайтеся, що Base - це той, що використовується моделями
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # Це створить усі таблиці, визначені за допомогою цього Base
    # logger.info(f"Стовпці в ExampleStatus: {[c.name for c in ExampleStatus.__table__.columns]}")
    # Цей список включав би: id, created_at, updated_at, name, description, state, deleted_at, notes,
    # code, is_default, display_order, custom_field_for_status
    logger.info("Щоб побачити фактичні стовпці таблиці, метадані SQLAlchemy потрібно ініціалізувати за допомогою engine (наприклад, Base.metadata.create_all(engine)).")


    status_instance = ExampleStatus(
        code="ACTIVE",
        name="Активний статус",
        description="Елемент активний і придатний до використання.",
        is_default=True,
        display_order=1,
        custom_field_for_status="Деякі власні дані"
    )
    # Імітація полів, встановлених ORM, для демонстрації
    status_instance.id = 1 # Зазвичай встановлюється БД
    # status_instance.created_at, .updated_at встановлювалися б БД/ORM або значеннями за замовчуванням TimestampedMixin

    logger.info(f"Приклад екземпляра: {status_instance!r}")
    logger.info(f"  Код: {status_instance.code}")
    logger.info(f"  Назва: {status_instance.name}")
    logger.info(f"  За замовчуванням: {status_instance.is_default}")
    logger.info(f"  Порядок відображення: {status_instance.display_order}")
    logger.info(f"  Власне поле: {status_instance.custom_field_for_status}")
    logger.info(f"  Стан (з BaseMainModel): {status_instance.state}") # Початковий стан буде None, якщо не встановлено
    status_instance.state = "ОПУБЛІКОВАНО"
    logger.info(f"  Оновлений стан: {status_instance.state}")
